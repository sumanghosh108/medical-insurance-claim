// Customer Login page
import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Shield, Eye, EyeOff, Loader, AlertCircle, ArrowRight, Mail, Lock } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

export default function CustomerLogin() {
    const nav = useNavigate();
    const { login } = useAuth();

    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [showPwd, setShowPwd] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!email || !password) { setError('Please fill in all fields.'); return; }
        setError(''); setLoading(true);
        try {
            await login(email, password);
            nav('/portal');
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{
            minHeight: '100vh', background: 'var(--bg-base)',
            backgroundImage: 'radial-gradient(ellipse 60% 40% at 50% 0%, rgba(99,102,241,0.1) 0%, transparent 60%)',
            display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '2rem',
        }}>

            {/* Logo */}
            <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
                <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.625rem', marginBottom: '1rem', cursor: 'pointer' }} onClick={() => nav('/')}>
                    <div style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', borderRadius: 10, padding: '8px', display: 'flex' }}>
                        <Shield size={22} color="#fff" />
                    </div>
                    <span style={{ fontWeight: 800, fontSize: '1.125rem', color: 'var(--text-primary)' }}>InClaim</span>
                </div>
                <h1 style={{ fontSize: '1.625rem', fontWeight: 800, marginBottom: '0.375rem', letterSpacing: '-0.03em' }}>Welcome back</h1>
                <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Sign in to manage your claims</p>
            </div>

            {/* Card */}
            <div className="portal-glass" style={{ width: '100%', maxWidth: 420, padding: '2rem 2.25rem' }}>
                <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>

                    {/* Error */}
                    {error && (
                        <div style={{ display: 'flex', gap: '0.625rem', alignItems: 'flex-start', padding: '0.75rem 0.875rem', background: 'rgba(248,113,113,0.09)', border: '1px solid rgba(248,113,113,0.25)', borderRadius: 10 }}>
                            <AlertCircle size={15} color="#f87171" style={{ flexShrink: 0, marginTop: 1 }} />
                            <span style={{ fontSize: '0.8125rem', color: '#f87171' }}>{error}</span>
                        </div>
                    )}

                    {/* Email */}
                    <div className="form-group">
                        <label className="form-label">Email Address</label>
                        <div style={{ position: 'relative' }}>
                            <Mail size={15} color="var(--text-muted)" style={{ position: 'absolute', left: '0.875rem', top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none' }} />
                            <input
                                type="email" autoComplete="email" placeholder="you@example.com"
                                value={email} onChange={e => { setEmail(e.target.value); setError(''); }}
                                className="form-input" style={{ paddingLeft: '2.5rem' }}
                                required
                            />
                        </div>
                    </div>

                    {/* Password */}
                    <div className="form-group">
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.375rem' }}>
                            <label className="form-label" style={{ margin: 0 }}>Password</label>
                            <a href="#" style={{ fontSize: '0.75rem', color: '#818cf8', textDecoration: 'none' }}>Forgot password?</a>
                        </div>
                        <div style={{ position: 'relative' }}>
                            <Lock size={15} color="var(--text-muted)" style={{ position: 'absolute', left: '0.875rem', top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none' }} />
                            <input
                                type={showPwd ? 'text' : 'password'} autoComplete="current-password"
                                placeholder="Enter your password"
                                value={password} onChange={e => { setPassword(e.target.value); setError(''); }}
                                className="form-input" style={{ paddingLeft: '2.5rem', paddingRight: '2.75rem' }}
                                required
                            />
                            <button type="button" onClick={() => setShowPwd(s => !s)}
                                style={{ position: 'absolute', right: '0.75rem', top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', padding: 2, display: 'flex' }}>
                                {showPwd ? <EyeOff size={15} color="var(--text-muted)" /> : <Eye size={15} color="var(--text-muted)" />}
                            </button>
                        </div>
                    </div>

                    {/* Demo hint */}
                    <div style={{ padding: '0.625rem 0.75rem', background: 'rgba(99,102,241,0.06)', border: '1px dashed rgba(99,102,241,0.2)', borderRadius: 8 }}>
                        <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', margin: '0 0 0.25rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Demo</p>
                        <button type="button" onClick={() => { setEmail('suman@example.com'); setPassword('test@123'); setError(''); }}
                            style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0, fontSize: '0.8rem', color: '#818cf8', fontFamily: 'monospace' }}>
                            suman@example.com / test@123
                        </button>
                    </div>

                    {/* Submit */}
                    <button type="submit" className="btn btn-primary btn-lg" disabled={loading}
                        style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', boxShadow: loading ? 'none' : '0 4px 16px rgba(99,102,241,0.4)', justifyContent: 'center', width: '100%', marginTop: '0.25rem' }}>
                        {loading
                            ? <><Loader size={15} style={{ animation: 'spin 1s linear infinite' }} /> Signing in…</>
                            : <>Sign In <ArrowRight size={15} /></>}
                    </button>
                </form>

                <div style={{ textAlign: 'center', marginTop: '1.5rem', paddingTop: '1.25rem', borderTop: '1px solid var(--border)', fontSize: '0.875rem', color: 'var(--text-muted)' }}>
                    Don't have an account?{' '}
                    <Link to="/portal/signup" style={{ color: '#818cf8', fontWeight: 700, textDecoration: 'none' }}>
                        Create free account →
                    </Link>
                </div>
            </div>

            <button onClick={() => nav('/')} style={{ marginTop: '1.5rem', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', fontSize: '0.8125rem' }}>
                ← Back to home
            </button>
        </div>
    );
}
