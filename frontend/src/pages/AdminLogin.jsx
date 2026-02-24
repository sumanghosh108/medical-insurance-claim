// Hidden staff login page — uses StaffDB for authentication
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, Eye, EyeOff, Lock, Loader, AlertCircle } from 'lucide-react';
import { StaffDB } from '../api/userDatabase';

export default function AdminLogin() {
    const nav = useNavigate();
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [showPwd, setShowPwd] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!username || !password) { setError('Please fill in all fields.'); return; }
        setError(''); setLoading(true);

        // Simulate network delay
        await new Promise(r => setTimeout(r, 900));

        const { user, error: authError } = StaffDB.authenticate(username.trim(), password);
        if (user) {
            sessionStorage.setItem('admin_auth', JSON.stringify({ ...user, ts: Date.now() }));
            nav('/dashboard');
        } else {
            setError(authError || 'Invalid username or password.');
        }
        setLoading(false);
    };

    // Get staff list for demo credentials
    const staffList = StaffDB.list().slice(0, 3);

    return (
        <div style={{
            minHeight: '100vh',
            background: 'var(--bg-base)',
            backgroundImage: 'radial-gradient(ellipse 60% 40% at 50% 20%, rgba(79,142,247,0.07) 0%, transparent 60%)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '2rem',
        }}>
            <div style={{ width: '100%', maxWidth: 400 }}>

                {/* Logo */}
                <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
                    <div style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', background: 'linear-gradient(135deg, #4f8ef7, #6366f1)', borderRadius: 14, padding: '10px', marginBottom: '1rem' }}>
                        <Shield size={28} color="#fff" />
                    </div>
                    <h1 style={{ fontSize: '1.375rem', fontWeight: 800, marginBottom: '0.25rem' }}>Staff Portal</h1>
                    <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>InClaim · Internal Access Only</p>
                </div>

                {/* Card */}
                <div className="glass-elevated" style={{ padding: '2rem 2.25rem' }}>
                    {/* Security notice */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.5rem', padding: '0.625rem 0.875rem', background: 'rgba(79,142,247,0.07)', border: '1px solid rgba(79,142,247,0.15)', borderRadius: 8 }}>
                        <Lock size={13} color="var(--primary)" />
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Authorised personnel only. All access is monitored and logged.</span>
                    </div>

                    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        {/* Error banner */}
                        {error && (
                            <div style={{ display: 'flex', gap: '0.625rem', alignItems: 'flex-start', padding: '0.75rem 0.875rem', background: 'rgba(248,113,113,0.09)', border: '1px solid rgba(248,113,113,0.25)', borderRadius: 8 }}>
                                <AlertCircle size={15} color="var(--danger)" style={{ flexShrink: 0, marginTop: 1 }} />
                                <span style={{ fontSize: '0.8125rem', color: 'var(--danger)' }}>{error}</span>
                            </div>
                        )}

                        {/* Username */}
                        <div className="form-group">
                            <label className="form-label">Username</label>
                            <input
                                type="text"
                                autoComplete="username"
                                placeholder="Enter your username"
                                value={username}
                                onChange={e => { setUsername(e.target.value); setError(''); }}
                                className="form-input"
                                required
                            />
                        </div>

                        {/* Password */}
                        <div className="form-group">
                            <label className="form-label">Password</label>
                            <div style={{ position: 'relative' }}>
                                <input
                                    type={showPwd ? 'text' : 'password'}
                                    autoComplete="current-password"
                                    placeholder="Enter your password"
                                    value={password}
                                    onChange={e => { setPassword(e.target.value); setError(''); }}
                                    className="form-input"
                                    style={{ paddingRight: '2.75rem' }}
                                    required
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPwd(s => !s)}
                                    style={{ position: 'absolute', right: '0.75rem', top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', padding: 2, display: 'flex' }}
                                >
                                    {showPwd ? <EyeOff size={16} color="var(--text-muted)" /> : <Eye size={16} color="var(--text-muted)" />}
                                </button>
                            </div>
                        </div>

                        {/* Submit */}
                        <button
                            type="submit"
                            className="btn btn-primary btn-lg"
                            disabled={loading || !username || !password}
                            style={{ marginTop: '0.5rem', justifyContent: 'center', width: '100%' }}
                        >
                            {loading
                                ? <><Loader size={16} style={{ animation: 'spin 1s linear infinite' }} /> Verifying…</>
                                : 'Sign In to Staff Panel'
                            }
                        </button>
                    </form>

                    <div className="divider" style={{ margin: '1.25rem 0' }} />

                    {/* Demo credentials from database */}
                    <div style={{ background: 'rgba(255,255,255,0.02)', borderRadius: 8, padding: '0.75rem', border: '1px dashed rgba(255,255,255,0.07)' }}>
                        <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '0.375rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Demo Credentials</p>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                            {[
                                { username: 'admin', password: 'admin123', role: 'Administrator', dept: 'IT' },
                                { username: 'adjuster', password: 'staff2024', role: 'Claims Adjuster', dept: 'Claims' },
                                { username: 'manager', password: 'manager@1', role: 'Senior Manager', dept: 'Management' },
                            ].map(c => (
                                <button key={c.username} type="button" onClick={() => { setUsername(c.username); setPassword(c.password); setError(''); }}
                                    style={{ background: 'none', border: 'none', cursor: 'pointer', textAlign: 'left', padding: '0.2rem 0', fontSize: '0.75rem', color: 'var(--text-muted)' }}
                                    onMouseEnter={e => e.target.style.color = 'var(--primary)'}
                                    onMouseLeave={e => e.target.style.color = 'var(--text-muted)'}
                                >
                                    <span style={{ fontFamily: 'monospace' }}>{c.username}</span> / <span style={{ fontFamily: 'monospace' }}>{c.password}</span>
                                    <span style={{ marginLeft: '0.375rem', opacity: 0.6 }}>({c.role})</span>
                                </button>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Stats */}
                <div style={{ textAlign: 'center', marginTop: '1rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    <span>{StaffDB.count()} staff accounts</span> · <span>{StaffDB.departments().length} departments</span>
                </div>

                {/* Back link */}
                <div style={{ textAlign: 'center', marginTop: '1rem' }}>
                    <button
                        onClick={() => nav('/')}
                        style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', fontSize: '0.8125rem' }}
                        onMouseEnter={e => e.target.style.color = 'var(--text-secondary)'}
                        onMouseLeave={e => e.target.style.color = 'var(--text-muted)'}
                    >
                        ← Back to InClaim
                    </button>
                </div>
            </div>
        </div>
    );
}
