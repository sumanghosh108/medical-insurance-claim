// Customer Claim Status Tracker — detailed view of a single claim
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
    ArrowLeft, CheckCircle, Clock, Loader, XCircle, AlertCircle,
    FileText, UploadCloud, DollarSign, Phone,
} from 'lucide-react';
import { fetchClaim } from '../api/claims';

const STEPS = [
    { key: 'submitted', label: 'Claim Submitted', desc: 'We received your claim and are reviewing the details.' },
    { key: 'processing', label: 'Document Processing', desc: 'We are extracting and verifying your supporting documents.' },
    { key: 'under_review', label: 'Adjuster Review', desc: 'A claims adjuster is reviewing your case.' },
    { key: 'approved', label: 'Claim Approved', desc: 'Your claim has been approved for payment.' },
    { key: 'paid', label: 'Payment Disbursed', desc: 'Your payout has been transferred.' },
];

function getState(stepKey, currentStatus) {
    if (currentStatus === 'rejected') {
        if (stepKey === 'submitted' || stepKey === 'processing') return 'done';
        if (stepKey === 'under_review') return 'error';
        return 'locked';
    }
    if (currentStatus === 'pending_documents' && stepKey === 'processing') return 'warning';
    const stepIdx = STEPS.findIndex(s => s.key === stepKey);
    const currentIdx = STEPS.findIndex(s => s.key === currentStatus);
    if (stepIdx < currentIdx) return 'done';
    if (stepIdx === currentIdx) return 'current';
    return 'locked';
}

function StepIcon({ state }) {
    if (state === 'done') return <CheckCircle size={18} />;
    if (state === 'current') return <Clock size={18} />;
    if (state === 'warning') return <AlertCircle size={18} />;
    if (state === 'error') return <XCircle size={18} />;
    return <div style={{ width: 10, height: 10, borderRadius: '50%', background: 'currentColor', opacity: 0.3 }} />;
}

const STATE_COLOR = { done: '#10b981', current: '#818cf8', warning: '#f59e0b', error: '#ef4444', locked: '#334155' };

