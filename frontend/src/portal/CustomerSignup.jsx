// Customer Signup page — full registration form
import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Shield, Eye, EyeOff, Loader, AlertCircle, ArrowRight, CheckCircle, User } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

const INIT = {
    full_name: '',
    father_name: '',
    email: '',
    phone: '',
    password: '',
    confirm_password: '',
    permanent_address: '',
    current_address: '',
    gender: '',
    marital_status: '',
    same_address: false,
};

function validate(d) {
    const err = {};
    if (!d.full_name.trim()) err.full_name = 'Full name is required';
    if (!d.father_name.trim()) err.father_name = "Father's name is required";
    if (!d.email.trim() || !/\S+@\S+\.\S+/.test(d.email)) err.email = 'Valid email is required';
    if (!d.phone.trim() || d.phone.replace(/\D/g, '').length < 10) err.phone = 'Valid phone number is required';
    if (!d.password || d.password.length < 6) err.password = 'Password must be at least 6 characters';
    if (d.password !== d.confirm_password) err.confirm_password = 'Passwords do not match';
    if (!d.permanent_address.trim()) err.permanent_address = 'Permanent address is required';
    if (!d.same_address && !d.current_address.trim()) err.current_address = 'Current address is required';
    if (!d.gender) err.gender = 'Please select gender';
    if (!d.marital_status) err.marital_status = 'Please select marital status';
    return err;
}

