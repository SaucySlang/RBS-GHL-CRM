import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from './components/Layout';
import { ContactsPage } from './pages/ContactsPage';
import { ConversationsPage } from './pages/ConversationsPage';
import { PipelinePage } from './pages/PipelinePage';
import { FormsPage } from './pages/FormsPage';
import { AutomationsPage } from './pages/AutomationsPage';
import { ReceptionistPage } from './pages/ReceptionistPage';
import { BrandingPage } from './pages/BrandingPage';
import { LandingPage } from './pages/LandingPage';
import { ThemeProvider } from './theme/ThemeProvider';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <BrowserRouter>
          <Routes>
            {/* Public marketing page (outside the app shell) */}
            <Route path="/landing" element={<LandingPage />} />
            <Route path="/" element={<Layout />}>
              <Route index element={<Navigate to="/pipeline" replace />} />
              <Route path="pipeline" element={<PipelinePage />} />
              <Route path="contacts" element={<ContactsPage />} />
              <Route path="conversations" element={<ConversationsPage />} />
              <Route path="forms" element={<FormsPage />} />
              <Route path="automations" element={<AutomationsPage />} />
              <Route path="receptionist" element={<ReceptionistPage />} />
              <Route path="branding" element={<BrandingPage />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