function fmtAmt(n) { return n != null ? `$${Number(n).toLocaleString(undefined, { minimumFractionDigits: 2 })}` : '—'; }
function fmtDate(s) { return s ? new Date(s).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' }) : '—'; }

export default function ClaimStatus() {
    const { id } = useParams();
    const nav = useNavigate();
    const [claim, setClaim] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchClaim(id).then(setClaim).catch(e => setError(e.message)).finally(() => setLoading(false));
    }, [id]);

    if (loading) return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {[...Array(3)].map((_, i) => <div key={i} className="skeleton" style={{ height: 100 }} />)}
        </div>
    );
    if (error || !claim) return (
        <div className="portal-glass" style={{ padding: '3rem', textAlign: 'center' }}>
            <p style={{ color: 'var(--portal-danger)' }}>Could not load claim. {error}</p>
            <button className="btn btn-secondary" style={{ marginTop: '1rem' }} onClick={() => nav('/portal')}>← Back</button>
        </div>
    );

    const m = claim.metadata;
    const data = claim.claim_data;
    const isPendingDocs = m.status === 'pending_documents';
    const isRejected = m.status === 'rejected';
    const isApproved = ['approved', 'paid'].includes(m.status);

    return (
        <div className="animate-fade" style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem', maxWidth: 780, margin: '0 auto' }}>
            {/* Back + header */}
            <div>
                <button className="btn btn-ghost btn-sm" onClick={() => nav('/portal')} style={{ marginBottom: '0.875rem', color: 'var(--text-muted)' }}>
                    <ArrowLeft size={14} /> My Claims
                </button>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
                    <div>
                        <h1 style={{ fontSize: '1.5rem', marginBottom: '0.25rem' }}>{m.claim_number}</h1>
                        <p style={{ fontSize: '0.875rem' }}>{data?.claim_type?.charAt(0).toUpperCase() + data?.claim_type?.slice(1)} Insurance · Submitted {fmtDate(m.created_at)}</p>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                        <span style={{ fontWeight: 800, fontSize: '1.5rem', color: '#818cf8' }}>{fmtAmt(data?.amount?.claimed_amount)}</span>
                        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Claimed Amount</p>
                    </div>
                </div>
            </div>

            {/* Conditional alert banners */}
            {isPendingDocs && (
                <div className="portal-alert portal-alert-warning">
                    <AlertCircle size={20} color="#f59e0b" style={{ flexShrink: 0 }} />
                    <div>
                        <p style={{ fontWeight: 700, color: '#f59e0b', marginBottom: '0.25rem' }}>Action Required: Documents Needed</p>
                        <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                            Please upload the requested documents to continue processing your claim.{' '}
                            <button onClick={() => nav('/portal/upload')} style={{ background: 'none', border: 'none', color: '#f59e0b', cursor: 'pointer', fontWeight: 700, padding: 0 }}>
                                Upload now →
                            </button>
                        </p>
                    </div>
                </div>
            )}
            {isRejected && (
                <div className="portal-alert portal-alert-danger">
                    <XCircle size={20} color="#ef4444" style={{ flexShrink: 0 }} />
                    <div>
                        <p style={{ fontWeight: 700, color: '#ef4444', marginBottom: '0.25rem' }}>Claim Not Approved</p>
                        <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                            Unfortunately your claim was not approved. Contact our support team to learn more or to appeal this decision.
                        </p>
                    </div>
                </div>
            )}
            {isApproved && (
                <div className="portal-alert portal-alert-success">
                    <CheckCircle size={20} color="#10b981" style={{ flexShrink: 0 }} />
                    <div>
                        <p style={{ fontWeight: 700, color: '#10b981', marginBottom: '0.25rem' }}>
                            {m.status === 'paid' ? '🎉 Payment has been disbursed' : '✅ Claim Approved!'}
                        </p>
                        <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                            {m.status === 'paid' ? `Your payout of ${fmtAmt(data?.amount?.claimed_amount)} has been transferred.` : `Your claim for ${fmtAmt(data?.amount?.claimed_amount)} has been approved. Payment will be processed shortly.`}
                        </p>
                    </div>
                </div>
            )}

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: '1.5rem', alignItems: 'start' }}>
                {/* Pipeline tracker */}
                <div className="portal-glass" style={{ padding: '2rem' }}>
                    <h3 style={{ marginBottom: '1.75rem' }}>Claim Progress</h3>
                    <div className="step-track">
                        {STEPS.map((step, i) => {
                            const state = getState(step.key, m.status);
                            const color = STATE_COLOR[state];
                            const isLast = i === STEPS.length - 1;
                            return (
                                <div key={step.key} className="step-item">
                                    <div className="step-connector">
                                        <div className="step-dot" style={{
                                            background: state !== 'locked' ? `${color}20` : 'transparent',
                                            border: `2px solid ${color}`,
                                            color,
                                            width: 36, height: 36,
                                        }}>
                                            <StepIcon state={state} />
                                        </div>
                                        {!isLast && (
                                            <div className="step-line" style={{
                                                background: state === 'done' ? '#10b981' : 'rgba(255,255,255,0.07)',
                                            }} />
                                        )}
                                    </div>
                                    <div style={{ paddingBottom: isLast ? 0 : '2rem', paddingTop: '0.375rem', flex: 1 }}>
                                        <p style={{ fontWeight: state === 'current' || state === 'warning' ? 700 : 500, color: state === 'locked' ? 'var(--text-muted)' : 'var(--text-primary)', margin: 0, marginBottom: '0.2rem', fontSize: '0.9375rem' }}>
                                            {step.label}
                                        </p>
                                        <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.5 }}>
                                            {state === 'current' ? <span style={{ color }}>{step.desc}</span> : state === 'locked' ? 'Waiting…' : step.desc}
                                        </p>
                                        {state === 'warning' && (
                                            <p style={{ fontSize: '0.8125rem', color: '#f59e0b', fontWeight: 700, marginTop: '0.35rem', margin: 0 }}>
                                                ⚠ Additional documents required
                                            </p>
                                        )}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* Right sidebar */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    {/* Quick actions */}
                    <div className="portal-glass" style={{ padding: '1.25rem' }}>
                        <h4 style={{ marginBottom: '0.875rem', fontSize: '0.875rem' }}>Quick Actions</h4>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                            <button className="btn btn-secondary" style={{ justifyContent: 'flex-start', gap: '0.625rem', width: '100%', fontSize: '0.8125rem' }} onClick={() => nav('/portal/upload')}>
                                <UploadCloud size={14} /> Upload Documents
                            </button>
                            <button className="btn btn-secondary" style={{ justifyContent: 'flex-start', gap: '0.625rem', width: '100%', fontSize: '0.8125rem' }}>
                                <Phone size={14} /> Contact Adjuster
                            </button>
                            <button className="btn btn-secondary" style={{ justifyContent: 'flex-start', gap: '0.625rem', width: '100%', fontSize: '0.8125rem' }}>
                                <FileText size={14} /> Download Claim PDF
                            </button>
                        </div>
                    </div>

                    {/* Claim summary */}
                    <div className="portal-glass" style={{ padding: '1.25rem' }}>
                        <h4 style={{ marginBottom: '0.875rem', fontSize: '0.875rem' }}>Claim Summary</h4>
                        {[
                            { label: 'Type', value: data?.claim_type },
                            { label: 'Priority', value: m.priority },
                            { label: 'Adjuster', value: m.assigned_to || 'Not yet assigned' },
                            { label: 'Docs Processed', value: claim.processing?.documents_processed ?? '—' },
                        ].map(({ label, value }) => (
                            <div key={label} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.45rem 0', borderBottom: '1px solid rgba(99,102,241,0.07)', fontSize: '0.8125rem' }}>
                                <span style={{ color: 'var(--text-muted)' }}>{label}</span>
                                <span style={{ fontWeight: 600, color: 'var(--text-primary)', textTransform: 'capitalize' }}>{value}</span>
                            </div>
                        ))}
                    </div>

                    {/* Estimated amount if approved */}
                    <div className="portal-glass" style={{ padding: '1.25rem', textAlign: 'center' }}>
                        <DollarSign size={20} color="#818cf8" style={{ margin: '0 auto 0.5rem' }} />
                        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.25rem', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 700 }}>Claimed Amount</p>
                        <p style={{ fontSize: '1.625rem', fontWeight: 800, color: '#818cf8' }}>{fmtAmt(data?.amount?.claimed_amount)}</p>
                        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>{data?.amount?.currency}</p>
                    </div>
                </div>
            </div>
        </div>
    );
}
