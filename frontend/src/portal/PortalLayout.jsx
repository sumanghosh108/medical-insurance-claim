// Customer Portal Layout — lighter, friendlier than admin
import { NavLink, useNavigate } from 'react-router-dom';
import { Home, FileText, UploadCloud, HelpCircle, LogOut, Shield, ChevronRight } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import '../portal/portal.css';

const NAV = [
    { to: '/portal', icon: Home, label: 'My Claims', end: true },
    { to: '/portal/submit', icon: FileText, label: 'New Claim' },
    { to: '/portal/upload', icon: UploadCloud, label: 'Upload Documents' },
    { to: '/portal/help', icon: HelpCircle, label: 'Help & FAQ' },
];

export default function PortalLayout({ children }) {
    const { user, logout } = useAuth();
    const nav = useNavigate();

    const handleLogout = () => {
        logout();
        nav('/');
    };

    return (
        <div style={{ minHeight: '100vh', background: 'var(--portal-bg, var(--bg-base))', display: 'flex', flexDirection: 'column' }}>
            {/* Top nav bar */}
            <header style={{
                borderBottom: '1px solid var(--portal-border)',
                background: 'rgba(6,11,24,0.92)',
                backdropFilter: 'blur(20px)',
                position: 'sticky', top: 0, zIndex: 100,
            }}>
                <div style={{ maxWidth: 1100, margin: '0 auto', padding: '0 2rem', height: 64, display: 'flex', alignItems: 'center', gap: '2rem' }}>
                    {/* Logo */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', flexShrink: 0, cursor: 'pointer' }} onClick={() => nav('/portal')}>
                        <div style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', borderRadius: 10, padding: '6px', display: 'flex' }}>
                            <Shield size={18} color="#fff" />
                        </div>
                        <span style={{ fontWeight: 800, fontSize: '0.9375rem', color: 'var(--text-primary)' }}>InClaim</span>
                        <span style={{ fontSize: '0.75rem', background: 'rgba(99,102,241,0.15)', border: '1px solid rgba(99,102,241,0.3)', color: '#818cf8', padding: '0.15rem 0.5rem', borderRadius: 100, fontWeight: 700 }}>Customer</span>
                    </div>

                    {/* Nav links */}
                    <nav style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', flex: 1 }}>
                        {NAV.map(({ to, icon: Icon, label, end }) => (
                            <NavLink key={to} to={to} end={end} style={({ isActive }) => ({
                                display: 'flex', alignItems: 'center', gap: '0.5rem',
                                padding: '0.45rem 0.875rem', borderRadius: 8,
                                textDecoration: 'none', fontSize: '0.875rem', fontWeight: 500,
                                transition: 'all 0.18s',
                                color: isActive ? '#818cf8' : 'var(--text-secondary)',
                                background: isActive ? 'rgba(99,102,241,0.12)' : 'transparent',
                            })}>
                                <Icon size={15} />
                                {label}
                            </NavLink>
                        ))}
                    </nav>

                    {/* User + logout */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexShrink: 0 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <div style={{ width: 30, height: 30, borderRadius: '50%', background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: '0.8125rem', color: '#fff' }}>
                                {user?.full_name?.charAt(0) || 'U'}
                            </div>
                            <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-secondary)' }}>{user?.full_name?.split(' ')[0] || 'User'}</span>
                        </div>
                        <button className="btn btn-ghost btn-sm" onClick={handleLogout} style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                            <LogOut size={13} /> Logout
                        </button>
                    </div>
                </div>
            </header>

            {/* Breadcrumb strip */}
            <div style={{ background: 'rgba(99,102,241,0.04)', borderBottom: '1px solid var(--portal-border)' }}>
                <div style={{ maxWidth: 1100, margin: '0 auto', padding: '0.5rem 2rem', display: 'flex', alignItems: 'center', gap: '0.375rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    <button onClick={() => nav('/')} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: 0, fontSize: 'inherit' }}>Home</button>
                    <ChevronRight size={11} />
                    <span style={{ color: '#818cf8', fontWeight: 600 }}>Customer Portal</span>
                </div>
            </div>

            {/* Content */}
            <main style={{ flex: 1, maxWidth: 1100, width: '100%', margin: '0 auto', padding: '2rem' }}>
                {children}
            </main>

            {/* Footer */}
            <footer style={{ borderTop: '1px solid var(--portal-border)', padding: '1.25rem 2rem', textAlign: 'center', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                InClaim · Secure & HIPAA Compliant · <a href="#" style={{ color: '#818cf8', textDecoration: 'none' }}>Privacy Policy</a> · <a href="#" style={{ color: '#818cf8', textDecoration: 'none' }}>Contact Support</a>
            </footer>
        </div>
    );
}
