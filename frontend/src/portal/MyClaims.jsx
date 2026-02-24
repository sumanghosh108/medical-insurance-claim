// My Claims — customer's personal claim tracker
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { PlusCircle, Clock, FileText, ChevronRight, AlertCircle, CheckCircle, XCircle, Loader } from 'lucide-react';
import { fetchClaims } from '../api/claims';

const STATUS_CONFIG = {
    submitted: { color: '#94a3b8', bg: 'rgba(148,163,184,0.12)', icon: Clock, label: 'Submitted' },
    processing: { color: '#38bdf8', bg: 'rgba(56,189,248,0.12)', icon: Loader, label: 'Processing' },
    under_review: { color: '#fbbf24', bg: 'rgba(251,191,36,0.12)', icon: Clock, label: 'Under Review' },
    approved: { color: '#34d399', bg: 'rgba(52,211,153,0.12)', icon: CheckCircle, label: 'Approved ✓' },
    rejected: { color: '#f87171', bg: 'rgba(248,113,113,0.12)', icon: XCircle, label: 'Rejected' },
    pending_documents: { color: '#a78bfa', bg: 'rgba(167,139,250,0.12)', icon: AlertCircle, label: 'Docs Needed' },
    paid: { color: '#34d399', bg: 'rgba(52,211,153,0.2)', icon: CheckCircle, label: 'Paid ✓' },
    closed: { color: '#64748b', bg: 'rgba(100,116,139,0.12)', icon: FileText, label: 'Closed' },
};

const PIPELINE = ['submitted', 'processing', 'under_review', 'approved', 'paid'];

function MiniTimeline({ status }) {
    const idx = PIPELINE.indexOf(status);
    return (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0', marginTop: '0.875rem' }}>
            {PIPELINE.map((s, i) => {
                const done = i < idx || (status === 'paid' && i <= 4);
                const current = i === idx;
                const isPaid = status === 'paid';
                const color = done || isPaid ? '#34d399' : current ? '#818cf8' : 'rgba(255,255,255,0.1)';
                return (
                    <div key={s} style={{ display: 'flex', alignItems: 'center', flex: i < PIPELINE.length - 1 ? 1 : 'none' }}>
                        <div style={{
                            width: 10, height: 10, borderRadius: '50%',
                            background: done || current ? color : 'transparent',
                            border: `2px solid ${color}`,
                            flexShrink: 0, transition: 'all 0.3s',
                        }} />
                        {i < PIPELINE.length - 1 && (
                            <div style={{ flex: 1, height: 2, background: done ? '#34d399' : 'rgba(255,255,255,0.08)', transition: 'background 0.3s' }} />
                        )}
                    </div>
                );
            })}
        </div>
    );
}

function fmtAmt(n) { return n != null ? `$${Number(n).toLocaleString()}` : '—'; }
function fmtDate(s) { return s ? new Date(s).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }) : '—'; }

