// Simplified claim submission for customers (3 steps)
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCircle, ChevronRight, ChevronLeft, Loader, UploadCloud } from 'lucide-react';
import { submitClaim } from '../api/claims';
import { useApp } from '../contexts/AppContext';

const STEPS = ['Your Details', 'Incident & Policy', 'Claim Amount'];

const INIT = {
    claim_type: 'health',
    personal_info: { first_name: '', last_name: '', email: '', phone: '', address: '' },
    policy_info: { policy_number: '', coverage_type: '' },
    incident_info: { incident_date: '', description: '', incident_location: '' },
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
    }
    if (step === 1) {
        if (!data.policy_info.policy_number) err['policy_info.policy_number'] = 'Required';
        if (!data.incident_info.incident_date) err['incident_info.incident_date'] = 'Required';
        if (!data.incident_info.description || data.incident_info.description.length < 10) err['incident_info.description'] = 'Please describe the incident (min. 10 characters)';
    }
    if (step === 2) {
        if (!data.amount.claimed_amount || isNaN(data.amount.claimed_amount) || Number(data.amount.claimed_amount) <= 0) err['amount.claimed_amount'] = 'Enter a valid amount';
    }
    return err;
}

function deepSet(obj, path, value) {
    const result = JSON.parse(JSON.stringify(obj));
    const keys = path.split('.');
    let cur = result;
    for (let i = 0; i < keys.length - 1; i++) cur = cur[keys[i]];
    cur[keys[keys.length - 1]] = value;
    return result;
}
function get(obj, path) { return path.split('.').reduce((o, k) => o?.[k], obj); }

