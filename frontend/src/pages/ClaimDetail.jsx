// Claim Detail page
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Calendar, MapPin, DollarSign, User, FileText, Stethoscope, ShieldAlert } from 'lucide-react';
import StatusBadge from '../components/StatusBadge';
import FraudMeter from '../components/FraudMeter';
import Timeline from '../components/Timeline';
import { fetchClaim } from '../api/claims';

function Section({ title, icon: Icon, children }) {
    return (
        <div className="glass" style={{ padding: '1.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', marginBottom: '1.25rem', paddingBottom: '0.875rem', borderBottom: '1px solid var(--border)' }}>
                {Icon && <Icon size={16} color="var(--primary)" />}
                <h3>{title}</h3>
            </div>
            {children}
        </div>
    );
}

function Row({ label, value }) {
    return (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem', padding: '0.5rem 0', borderBottom: '1px solid rgba(90,130,255,0.06)' }}>
            <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', flexShrink: 0 }}>{label}</span>
            <span style={{ fontSize: '0.875rem', color: 'var(--text-primary)', fontWeight: 500, textAlign: 'right' }}>{value ?? '—'}</span>
        </div>
    );
}

function fmtDate(s) { return s ? new Date(s).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' }) : '—'; }
function fmtAmt(n) { return n != null ? `$${Number(n).toLocaleString(undefined, { minimumFractionDigits: 2 })}` : '—'; }

export default function ClaimDetail() {
    const { id } = useParams();
    const nav = useNavigate();
    const [claim, setClaim] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchClaim(id).then(setClaim).catch(e => setError(e.message)).finally(() => setLoading(false));
    }, [id]);

    if (loading) return (
        <div style={{ display: 'grid', gap: '1rem' }}>
            {[...Array(3)].map((_, i) => <div key={i} className="skeleton" style={{ height: 140 }} />)}
        </div>
    );
    if (error) return (
        <div className="glass" style={{ padding: '3rem', textAlign: 'center' }}>
            <p style={{ color: 'var(--danger)' }}>Error: {error}</p>
            <button className="btn btn-secondary" style={{ marginTop: '1rem' }} onClick={() => nav('/claims')}>← Back to Claims</button>
        </div>
    );

    const m = claim.metadata;
    const data = claim.claim_data;
    const pi = data?.personal_info;
    const po = data?.policy_info;
    const ii = data?.incident_info;
    const mi = data?.medical_info;
    const amt = data?.amount;
    const fraud = claim.fraud_score;
    const valid = claim.validation;
    const proc = claim.processing;

    return (
        <div className="animate-fade" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <button className="btn btn-ghost btn-icon" onClick={() => nav('/claims')}><ArrowLeft size={18} /></button>
                    <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
                            <h1 style={{ fontSize: '1.5rem' }}>{m.claim_number}</h1>
                            <StatusBadge value={m.status} />
                            <StatusBadge value={m.priority} />
                            <StatusBadge value={data?.claim_type} />
                        </div>
                        <p style={{ marginTop: '0.25rem' }}>Submitted {fmtDate(m.created_at)} · ID: <span style={{ fontFamily: 'monospace', fontSize: '0.8125rem' }}>{m.claim_id}</span></p>
                    </div>
                </div>
            </div>

            {/* Main grid */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '1.25rem', alignItems: 'start' }}>
                {/* Left column */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                    {/* Claimant */}
                    <Section title="Personal Information" icon={User}>
                        <Row label="Full Name" value={`${pi?.first_name} ${pi?.last_name}`} />
                        <Row label="Email" value={pi?.email} />
                        <Row label="Date of Birth" value={fmtDate(pi?.date_of_birth)} />
                        <Row label="Address" value={pi?.address} />
                    </Section>

                    {/* Policy */}
                    {po && (
                        <Section title="Policy Information" icon={FileText}>
                            <Row label="Policy Number" value={po.policy_number} />
                            <Row label="Holder Name" value={po.policy_holder_name} />
                            <Row label="Coverage Type" value={po.coverage_type} />
                            <Row label="Effective Date" value={fmtDate(po.effective_date)} />
                            <Row label="Expiry Date" value={fmtDate(po.expiration_date)} />
                        </Section>
                    )}

                    {/* Incident */}
                    {ii && (
                        <Section title="Incident Details" icon={MapPin}>
                            <Row label="Date" value={fmtDate(ii.incident_date)} />
                            <Row label="Location" value={ii.incident_location} />
                            <Row label="Type" value={ii.incident_type} />
                            <Row label="Police Report" value={ii.police_report_number} />
                            <div style={{ marginTop: '0.75rem' }}>
                                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.375rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Description</p>
                                <p style={{ fontSize: '0.875rem', color: 'var(--text-primary)', lineHeight: 1.6 }}>{ii.description}</p>
                            </div>
                        </Section>
                    )}

                    {/* Amount */}
                    <Section title="Claim Amount" icon={DollarSign}>
                        <div style={{ textAlign: 'center', padding: '0.75rem 0 0.5rem' }}>
                            <span style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--primary)' }}>{fmtAmt(amt?.claimed_amount)}</span>
                            <span style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginLeft: '0.5rem' }}>{amt?.currency}</span>
                        </div>
                        {amt?.breakdown && Object.entries(amt.breakdown).map(([k, v]) => (
                            <Row key={k} label={k.replace(/_/g, ' ')} value={fmtAmt(v)} />
                        ))}
                    </Section>

                    {/* Medical */}
                    {mi && (
                        <Section title="Medical Information" icon={Stethoscope}>
                            <Row label="Provider" value={mi.provider_name} />
                            <Row label="NPI" value={mi.provider_npi} />
                            <Row label="Facility" value={mi.facility_name} />
                            <Row label="Treatment Date" value={fmtDate(mi.treatment_date)} />
                            <Row label="ICD-10 Codes" value={mi.diagnosis_codes?.join(', ')} />
                            <Row label="Procedure Codes" value={mi.procedure_codes?.join(', ')} />
                        </Section>
                    )}
                </div>

                {/* Right sidebar */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                    {/* Fraud Score */}
                    {fraud ? (
                        <div className="glass" style={{ padding: '1.5rem', textAlign: 'center' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', justifyContent: 'center', marginBottom: '1rem' }}>
                                <ShieldAlert size={15} color="var(--primary)" />
                                <h4>Fraud Analysis</h4>
                            </div>
                            <FraudMeter probability={fraud.fraud_probability} riskLevel={fraud.risk_level} size={140} />
                            {fraud.contributing_factors?.length > 0 && (
                                <div style={{ marginTop: '1rem', textAlign: 'left' }}>
                                    <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '0.5rem' }}>Factors</p>
                                    {fraud.contributing_factors.map(f => (
                                        <div key={f} style={{ fontSize: '0.8125rem', color: 'var(--warning)', padding: '0.25rem 0', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                                            <span style={{ width: 5, height: 5, borderRadius: '50%', background: 'currentColor', flexShrink: 0 }} />{f.replace(/_/g, ' ')}
                                        </div>
                                    ))}
                                </div>
                            )}
                            <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.75rem' }}>Model v{fraud.model_version}</p>
                        </div>
                    ) : (
                        <div className="glass" style={{ padding: '1.5rem', textAlign: 'center' }}>
                            <ShieldAlert size={24} color="var(--text-muted)" />
                            <p style={{ fontSize: '0.825rem', marginTop: '0.5rem' }}>Fraud analysis pending</p>
                        </div>
                    )}

                    {/* Validation */}
                    {valid && (
                        <div className="glass" style={{ padding: '1.5rem' }}>
                            <h4 style={{ marginBottom: '0.875rem' }}>Validation</h4>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.625rem' }}>
                                <span style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>Score</span>
                                <span style={{ fontWeight: 800, color: valid.validation_score >= 80 ? 'var(--success)' : valid.validation_score >= 60 ? 'var(--warning)' : 'var(--danger)' }}>{valid.validation_score.toFixed(1)}/100</span>
                            </div>
                            <div className="progress-track">
                                <div className="progress-fill" style={{ width: `${valid.validation_score}%`, background: valid.validation_score >= 80 ? 'linear-gradient(90deg,#34d399,#6ee7b7)' : valid.validation_score >= 60 ? 'linear-gradient(90deg,#fbbf24,#fde68a)' : 'linear-gradient(90deg,#f87171,#fca5a5)' }} />
                            </div>
                            {valid.warnings?.length > 0 && valid.warnings.map(w => (
                                <div key={w.code} style={{ marginTop: '0.5rem', padding: '0.5rem 0.625rem', background: 'rgba(251,191,36,0.08)', border: '1px solid rgba(251,191,36,0.2)', borderRadius: 6, fontSize: '0.75rem', color: 'var(--warning)' }}>{w.message}</div>
                            ))}
                            {valid.errors?.length > 0 && valid.errors.map(e => (
                                <div key={e.code} style={{ marginTop: '0.5rem', padding: '0.5rem 0.625rem', background: 'rgba(248,113,113,0.08)', border: '1px solid rgba(248,113,113,0.2)', borderRadius: 6, fontSize: '0.75rem', color: 'var(--danger)' }}>{e.message}</div>
                            ))}
                        </div>
                    )}

                    {/* Processing */}
                    {proc && (
                        <div className="glass" style={{ padding: '1.5rem' }}>
                            <h4 style={{ marginBottom: '0.875rem' }}>Processing</h4>
                            <Row label="Docs Processed" value={proc.documents_processed} />
                            <Row label="Extraction Confidence" value={proc.text_extraction_confidence ? `${proc.text_extraction_confidence.toFixed(1)}%` : null} />
                            <Row label="Entities Extracted" value={proc.entities_extracted} />
                        </div>
                    )}

                    {/* Timeline */}
                    <div className="glass" style={{ padding: '1.5rem' }}>
                        <h4 style={{ marginBottom: '1rem' }}>Processing Timeline</h4>
                        <Timeline status={m.status} />
                    </div>

                    {/* Assignment */}
                    <div className="glass" style={{ padding: '1.5rem' }}>
                        <h4 style={{ marginBottom: '0.875rem' }}>Assignment</h4>
                        <Row label="Created By" value={m.created_by} />
                        <Row label="Assigned To" value={m.assigned_to} />
                        <Row label="Last Updated" value={fmtDate(m.updated_at)} />
                    </div>
                </div>
            </div>
        </div>
    );
}
