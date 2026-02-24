import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AppProvider } from './contexts/AppContext';
import { AuthProvider } from './contexts/AuthContext';

// Landing
import Landing from './pages/Landing';
import AdminLogin from './pages/AdminLogin';

// Admin panel
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import ClaimsList from './pages/ClaimsList';
import ClaimDetail from './pages/ClaimDetail';
import SubmitClaim from './pages/SubmitClaim';
import Documents from './pages/Documents';
import Analytics from './pages/Analytics';

// Customer portal — auth
import CustomerLogin from './portal/CustomerLogin';
import CustomerSignup from './portal/CustomerSignup';
import ProtectedRoute from './portal/ProtectedRoute';

// Customer portal — pages
import PortalLayout from './portal/PortalLayout';
import MyClaims from './portal/MyClaims';
import CustomerSubmit from './portal/CustomerSubmit';
import CustomerUpload from './portal/CustomerUpload';
import ClaimStatus from './portal/ClaimStatus';
import Help from './portal/Help';

function Portal({ children }) {
  return (
    <ProtectedRoute>
      <PortalLayout>{children}</PortalLayout>
    </ProtectedRoute>
  );
}

export default function App() {
  return (
    <AppProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            {/* ── Public ──────────────────── */}
            <Route path="/" element={<Landing />} />
            <Route path="/portal/login" element={<CustomerLogin />} />
            <Route path="/portal/signup" element={<CustomerSignup />} />

            {/* ── Admin (hidden) ──────────── */}
            <Route path="/admin/login" element={<AdminLogin />} />
            <Route path="/dashboard" element={<Layout><Dashboard /></Layout>} />
            <Route path="/claims" element={<Layout><ClaimsList /></Layout>} />
            <Route path="/claims/new" element={<Layout><SubmitClaim /></Layout>} />
            <Route path="/claims/:id" element={<Layout><ClaimDetail /></Layout>} />
            <Route path="/documents" element={<Layout><Documents /></Layout>} />
            <Route path="/analytics" element={<Layout><Analytics /></Layout>} />

            {/* ── Customer Portal (protected) ── */}
            <Route path="/portal" element={<Portal><MyClaims /></Portal>} />
            <Route path="/portal/submit" element={<Portal><CustomerSubmit /></Portal>} />
            <Route path="/portal/upload" element={<Portal><CustomerUpload /></Portal>} />
            <Route path="/portal/status/:id" element={<Portal><ClaimStatus /></Portal>} />
            <Route path="/portal/help" element={<Portal><Help /></Portal>} />

            {/* Fallback */}
            <Route path="*" element={<Landing />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </AppProvider>
  );
}