export default function CustomerSubmit() {
    const nav = useNavigate();
    const { addNotification } = useApp();
    const [step, setStep] = useState(0);
    const [data, setData] = useState(INIT);
    const [errors, setErrors] = useState({});
    const [submitting, setSub] = useState(false);
    const [result, setResult] = useState(null);

    const inp = (path, placeholder, type = 'text') => (
        <>
            <input type={type} placeholder={placeholder} value={get(data, path) || ''} onChange={e => { setData(prev => deepSet(prev, path, e.target.value)); setErrors(prev => { const n = { ...prev }; delete n[path]; return n; }); }} className="form-input" />
            {errors[path] && <span className="form-error">{errors[path]}</span>}
        </>
    );

    const next = () => {
        const err = validate(step, data);
        if (Object.keys(err).length) { setErrors(err); return; }
        setStep(s => s + 1);
    };

    const submit = async () => {
        const err = validate(step, data);
        if (Object.keys(err).length) { setErrors(err); return; }
        setSub(true);
        try {
            const payload = {
                ...data,
                amount: { ...data.amount, claimed_amount: Number(data.amount.claimed_amount) },
                medical_info: data.claim_type === 'health' ? {
                    ...data.medical_info,
                    diagnosis_codes: data.medical_info.diagnosis_codes.split(/[\s,]+/).filter(Boolean),
                } : undefined,
            };
            const res = await submitClaim(payload);
            setResult(res);
            addNotification('Claim submitted successfully!', 'success');
        } catch (e) {
            addNotification('Submission failed: ' + e.message, 'error');
        } finally { setSub(false); }
    };

    // Step indicator
    function StepIndicator() {
        return (
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '2rem', gap: 0 }}>
                {STEPS.map((s, i) => {
                    const done = i < step, active = i === step;
                    return (
                        <div key={i} style={{ display: 'flex', alignItems: 'center', flex: i < STEPS.length - 1 ? 1 : 'none' }}>
                            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.375rem', flexShrink: 0 }}>
                                <div style={{
                                    width: 32, height: 32, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: '0.8125rem', transition: 'all 0.3s',
                                    background: done ? '#10b981' : active ? '#6366f1' : 'rgba(255,255,255,0.06)',
                                    border: 'none', color: done || active ? '#fff' : 'var(--text-muted)',
                                }}>
                                    {done ? <CheckCircle size={16} /> : i + 1}
                                </div>
                                <span style={{ fontSize: '0.7rem', fontWeight: 600, color: active ? '#818cf8' : done ? '#10b981' : 'var(--text-muted)', whiteSpace: 'nowrap' }}>{s}</span>
                            </div>
                            {i < STEPS.length - 1 && (
                                <div style={{ flex: 1, height: 2, background: i < step ? '#10b981' : 'var(--border)', margin: '0 0.5rem', marginBottom: '1.1rem', transition: 'background 0.3s' }} />
                            )}
                        </div>
                    );
                })}
            </div>
        );
    }

    // Success screen
    if (result) return (
        <div style={{ maxWidth: 560, margin: '3rem auto', textAlign: 'center' }} className="animate-scale">
            <div className="portal-glass" style={{ padding: '3rem 2.5rem' }}>
                <div style={{ width: 72, height: 72, borderRadius: '50%', background: 'rgba(16,185,129,0.12)', border: '2px solid #10b981', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1.5rem' }}>
                    <CheckCircle size={36} color="#10b981" />
                </div>
                <h2 style={{ marginBottom: '0.5rem' }}>Claim Submitted!</h2>
                <p style={{ marginBottom: '0.375rem' }}>
                    Your claim number is <strong style={{ color: '#818cf8', fontFamily: 'monospace', fontSize: '1rem' }}>{result.metadata?.claim_number}</strong>
                </p>
                <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '2rem' }}>
                    We'll review your claim and send updates to your email. You can track the status from "My Claims".
                </p>

                {/* Next steps */}
                <div style={{ background: 'rgba(99,102,241,0.07)', border: '1px solid rgba(99,102,241,0.2)', borderRadius: 12, padding: '1.25rem', textAlign: 'left', marginBottom: '1.5rem' }}>
                    <p style={{ fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.75rem', fontSize: '0.875rem' }}>📋 Next Steps</p>
                    {(result.next_steps || [
                        'Claim submitted successfully',
                        'Upload any supporting documents',
                        'Track your status from My Claims',
                        'Expect processing within 24–48 hours',
                    ]).map((s, i) => (
                        <div key={i} style={{ display: 'flex', gap: '0.625rem', padding: '0.3rem 0', fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
                            <span style={{ color: '#10b981', fontWeight: 700 }}>{i + 1}.</span> {s}
                        </div>
                    ))}
                </div>

                <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center' }}>
                    <button className="btn btn-secondary" onClick={() => nav('/portal')}>My Claims</button>
                    <button className="btn btn-primary" style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }} onClick={() => nav('/portal/upload')}>
                        <UploadCloud size={14} /> Upload Documents
                    </button>
                </div>
            </div>
        </div>
    );

    return (
        <div className="animate-fade" style={{ maxWidth: 660, margin: '0 auto' }}>
            <div style={{ marginBottom: '1.75rem' }}>
                <h1 style={{ marginBottom: '0.25rem' }}>Submit a Claim</h1>
                <p>Tell us about your claim and we'll handle the rest</p>
            </div>

            <div className="portal-glass" style={{ padding: '2rem 2.25rem' }}>
                <StepIndicator />

                {/* Step 0: Your Details */}
                {step === 0 && (
                    <div className="animate-fade" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        <div className="form-group">
                            <label className="form-label">Insurance Type *</label>
                            <select value={data.claim_type} onChange={e => setData(p => deepSet(p, 'claim_type', e.target.value))} className="form-select">
                                {[['health', '🏥 Health Insurance'], ['auto', '🚗 Auto Insurance'], ['property', '🏠 Property Insurance'], ['life', '💼 Life Insurance']].map(([v, l]) => (
                                    <option key={v} value={v}>{l}</option>
                                ))}
                            </select>
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                            <div className="form-group"><label className="form-label">First Name *</label>{inp('personal_info.first_name', 'John')}</div>
                            <div className="form-group"><label className="form-label">Last Name *</label>{inp('personal_info.last_name', 'Doe')}</div>
                            <div className="form-group"><label className="form-label">Email Address *</label>{inp('personal_info.email', 'you@example.com', 'email')}</div>
                            <div className="form-group"><label className="form-label">Phone Number *</label>{inp('personal_info.phone', '+91 98765 43210', 'tel')}</div>
                        </div>
                        <div className="form-group"><label className="form-label">Address</label>{inp('personal_info.address', '123 Main St, City, State')}</div>
                    </div>
                )}

                {/* Step 1: Incident */}
                {step === 1 && (
                    <div className="animate-fade" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                            <div className="form-group"><label className="form-label">Policy Number *</label>{inp('policy_info.policy_number', 'AB1234567')}</div>
                            <div className="form-group"><label className="form-label">Coverage Type</label>{inp('policy_info.coverage_type', 'e.g. Comprehensive')}</div>
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                            <div className="form-group"><label className="form-label">Incident Date *</label>{inp('incident_info.incident_date', '', 'date')}</div>
                            <div className="form-group"><label className="form-label">Location</label>{inp('incident_info.incident_location', 'City, State')}</div>
                        </div>
                        <div className="form-group">
                            <label className="form-label">Describe what happened *</label>
                            <textarea
                                value={data.incident_info.description}
                                onChange={e => { setData(p => deepSet(p, 'incident_info.description', e.target.value)); setErrors(prev => { const n = { ...prev }; delete n['incident_info.description']; return n; }); }}
                                placeholder="Please describe the incident in detail. Include dates, locations, and what was damaged or lost…"
                                className="form-textarea"
                                style={{ minHeight: 120 }}
                            />
                            {errors['incident_info.description'] && <span className="form-error">{errors['incident_info.description']}</span>}
                        </div>
                    </div>
                )}

                {/* Step 2: Amount */}
                {step === 2 && (
                    <div className="animate-fade" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                        <div className="portal-glass" style={{ padding: '1.25rem' }}>
                            <p style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>You're almost done! 🎉</p>
                            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Enter the total amount you're claiming. You can upload supporting documents (bills, invoices) after submission.</p>
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1rem' }}>
                            <div className="form-group">
                                <label className="form-label">Total Claimed Amount *</label>
                                <input type="number" min="0" step="0.01" placeholder="0.00" value={data.amount.claimed_amount} onChange={e => { setData(p => deepSet(p, 'amount.claimed_amount', e.target.value)); setErrors(prev => { const n = { ...prev }; delete n['amount.claimed_amount']; return n; }); }} className="form-input" style={{ fontSize: '1.375rem', fontWeight: 700 }} />
                                {errors['amount.claimed_amount'] && <span className="form-error">{errors['amount.claimed_amount']}</span>}
                            </div>
                            <div className="form-group">
                                <label className="form-label">Currency</label>
                                <select value={data.amount.currency} onChange={e => setData(p => deepSet(p, 'amount.currency', e.target.value))} className="form-select">
                                    {['USD', 'EUR', 'GBP', 'INR'].map(c => <option key={c} value={c}>{c}</option>)}
                                </select>
                            </div>
                        </div>
                        {data.claim_type === 'health' && (
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                                <div className="form-group"><label className="form-label">Doctor / Hospital Name</label>{inp('medical_info.provider_name', 'Dr. Smith / City Hospital')}</div>
                                <div className="form-group"><label className="form-label">Treatment Date</label>{inp('medical_info.treatment_date', '', 'date')}</div>
                            </div>
                        )}
                        <div className="form-group">
                            <label className="form-label">Any additional information?</label>
                            <textarea value={data.additional_notes} onChange={e => setData(p => deepSet(p, 'additional_notes', e.target.value))} placeholder="Anything else you'd like us to know about your claim…" className="form-textarea" style={{ minHeight: 80 }} />
                        </div>
                    </div>
                )}

                {/* Nav buttons */}
                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '2rem', paddingTop: '1.25rem', borderTop: '1px solid var(--border)' }}>
                    <button className="btn btn-secondary" onClick={() => step === 0 ? nav('/portal') : setStep(s => s - 1)} disabled={submitting}>
                        <ChevronLeft size={15} />{step === 0 ? 'Cancel' : 'Back'}
                    </button>
                    {step < STEPS.length - 1
                        ? <button className="btn btn-primary" style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }} onClick={next}>Continue <ChevronRight size={15} /></button>
                        : <button className="btn btn-primary btn-lg" style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }} onClick={submit} disabled={submitting}>
                            {submitting ? <><Loader size={15} style={{ animation: 'spin 1s linear infinite' }} /> Submitting…</> : <>Submit Claim <CheckCircle size={15} /></>}
                        </button>
                    }
                </div>
            </div>
        </div>
    );
}
