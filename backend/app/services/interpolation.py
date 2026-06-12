"""Merge-tag interpolation for outbound messages.

Replaces tags like ``{{contact.first_name}}`` and ``{{sub_account.name}}``
with live database values immediately before transmission. Unknown tags
resolve to an empty string so a typo never leaks braces to a customer.
"""
import re
from typing import Any, Mapping, Optional

TAG_PATTERN = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)\s*\}\}")


def _contact_namespace(contact) -> dict:
    if contact is None:
        return {}
    full_name = " ".join(p for p in [contact.first_name, contact.last_name] if p)
    return {
        "first_name": contact.first_name or "",
        "last_name": contact.last_name or "",
        "full_name": full_name,
        "email": contact.email or "",
        "phone": contact.phone or "",
        "source": contact.source or "",
    }


def _sub_account_namespace(sub_account) -> dict:
    if sub_account is None:
        return {}
    return {
        "name": sub_account.name or "",
        "industry": (
            sub_account.industry_type.value
            if hasattr(sub_account.industry_type, "value")
            else (sub_account.industry_type or "")
        ),
        "from_name": sub_account.from_name or sub_account.name or "",
        "reply_to_email": sub_account.reply_to_email or "",
        "phone": sub_account.twilio_phone_number or "",
        "custom_domain": sub_account.custom_domain or "",
    }


def render_merge_tags(
    template: str,
    contact=None,
    sub_account=None,
    extra: Optional[Mapping[str, Mapping[str, Any]]] = None,
) -> str:
    """Render a template against real database rows.

    >>> render_merge_tags("Hi {{contact.first_name}} — {{sub_account.name}} here")
    'Hi  —  here'
    """
    namespaces: dict[str, Mapping[str, Any]] = {
        "contact": _contact_namespace(contact),
        "sub_account": _sub_account_namespace(sub_account),
    }
    if extra:
        for key, values in extra.items():
            namespaces.setdefault(key, {})
            namespaces[key] = {**namespaces.get(key, {}), **values}

    def _replace(match: re.Match) -> str:
        namespace, attr = match.group(1), match.group(2)
        return str(namespaces.get(namespace, {}).get(attr, ""))

    return TAG_PATTERN.sub(_replace, template)