export default function CustomerSignup() {
    const nav = useNavigate();
    const { signup } = useAuth();

    const [data, setData] = useState(INIT);
    const [errors, setErrors] = useState({});
    const [loading, setLoading] = useState(false);
    const [apiError, setApiError] = useState('');
    const [showPwd, setShowPwd] = useState(false);
    const [success, setSuccess] = useState(false);

    const set = (key, value) => {
        setData(prev => {
            const next = { ...prev, [key]: value };
            if (key === 'same_address' && value) next.current_address = prev.permanent_address;
            if (key === 'permanent_address' && prev.same_address) next.current_address = value;
            return next;
        });
        setErrors(prev => { const n = { ...prev }; delete n[key]; return n; });
        setApiError('');
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        const validationErrors = validate(data);
        if (Object.keys(validationErrors).length) { setErrors(validationErrors); return; }

        setLoading(true);
        try {
            await signup({
                full_name: data.full_name.trim(),
                father_name: data.father_name.trim(),
                email: data.email.trim(),
                phone: data.phone.trim(),
                password: data.password,
                permanent_address: data.permanent_address.trim(),
                current_address: data.same_address ? data.permanent_address.trim() : data.current_address.trim(),
                gender: data.gender,
                marital_status: data.marital_status,
            });
            setSuccess(true);
        } catch (err) {
            setApiError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const inputProps = (key, placeholder, type = 'text') => ({
        type,
        value: data[key],
        onChange: e => set(key, e.target.value),
        placeholder,
        className: `form-input ${errors[key] ? 'form-input-error' : ''}`,
        style: errors[key] ? { borderColor: '#f87171' } : {},
    });

    /* ── Success screen ── */
    if (success) return (
        <div style={{
            minHeight: '100vh', background: 'var(--bg-base)',
            backgroundImage: 'radial-gradient(ellipse 60% 40% at 50% 0%, rgba(99,102,241,0.1) 0%, transparent 60%)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '2rem',
        }}>
            <div className="portal-glass animate-scale" style={{ maxWidth: 460, width: '100%', padding: '3rem 2.5rem', textAlign: 'center' }}>
                <div style={{ width: 72, height: 72, borderRadius: '50%', background: 'rgba(16,185,129,0.12)', border: '2px solid #10b981', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1.5rem' }}>
                    <CheckCircle size={36} color="#10b981" />
                </div>
                <h2 style={{ marginBottom: '0.5rem' }}>Account Created!</h2>
                <p style={{ color: 'var(--text-secondary)', marginBottom: '0.375rem' }}>
                    Welcome to InClaim, <strong style={{ color: 'var(--text-primary)' }}>{data.full_name}</strong>
                </p>
                <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '2rem' }}>
                    You can now submit claims, upload documents, and track your claim status.
                </p>
                <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center', flexWrap: 'wrap' }}>
                    <button className="btn btn-secondary" onClick={() => nav('/portal')}>My Claims</button>
                    <button className="btn btn-primary" onClick={() => nav('/portal/submit')} style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }}>
                        Submit a Claim <ArrowRight size={14} />
                    </button>
                </div>
            </div>
        </div>
    );

    /* ── Registration form ── */
    return (
        <div style={{
            minHeight: '100vh', background: 'var(--bg-base)',
            backgroundImage: 'radial-gradient(ellipse 60% 40% at 50% 0%, rgba(99,102,241,0.1) 0%, transparent 60%)',
            display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '2rem 1rem',
        }}>

            {/* Header */}
            <div style={{ textAlign: 'center', marginBottom: '1.75rem', marginTop: '1rem' }}>
                <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.625rem', marginBottom: '1rem', cursor: 'pointer' }} onClick={() => nav('/')}>
                    <div style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', borderRadius: 10, padding: '8px', display: 'flex' }}>
                        <Shield size={22} color="#fff" />
                    </div>
                    <span style={{ fontWeight: 800, fontSize: '1.125rem', color: 'var(--text-primary)' }}>InClaim</span>
                </div>
                <h1 style={{ fontSize: '1.5rem', fontWeight: 800, marginBottom: '0.375rem', letterSpacing: '-0.03em' }}>Create your account</h1>
                <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Get started with your insurance claims in minutes</p>
            </div>

            {/* Card */}
            <div className="portal-glass" style={{ width: '100%', maxWidth: 600, padding: '2rem 2.25rem', marginBottom: '2rem' }}>
                <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>

                    {apiError && (
                        <div style={{ display: 'flex', gap: '0.625rem', alignItems: 'flex-start', padding: '0.75rem 0.875rem', background: 'rgba(248,113,113,0.09)', border: '1px solid rgba(248,113,113,0.25)', borderRadius: 10 }}>
                            <AlertCircle size={15} color="#f87171" style={{ flexShrink: 0, marginTop: 1 }} />
                            <span style={{ fontSize: '0.8125rem', color: '#f87171' }}>{apiError}</span>
                        </div>
                    )}

                    {/* ── Personal Info ── */}
                    <div>
                        <p style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: '#818cf8', marginBottom: '0.875rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <User size={13} /> Personal Information
                        </p>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                            <div className="form-group">
                                <label className="form-label">Full Name *</label>
                                <input {...inputProps('full_name', 'John Doe')} />
                                {errors.full_name && <span className="form-error">{errors.full_name}</span>}
                            </div>
                            <div className="form-group">
                                <label className="form-label">Father's Name *</label>
                                <input {...inputProps('father_name', 'Robert Doe')} />
                                {errors.father_name && <span className="form-error">{errors.father_name}</span>}
                            </div>
                            <div className="form-group">
                                <label className="form-label">Email Address *</label>
                                <input {...inputProps('email', 'you@example.com', 'email')} />
                                {errors.email && <span className="form-error">{errors.email}</span>}
                            </div>
                            <div className="form-group">
                                <label className="form-label">Phone Number *</label>
                                <input {...inputProps('phone', '+91 98765 43210', 'tel')} />
                                {errors.phone && <span className="form-error">{errors.phone}</span>}
                            </div>
                            <div className="form-group">
                                <label className="form-label">Gender *</label>
                                <select value={data.gender} onChange={e => set('gender', e.target.value)} className="form-select" style={errors.gender ? { borderColor: '#f87171' } : {}}>
                                    <option value="">Select gender</option>
                                    <option value="male">Male</option>
                                    <option value="female">Female</option>
                                    <option value="other">Other</option>
                                    <option value="prefer_not_to_say">Prefer not to say</option>
                                </select>
                                {errors.gender && <span className="form-error">{errors.gender}</span>}
                            </div>
                            <div className="form-group">
                                <label className="form-label">Marital Status *</label>
                                <select value={data.marital_status} onChange={e => set('marital_status', e.target.value)} className="form-select" style={errors.marital_status ? { borderColor: '#f87171' } : {}}>
                                    <option value="">Select status</option>
                                    <option value="single">Single</option>
                                    <option value="married">Married</option>
                                    <option value="divorced">Divorced</option>
                                    <option value="widowed">Widowed</option>
                                </select>
                                {errors.marital_status && <span className="form-error">{errors.marital_status}</span>}
                            </div>
                        </div>
                    </div>

                    {/* ── Address ── */}
                    <div>
                        <p style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: '#818cf8', marginBottom: '0.875rem' }}>📍 Address</p>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                            <div className="form-group">
                                <label className="form-label">Permanent Address *</label>
                                <textarea {...inputProps('permanent_address', '12, Park Street, Kolkata, WB 700016')}
                                    className="form-textarea" style={{ minHeight: 70, ...(errors.permanent_address ? { borderColor: '#f87171' } : {}) }}
                                    onChange={e => set('permanent_address', e.target.value)}
                                />
                                {errors.permanent_address && <span className="form-error">{errors.permanent_address}</span>}
                            </div>
                            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                                <input type="checkbox" checked={data.same_address} onChange={e => set('same_address', e.target.checked)} style={{ accentColor: '#6366f1' }} />
                                Current address is same as permanent address
                            </label>
                            {!data.same_address && (
                                <div className="form-group animate-fade">
                                    <label className="form-label">Current Address *</label>
                                    <textarea {...inputProps('current_address', '45, MG Road, Bengaluru, KA 560001')}
                                        className="form-textarea" style={{ minHeight: 70, ...(errors.current_address ? { borderColor: '#f87171' } : {}) }}
                                        onChange={e => set('current_address', e.target.value)}
                                    />
                                    {errors.current_address && <span className="form-error">{errors.current_address}</span>}
                                </div>
                            )}
                        </div>
                    </div>

                    {/* ── Password ── */}
                    <div>
                        <p style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: '#818cf8', marginBottom: '0.875rem' }}>🔒 Security</p>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                            <div className="form-group">
                                <label className="form-label">Password *</label>
                                <div style={{ position: 'relative' }}>
                                    <input
                                        type={showPwd ? 'text' : 'password'} placeholder="Min. 6 characters"
                                        value={data.password} onChange={e => set('password', e.target.value)}
                                        className="form-input" style={{ paddingRight: '2.75rem', ...(errors.password ? { borderColor: '#f87171' } : {}) }}
                                    />
                                    <button type="button" onClick={() => setShowPwd(s => !s)}
                                        style={{ position: 'absolute', right: '0.75rem', top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', display: 'flex' }}>
                                        {showPwd ? <EyeOff size={15} color="var(--text-muted)" /> : <Eye size={15} color="var(--text-muted)" />}
                                    </button>
                                </div>
                                {errors.password && <span className="form-error">{errors.password}</span>}
                            </div>
                            <div className="form-group">
                                <label className="form-label">Confirm Password *</label>
                                <input type="password" placeholder="Re-enter password"
                                    value={data.confirm_password} onChange={e => set('confirm_password', e.target.value)}
                                    className="form-input" style={errors.confirm_password ? { borderColor: '#f87171' } : {}}
                                />
                                {errors.confirm_password && <span className="form-error">{errors.confirm_password}</span>}
                            </div>
                        </div>
                    </div>

                    {/* Submit */}
                    <button type="submit" className="btn btn-primary btn-lg" disabled={loading}
                        style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', boxShadow: loading ? 'none' : '0 4px 16px rgba(99,102,241,0.4)', justifyContent: 'center', width: '100%' }}>
                        {loading
                            ? <><Loader size={15} style={{ animation: 'spin 1s linear infinite' }} /> Creating account…</>
                            : <>Create Account <ArrowRight size={15} /></>}
                    </button>
                </form>

                <div style={{ textAlign: 'center', marginTop: '1.5rem', paddingTop: '1.25rem', borderTop: '1px solid var(--border)', fontSize: '0.875rem', color: 'var(--text-muted)' }}>
                    Already have an account?{' '}
                    <Link to="/portal/login" style={{ color: '#818cf8', fontWeight: 700, textDecoration: 'none' }}>
                        Sign in →
                    </Link>
                </div>
            </div>

            <button onClick={() => nav('/')} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', fontSize: '0.8125rem' }}>
                ← Back to home
            </button>
        </div>
    );
}
