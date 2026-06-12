"""Public, unauthenticated lead-capture endpoints.

These routes are intentionally outside the tenant-header scheme: the form id
itself carries the workspace context. The server only ever trusts the
sub_account_id stored on the Form row — never anything in the client payload —
so a submission can only ever land in the workspace that owns the form.

Embedding: the /render response explicitly allows framing from any origin
(`Content-Security-Policy: frame-ancestors *`, no `X-Frame-Options`) so the
form can be dropped into external landing pages, and the /submit endpoint
answers CORS preflights for direct cross-origin posts.
"""
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID
from xml.sax.saxutils import escape

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.tenancy import tenant_context
from app.models import Contact
from app.models.forms import Form

router = APIRouter()
logger = logging.getLogger(__name__)

PUBLIC_CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}


class FormSubmission(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    message: Optional[str] = None
    # Present in payloads for context/debugging; the server ignores it and
    # uses the form's own sub_account_id.
    sub_account_id: Optional[str] = None


async def _get_published_form(db: AsyncSession, form_id: UUID) -> Form:
    result = await db.execute(
        select(Form).where(Form.id == form_id, Form.is_published.is_(True))
    )
    form = result.scalar_one_or_none()
    if form is None:
        raise HTTPException(status_code=404, detail="Form not found or unpublished")
    return form


@router.options("/forms/{form_id}/submit", include_in_schema=False)
async def submit_preflight(form_id: UUID):
    return Response(status_code=204, headers=PUBLIC_CORS_HEADERS)


@router.get("/forms/{form_id}")
async def get_public_form(form_id: UUID, db: AsyncSession = Depends(get_db)):
    """Machine-readable definition for custom (non-iframe) embeds."""
    form = await _get_published_form(db, form_id)
    return JSONResponse(
        content={
            "id": str(form.id),
            "name": form.name,
            "fields": form.fields_json,
            "configurations": form.configurations_json,
        },
        headers=PUBLIC_CORS_HEADERS,
    )


@router.post("/forms/{form_id}/submit")
async def submit_form(
    form_id: UUID, data: FormSubmission, db: AsyncSession = Depends(get_db)
):
    """Map a public submission directly into a new Contact in the
    sub-account that owns the form, then fire automation triggers."""
    form = await _get_published_form(db, form_id)

    # Server-side required-field validation from the builder config
    payload = data.model_dump()
    for field in form.fields_json:
        if (
            field.get("enabled")
            and field.get("required")
            and field["key"] != "sub_account_id"
            and not (payload.get(field["key"]) or "").strip()
        ):
            raise HTTPException(
                status_code=422, detail=f"{field.get('label', field['key'])} is required"
            )

    with tenant_context(form.sub_account_id):
        contact = Contact(
            sub_account_id=form.sub_account_id,
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            phone=data.phone,
            custom_fields={"message": data.message} if data.message else {},
            source="form",
            source_id=str(form.id),
            sms_consent=bool(data.phone),
            email_consent=bool(data.email),
        )
        db.add(contact)
        form.submission_count += 1
        form.updated_at = datetime.utcnow()
        await db.flush()

        # Speed-to-lead: enroll the new contact in any form-submission workflows
        from app.services.workflow_engine import trigger_workflows

        await trigger_workflows(
            db,
            sub_account_id=form.sub_account_id,
            trigger_type="form_submission",
            contact=contact,
            context={"form_id": str(form.id), "form_name": form.name},
        )

        await db.commit()

    success_message = (form.configurations_json or {}).get(
        "success_message", "Thanks! We'll be in touch."
    )
    return JSONResponse(
        content={
            "submitted": True,
            "contact_id": str(contact.id),
            "message": success_message,
        },
        headers=PUBLIC_CORS_HEADERS,
    )


@router.get("/forms/{form_id}/render", response_class=HTMLResponse)
async def render_form(form_id: UUID, db: AsyncSession = Depends(get_db)):
    """Self-contained HTML document designed to live inside an iframe on
    any external landing page."""
    form = await _get_published_form(db, form_id)

    config = form.configurations_json or {}
    theme = config.get("theme", {})
    background = theme.get("background", "#09090e")
    accent = theme.get("accent", "#8b5cf6")
    text_color = theme.get("text", "#e5e7eb")
    submit_label = escape(config.get("submit_label", "Send"))

    inputs_html = []
    for field in form.fields_json:
        if not field.get("enabled"):
            continue
        key = escape(field["key"])
        label = escape(field.get("label", key))
        required = "required" if field.get("required") else ""
        if field["type"] == "hidden":
            inputs_html.append(
                f'<input type="hidden" name="{key}" value="{form.sub_account_id}">'
            )
        elif field["type"] == "textarea":
            inputs_html.append(
                f'<label>{label}{"<span>*</span>" if required else ""}'
                f'<textarea name="{key}" rows="4" {required}></textarea></label>'
            )
        else:
            input_type = escape(field.get("type", "text"))
            inputs_html.append(
                f'<label>{label}{"<span>*</span>" if required else ""}'
                f'<input type="{input_type}" name="{key}" {required}></label>'
            )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(form.name)}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; }}
  body {{
    font-family: ui-sans-serif, system-ui, -apple-system, sans-serif;
    background: {background}; color: {text_color}; padding: 24px;
  }}
  form {{ display: flex; flex-direction: column; gap: 14px; max-width: 480px; margin: 0 auto; }}
  h2 {{ font-size: 18px; margin-bottom: 4px; }}
  label {{ display: flex; flex-direction: column; gap: 6px; font-size: 13px; }}
  label span {{ color: {accent}; margin-left: 2px; }}
  input, textarea {{
    background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.14);
    border-radius: 8px; padding: 10px 12px; color: {text_color}; font-size: 14px;
  }}
  input:focus, textarea:focus {{ outline: none; border-color: {accent}; }}
  button {{
    background: {accent}; color: #fff; border: none; border-radius: 8px;
    padding: 12px; font-size: 14px; font-weight: 600; cursor: pointer;
  }}
  button:disabled {{ opacity: 0.6; cursor: wait; }}
  .success {{ text-align: center; padding: 40px 16px; font-size: 15px; }}
  .error {{ color: #f87171; font-size: 13px; }}
</style>
</head>
<body>
<form id="lead-form">
  <h2>{escape(form.name)}</h2>
  {''.join(inputs_html)}
  <p class="error" id="form-error" hidden></p>
  <button type="submit" id="submit-btn">{submit_label}</button>
</form>
<script>
  const formEl = document.getElementById('lead-form');
  formEl.addEventListener('submit', async (e) => {{
    e.preventDefault();
    const btn = document.getElementById('submit-btn');
    const errEl = document.getElementById('form-error');
    btn.disabled = true;
    errEl.hidden = true;
    const payload = Object.fromEntries(new FormData(formEl).entries());
    try {{
      const resp = await fetch('./submit', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify(payload),
      }});
      const body = await resp.json();
      if (!resp.ok) throw new Error(body.detail || 'Submission failed');
      document.body.innerHTML = '<p class="success">' + body.message + '</p>';
    }} catch (err) {{
      errEl.textContent = err.message;
      errEl.hidden = false;
      btn.disabled = false;
    }}
  }});
</script>
</body>
</html>"""

    # Explicitly allow this document to be framed anywhere — that is its job.
    return HTMLResponse(
        content=html,
        headers={
            "Content-Security-Policy": "frame-ancestors *",
            "Cache-Control": "no-store",
            **PUBLIC_CORS_HEADERS,
        },
    )
