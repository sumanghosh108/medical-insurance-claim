// Submit Claim — 4-step wizard
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCircle, ChevronRight, ChevronLeft, Loader } from 'lucide-react';
import { submitClaim } from '../api/claims';
import { useApp } from '../contexts/AppContext';

const STEPS = ['Personal Info', 'Policy & Incident', 'Claim Amount', 'Review & Submit'];

function StepIndicator({ current }) {
    return (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0', marginBottom: '2rem' }}>
            {STEPS.map((s, i) => {
                const done = i < current, active = i === current;
                return (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', flex: i < STEPS.length - 1 ? 1 : 'none' }}>
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.375rem', flexShrink: 0 }}>
                            <div style={{
                                width: 32, height: 32, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.8125rem', fontWeight: 700, transition: 'all 0.3s',
                                background: done ? 'var(--success)' : active ? 'var(--primary)' : 'rgba(255,255,255,0.06)',
                                border: done || active ? 'none' : '1px solid var(--border)',
                                color: done || active ? '#fff' : 'var(--text-muted)',
                            }}>
                                {done ? <CheckCircle size={16} /> : i + 1}
                            </div>
                            <span style={{ fontSize: '0.7rem', fontWeight: 600, color: active ? 'var(--primary)' : done ? 'var(--success)' : 'var(--text-muted)', whiteSpace: 'nowrap', textAlign: 'center' }}>{s}</span>
                        </div>
                        {i < STEPS.length - 1 && <div style={{ flex: 1, height: 2, background: i < current ? 'var(--success)' : 'var(--border)', margin: '0 0.5rem', marginBottom: '1.1rem', transition: 'background 0.3s' }} />}
                    </div>
                );
            })}
        </div>
    );
}

function Field({ label, error, children }) {
    return (
        <div className="form-group">
            <label className="form-label">{label}</label>
            {children}
            {error && <span className="form-error">{error}</span>}
        </div>
    );
}

const INIT = {
    claim_type: 'health',
    personal_info: { first_name: '', last_name: '', email: '', phone: '', address: '', date_of_birth: '' },
    policy_info: { policy_number: '', policy_holder_name: '', coverage_type: '', effective_date: '' },
    incident_info: { incident_date: '', incident_location: '', description: '', incident_type: '' },
    amount: { claimed_amount: '', currency: 'USD' },
    medical_info: { provider_name: '', diagnosis_codes: '', treatment_date: '' },
    additional_notes: '',
    priority: 'medium',
};

function validate(step, data) {
    const err = {};
    if (step === 0) {
        if (!data.personal_info.first_name) err['personal_info.first_name'] = 'Required';
        if (!data.personal_info.last_name) err['personal_info.last_name'] = 'Required';
        if (!data.personal_info.email || !data.personal_info.email.includes('@')) err['personal_info.email'] = 'Valid email required';
        if (!data.personal_info.phone) err['personal_info.phone'] = 'Required';
        if (!data.personal_info.address) err['personal_info.address'] = 'Required';
    }
    if (step === 1) {
        if (!data.policy_info.policy_number) err['policy_info.policy_number'] = 'Required';
        if (!data.incident_info.incident_date) err['incident_info.incident_date'] = 'Required';
        if (!data.incident_info.description || data.incident_info.description.length < 10) err['incident_info.description'] = 'At least 10 characters';
    }
    if (step === 2) {
        if (!data.amount.claimed_amount || isNaN(data.amount.claimed_amount) || Number(data.amount.claimed_amount) <= 0) err['amount.claimed_amount'] = 'Enter a valid positive amount';
    }
    return err;
}

function get(obj, path) { return path.split('.').reduce((o, k) => o?.[k], obj); }
function set(obj, path, val) {
    const keys = path.split('.');
    return keys.reduceRight((v, k, i) => {
        if (i === keys.length - 1) return { ...get(obj, keys.slice(0, i).join('.') || '_'), [k]: v };
        return v;
    }, val);
}
// simple deep set helper
function deepSet(obj, path, value) {
    const result = JSON.parse(JSON.stringify(obj));
    const keys = path.split('.');
    let cur = result;
    for (let i = 0; i < keys.length - 1; i++) cur = cur[keys[i]];
    cur[keys[keys.length - 1]] = value;
    return result;
}

