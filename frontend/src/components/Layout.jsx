// App layout — sidebar + header shell
import { NavLink, useNavigate } from 'react-router-dom';
import {
    LayoutDashboard, FileText, PlusCircle, BarChart3,
    FolderOpen, Bell, Search, LogOut, Shield, Activity,
} from 'lucide-react';
import { useApp } from '../contexts/AppContext';

const NAV = [
    { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/claims', icon: FileText, label: 'Claims' },
    { to: '/claims/new', icon: PlusCircle, label: 'Submit Claim' },
    { to: '/documents', icon: FolderOpen, label: 'Documents' },
    { to: '/analytics', icon: BarChart3, label: 'Analytics' },
];

export default function Layout({ children }) {
    const { user } = useApp();
    const navigate = useNavigate();

    return (
        <div style={{ display: 'flex', minHeight: '100vh' }}>
            {/* ─── Sidebar ────────────────────────────────────────────── */}
            <aside style={{
                width: '240px', flexShrink: 0,
                background: 'rgba(8,16,38,0.95)',
                borderRight: '1px solid var(--border)',
                display: 'flex', flexDirection: 'column',
                position: 'fixed', top: 0, left: 0, bottom: 0,
                backdropFilter: 'blur(20px)', zIndex: 100,
            }}>
                {/* Logo */}
                <div style={{ padding: '1.5rem 1.25rem', borderBottom: '1px solid var(--border)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
                        <div style={{ background: 'linear-gradient(135deg, #4f8ef7, #a78bfa)', borderRadius: '10px', padding: '6px', display: 'flex' }}>
                            <Shield size={20} color="#fff" />
                        </div>
                        <div>
                            <div style={{ fontWeight: 800, fontSize: '0.9375rem', color: 'var(--text-primary)', lineHeight: 1.2 }}>InClaim</div>
                            <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', letterSpacing: '0.06em', textTransform: 'uppercase' }}>Insurance Suite</div>
                        </div>
                    </div>
                </div>

                {/* Nav */}
                <nav style={{ flex: 1, padding: '1rem 0.75rem', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                    {NAV.map(({ to, icon: Icon, label }) => (
                        <NavLink key={to} to={to} end={to === '/'} style={({ isActive }) => ({
                            display: 'flex', alignItems: 'center', gap: '0.75rem',
                            padding: '0.625rem 0.875rem', borderRadius: '10px',
                            textDecoration: 'none', fontSize: '0.875rem', fontWeight: 500,
                            transition: 'all 0.18s',
                            color: isActive ? 'var(--primary)' : 'var(--text-secondary)',
                            background: isActive ? 'rgba(79,142,247,0.12)' : 'transparent',
                            border: isActive ? '1px solid rgba(79,142,247,0.25)' : '1px solid transparent',
                        })}>
                            <Icon size={17} />
                            {label}
                        </NavLink>
                    ))}
                </nav>

                {/* Activity indicator */}
                <div style={{ padding: '0.875rem 1.25rem', borderTop: '1px solid var(--border)', borderBottom: '1px solid var(--border)', margin: '0 0.75rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <Activity size={13} color="var(--success)" />
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>All systems operational</span>
                    </div>
                </div>

                {/* User */}
                <div style={{ padding: '1rem 1.25rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <div style={{ width: 34, height: 34, borderRadius: '50%', background: 'linear-gradient(135deg, #4f8ef7, #a78bfa)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: '0.875rem', color: '#fff', flexShrink: 0 }}>
                        {user?.name?.charAt(0)}
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{user?.name}</div>
                        <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', textTransform: 'capitalize' }}>{user?.role}</div>
                    </div>
                    <button className="btn btn-ghost btn-icon" title="Sign out" onClick={() => { sessionStorage.removeItem('admin_auth'); navigate('/admin/login'); }}>
                        <LogOut size={14} color="var(--text-muted)" />
                    </button>
                </div>
            </aside>

            {/* ─── Main ───────────────────────────────────────────────── */}
            <div style={{ flex: 1, marginLeft: '240px', display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
                {/* Top header */}
                <header style={{
                    height: '64px', borderBottom: '1px solid var(--border)',
                    background: 'rgba(8,16,38,0.85)', backdropFilter: 'blur(16px)',
                    display: 'flex', alignItems: 'center', gap: '1rem',
                    padding: '0 2rem', position: 'sticky', top: 0, zIndex: 50,
                }}>
                    <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: '0.75rem', background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border)', borderRadius: '10px', padding: '0 0.875rem', maxWidth: '420px' }}>
                        <Search size={15} color="var(--text-muted)" />
                        <input placeholder="Search claims, documents…" style={{ background: 'transparent', border: 'none', outline: 'none', color: 'var(--text-primary)', fontSize: '0.875rem', flex: 1, padding: '0.5rem 0' }} />
                    </div>
                    <button className="btn btn-secondary btn-sm" onClick={() => navigate('/claims/new')}>
                        <PlusCircle size={14} /> New Claim
                    </button>
                    <button className="btn btn-ghost btn-icon" style={{ position: 'relative' }}>
                        <Bell size={17} color="var(--text-secondary)" />
                        <span style={{ position: 'absolute', top: 4, right: 4, width: 8, height: 8, background: 'var(--danger)', borderRadius: '50%', border: '2px solid var(--bg-base)' }} />
                    </button>
                </header>

                {/* Page content */}
                <main style={{ flex: 1, padding: '2rem', maxWidth: '1400px', width: '100%' }}>
                    {children}
                </main>
            </div>
        </div>
    );
}