export default function MyClaims() {
    const nav = useNavigate();
    const [claims, setClaims] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => { fetchClaims().then(r => setClaims(r.claims)).finally(() => setLoading(false)); }, []);

    const pending_docs = claims.filter(c => c.metadata.status === 'pending_documents');
    const active = claims.filter(c => !['paid', 'closed', 'rejected'].includes(c.metadata.status));
    const completed = claims.filter(c => ['paid', 'closed', 'rejected'].includes(c.metadata.status));

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }} className="animate-fade">
            {/* Welcome banner */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
                <div>
                    <h1 style={{ marginBottom: '0.25rem' }}>My Claims</h1>
                    <p>Track all your submitted claims and their processing status</p>
                </div>
                <button className="btn btn-primary" onClick={() => nav('/portal/submit')}>
                    <PlusCircle size={16} /> New Claim
                </button>
            </div>

            {/* Pending-documents alert */}
            {pending_docs.length > 0 && (
                <div className="portal-alert portal-alert-warning" style={{ alignItems: 'flex-start' }}>
                    <AlertCircle size={20} color="var(--portal-warning)" style={{ flexShrink: 0, marginTop: 2 }} />
                    <div>
                        <p style={{ fontWeight: 700, color: 'var(--portal-warning)', marginBottom: '0.25rem' }}>
                            Action Required — {pending_docs.length} claim{pending_docs.length > 1 ? 's' : ''} need{pending_docs.length === 1 ? 's' : ''} more documents
                        </p>
                        <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                            Please upload the requested supporting documents to continue processing.{' '}
                            <button onClick={() => nav('/portal/upload')} style={{ background: 'none', border: 'none', color: '#f59e0b', cursor: 'pointer', fontWeight: 700, padding: 0, fontSize: 'inherit' }}>
                                Upload now →
                            </button>
                        </p>
                    </div>
                </div>
            )}

            {loading ? (
                <div style={{ display: 'grid', gap: '1rem' }}>
                    {[...Array(3)].map((_, i) => <div key={i} className="skeleton" style={{ height: 140 }} />)}
                </div>
            ) : claims.length === 0 ? (
                <div className="portal-glass" style={{ padding: '4rem 2rem', textAlign: 'center' }}>
                    <FileText size={48} color="var(--text-muted)" style={{ margin: '0 auto 1rem' }} />
                    <h3 style={{ marginBottom: '0.5rem' }}>No claims yet</h3>
                    <p style={{ marginBottom: '1.5rem' }}>Submit your first insurance claim to get started</p>
                    <button className="btn btn-primary" onClick={() => nav('/portal/submit')}>Submit a Claim</button>
                </div>
            ) : (
                <>
                    {/* Active claims */}
                    {active.length > 0 && (
                        <div>
                            <h3 style={{ marginBottom: '1rem', fontSize: '0.875rem', textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-muted)' }}>Active Claims ({active.length})</h3>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                                {active.map(c => <ClaimCard key={c.metadata.claim_id} claim={c} nav={nav} />)}
                            </div>
                        </div>
                    )}

                    {/* Completed claims */}
                    {completed.length > 0 && (
                        <div>
                            <h3 style={{ marginBottom: '1rem', fontSize: '0.875rem', textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-muted)' }}>Completed / Closed ({completed.length})</h3>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                                {completed.map(c => <ClaimCard key={c.metadata.claim_id} claim={c} nav={nav} />)}
                            </div>
                        </div>
                    )}
                </>
            )}
        </div>
    );
}

function ClaimCard({ claim, nav }) {
    const m = claim.metadata;
    const cfg = STATUS_CONFIG[m.status] || STATUS_CONFIG.submitted;
    const Icon = cfg.icon;
    const data = claim.claim_data;
    const isActionable = m.status === 'pending_documents';

    return (
        <div
            className="portal-glass portal-card"
            onClick={() => nav(`/portal/status/${m.claim_id}`)}
            style={{ padding: '1.5rem', cursor: 'pointer' }}
        >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem' }}>
                {/* Left */}
                <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.375rem', flexWrap: 'wrap' }}>
                        <span style={{ fontWeight: 800, color: 'var(--text-primary)', fontFamily: 'monospace', fontSize: '1rem' }}>{m.claim_number}</span>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'capitalize' }}>{data?.claim_type} Insurance</span>
                    </div>
                    <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 420 }}>
                        {data?.incident_info?.description || 'No description provided'}
                    </p>
                    <MiniTimeline status={m.status} />
                </div>

                {/* Right */}
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.5rem', flexShrink: 0 }}>
                    <span className="portal-badge" style={{ background: cfg.bg, color: cfg.color, border: `1px solid ${cfg.color}40` }}>
                        <Icon size={11} /> {cfg.label}
                    </span>
                    <span style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: '1.125rem' }}>{fmtAmt(data?.amount?.claimed_amount)}</span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{fmtDate(m.created_at)}</span>
                </div>
            </div>

            {isActionable && (
                <div style={{ marginTop: '0.875rem', padding: '0.625rem 0.875rem', background: 'rgba(167,139,250,0.08)', border: '1px solid rgba(167,139,250,0.25)', borderRadius: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.8125rem', color: '#a78bfa', fontWeight: 600 }}>📎 Additional documents required</span>
                    <ChevronRight size={14} color="#a78bfa" />
                </div>
            )}
        </div>
    );
}