export default function SubmitClaim() {
    const nav = useNavigate();
    const { addNotification } = useApp();
    const [step, setStep] = useState(0);
    const [data, setData] = useState(INIT);
    const [errors, setErrors] = useState({});
    const [submitting, setSub] = useState(false);
    const [submitted, setSubmitted] = useState(null);

    const update = (path, value) => {
        setData(prev => deepSet(prev, path, value));
        setErrors(prev => { const next = { ...prev }; delete next[path]; return next; });
    };

    const next = () => {
        const err = validate(step, data);
        if (Object.keys(err).length) { setErrors(err); return; }
        setStep(s => s + 1);
    };

    const submit = async () => {
        setSub(true);
        try {
            const payload = {
                ...data,
                amount: { ...data.amount, claimed_amount: Number(data.amount.claimed_amount) },
                medical_info: data.claim_type === 'health' ? {
                    ...data.medical_info,
                    diagnosis_codes: data.medical_info.diagnosis_codes.split(/[\s,]+/).filter(Boolean),
                    provider_name: data.medical_info.provider_name,
                } : undefined,
            };
            const res = await submitClaim(payload);
            setSubmitted(res);
            addNotification('Claim submitted successfully!', 'success');
        } catch (e) {
            addNotification('Submission failed: ' + e.message, 'error');
        } finally { setSub(false); }
    };

    if (submitted) return (
        <div className="animate-scale" style={{ maxWidth: 520, margin: '4rem auto', textAlign: 'center' }}>
            <div className="glass-elevated" style={{ padding: '3rem' }}>
                <div style={{ width: 64, height: 64, borderRadius: '50%', background: 'rgba(52,211,153,0.15)', border: '2px solid var(--success)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1.5rem' }}>
                    <CheckCircle size={32} color="var(--success)" />
                </div>
                <h2 style={{ marginBottom: '0.5rem' }}>Claim Submitted!</h2>
                <p style={{ marginBottom: '0.25rem' }}>Claim number: <strong style={{ color: 'var(--primary)', fontFamily: 'monospace' }}>{submitted.metadata?.claim_number}</strong></p>
                <p style={{ fontSize: '0.875rem', marginBottom: '1.5rem' }}>Your claim is now being processed. You'll receive updates by email.</p>
                <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center' }}>
                    <button className="btn btn-secondary" onClick={() => nav('/claims')}>View All Claims</button>
                    <button className="btn btn-primary" onClick={() => { setSubmitted(null); setStep(0); setData(INIT); }}>Submit Another</button>
                </div>
            </div>
        </div>
    );

    const inp = (path, placeholder, type = 'text') => (
        <input type={type} placeholder={placeholder} value={get(data, path) || ''} onChange={e => update(path, e.target.value)} className="form-input" />
    );
    const err = (path) => errors[path] ? <span className="form-error">{errors[path]}</span> : null;

    return (
        <div className="animate-fade" style={{ maxWidth: 760, margin: '0 auto' }}>
            <div style={{ marginBottom: '1.5rem' }}>
                <h1>Submit New Claim</h1>
                <p>Complete all required fields to submit your insurance claim</p>
            </div>

            <div className="glass-elevated" style={{ padding: '2rem' }}>
                <StepIndicator current={step} />

                {/* Step 0: Personal */}
                {step === 0 && (
                    <div className="animate-fade" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                        <div className="form-group" style={{ gridColumn: '1/-1' }}>
                            <label className="form-label">Claim Type</label>
                            <select value={data.claim_type} onChange={e => update('claim_type', e.target.value)} className="form-select">
                                {['health', 'auto', 'property', 'life'].map(t => <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>)}
                            </select>
                        </div>
                        <div className="form-group"><label className="form-label">First Name *</label>{inp('personal_info.first_name', 'John')}{err('personal_info.first_name')}</div>
                        <div className="form-group"><label className="form-label">Last Name *</label>{inp('personal_info.last_name', 'Doe')}{err('personal_info.last_name')}</div>
                        <div className="form-group"><label className="form-label">Email *</label>{inp('personal_info.email', 'john@example.com', 'email')}{err('personal_info.email')}</div>
                        <div className="form-group"><label className="form-label">Phone *</label>{inp('personal_info.phone', '+91 98765 43210', 'tel')}{err('personal_info.phone')}</div>
                        <div className="form-group"><label className="form-label">Date of Birth</label>{inp('personal_info.date_of_birth', '', 'date')}</div>
                        <div className="form-group"><label className="form-label">Priority</label>
                            <select value={data.priority} onChange={e => update('priority', e.target.value)} className="form-select">
                                {['low', 'medium', 'high', 'urgent'].map(p => <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>)}
                            </select>
                        </div>
                        <div className="form-group" style={{ gridColumn: '1/-1' }}><label className="form-label">Address *</label>{inp('personal_info.address', '123 Main St, City, State 12345')}{err('personal_info.address')}</div>
                    </div>
                )}

                {/* Step 1: Policy + Incident */}
                {step === 1 && (
                    <div className="animate-fade" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                        <div>
                            <h4 style={{ color: 'var(--primary)', marginBottom: '0.875rem', fontSize: '0.8125rem', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Policy Information</h4>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                                <div className="form-group"><label className="form-label">Policy Number *</label>{inp('policy_info.policy_number', 'AB1234567')}{err('policy_info.policy_number')}</div>
                                <div className="form-group"><label className="form-label">Policy Holder</label>{inp('policy_info.policy_holder_name', 'John Doe')}</div>
                                <div className="form-group"><label className="form-label">Coverage Type</label>{inp('policy_info.coverage_type', 'Comprehensive Health')}</div>
                                <div className="form-group"><label className="form-label">Effective Date</label>{inp('policy_info.effective_date', '', 'date')}</div>
                            </div>
                        </div>
                        <div className="divider" />
                        <div>
                            <h4 style={{ color: 'var(--primary)', marginBottom: '0.875rem', fontSize: '0.8125rem', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Incident Details</h4>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                                <div className="form-group"><label className="form-label">Incident Date *</label>{inp('incident_info.incident_date', '', 'date')}{err('incident_info.incident_date')}</div>
                                <div className="form-group"><label className="form-label">Incident Type</label>{inp('incident_info.incident_type', 'e.g. Auto Accident')}</div>
                                <div className="form-group" style={{ gridColumn: '1/-1' }}><label className="form-label">Location</label>{inp('incident_info.incident_location', '123 Main St, City')}</div>
                                <div className="form-group" style={{ gridColumn: '1/-1' }}><label className="form-label">Description *</label><textarea value={data.incident_info.description} onChange={e => update('incident_info.description', e.target.value)} className="form-textarea" placeholder="Describe the incident in detail (minimum 10 characters)…" style={{ minHeight: 100 }} />{err('incident_info.description')}</div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Step 2: Amount */}
                {step === 2 && (
                    <div className="animate-fade" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1rem' }}>
                            <div className="form-group">
                                <label className="form-label">Claimed Amount (USD) *</label>
                                <input type="number" min="0" step="0.01" placeholder="0.00" value={data.amount.claimed_amount} onChange={e => update('amount.claimed_amount', e.target.value)} className="form-input" style={{ fontSize: '1.25rem', fontWeight: 700 }} />
                                {err('amount.claimed_amount')}
                            </div>
                            <div className="form-group">
                                <label className="form-label">Currency</label>
                                <select value={data.amount.currency} onChange={e => update('amount.currency', e.target.value)} className="form-select">
                                    {['USD', 'EUR', 'GBP', 'INR'].map(c => <option key={c} value={c}>{c}</option>)}
                                </select>
                            </div>
                        </div>

                        {data.claim_type === 'health' && (
                            <>
                                <div className="divider" />
                                <h4 style={{ color: 'var(--primary)', fontSize: '0.8125rem', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Medical Information</h4>
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                                    <div className="form-group"><label className="form-label">Provider Name *</label>{inp('medical_info.provider_name', 'Dr. Smith')}</div>
                                    <div className="form-group"><label className="form-label">Treatment Date</label>{inp('medical_info.treatment_date', '', 'date')}</div>
                                    <div className="form-group" style={{ gridColumn: '1/-1' }}>
                                        <label className="form-label">ICD-10 Diagnosis Codes *</label>
                                        <input placeholder="E11.9, I10 (comma separated)" value={data.medical_info.diagnosis_codes} onChange={e => update('medical_info.diagnosis_codes', e.target.value)} className="form-input" />
                                    </div>
                                </div>
                            </>
                        )}

                        <div className="form-group">
                            <label className="form-label">Additional Notes</label>
                            <textarea value={data.additional_notes} onChange={e => update('additional_notes', e.target.value)} placeholder="Any additional information…" className="form-textarea" style={{ minHeight: 80 }} />
                        </div>
                    </div>
                )}

                {/* Step 3: Review */}
                {step === 3 && (
                    <div className="animate-fade" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        <div className="glass" style={{ padding: '1.25rem' }}>
                            <h4 style={{ color: 'var(--primary)', marginBottom: '0.75rem' }}>Personal</h4>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', fontSize: '0.875rem' }}>
                                <span style={{ color: 'var(--text-muted)' }}>Name</span><span>{data.personal_info.first_name} {data.personal_info.last_name}</span>
                                <span style={{ color: 'var(--text-muted)' }}>Email</span><span>{data.personal_info.email}</span>
                                <span style={{ color: 'var(--text-muted)' }}>Phone</span><span>{data.personal_info.phone}</span>
                            </div>
                        </div>
                        <div className="glass" style={{ padding: '1.25rem' }}>
                            <h4 style={{ color: 'var(--primary)', marginBottom: '0.75rem' }}>Claim Details</h4>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', fontSize: '0.875rem' }}>
                                <span style={{ color: 'var(--text-muted)' }}>Type</span><span style={{ textTransform: 'capitalize' }}>{data.claim_type}</span>
                                <span style={{ color: 'var(--text-muted)' }}>Amount</span><span style={{ fontWeight: 700, color: 'var(--primary)', fontSize: '1rem' }}>${Number(data.amount.claimed_amount || 0).toLocaleString()} {data.amount.currency}</span>
                                <span style={{ color: 'var(--text-muted)' }}>Policy #</span><span>{data.policy_info.policy_number || '—'}</span>
                                <span style={{ color: 'var(--text-muted)' }}>Priority</span><span style={{ textTransform: 'capitalize' }}>{data.priority}</span>
                            </div>
                        </div>
                        <div className="glass" style={{ padding: '1.25rem' }}>
                            <h4 style={{ color: 'var(--primary)', marginBottom: '0.75rem' }}>Incident</h4>
                            <p style={{ fontSize: '0.875rem', color: 'var(--text-primary)', lineHeight: 1.6 }}>{data.incident_info.description || '—'}</p>
                        </div>
                    </div>
                )}

                {/* Navigation */}
                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '2rem', paddingTop: '1.25rem', borderTop: '1px solid var(--border)' }}>
                    <button className="btn btn-secondary" onClick={() => step === 0 ? nav('/claims') : setStep(s => s - 1)} disabled={submitting}>
                        <ChevronLeft size={15} />{step === 0 ? 'Cancel' : 'Back'}
                    </button>
                    {step < STEPS.length - 1
                        ? <button className="btn btn-primary" onClick={next}>Continue <ChevronRight size={15} /></button>
                        : <button className="btn btn-primary btn-lg" onClick={submit} disabled={submitting}>
                            {submitting ? <><Loader size={15} style={{ animation: 'spin 1s linear infinite' }} /> Submitting…</> : <>Submit Claim <CheckCircle size={15} /></>}
                        </button>
                    }
                </div>
            </div>
        </div>
    );
}
