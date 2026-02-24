// Timeline — vertical status steps
import { CheckCircle, Clock, AlertCircle, XCircle } from 'lucide-react';

const STATUS_ORDER = ['submitted', 'processing', 'under_review', 'approved', 'paid'];

function getStepState(stepStatus, currentStatus) {
    const si = STATUS_ORDER.indexOf(stepStatus);
    const ci = STATUS_ORDER.indexOf(currentStatus);
    if (currentStatus === 'rejected') return si === 0 ? 'done' : si === 1 ? 'done' : 'error';
    if (si < ci) return 'done';
    if (si === ci) return 'current';
    return 'pending';
}

const STEP_LABELS = {
    submitted: 'Claim Submitted',
    processing: 'Document Processing',
    under_review: 'Adjuster Review',
    approved: 'Claim Approved',
    paid: 'Payment Disbursed',
};

export default function Timeline({ status }) {
    const steps = status === 'rejected'
        ? ['submitted', 'processing', 'rejected']
        : STATUS_ORDER;

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
            {steps.map((step, i) => {
                const state = step === 'rejected' ? 'error' : getStepState(step, status);
                const isLast = i === steps.length - 1;
                const Icon = state === 'done' ? CheckCircle : state === 'current' ? Clock : state === 'error' ? XCircle : AlertCircle;
                const color = state === 'done' ? 'var(--success)' : state === 'current' ? 'var(--primary)' : state === 'error' ? 'var(--danger)' : 'var(--text-muted)';

                return (
                    <div key={step} style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>
                        {/* icon + line */}
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flexShrink: 0 }}>
                            <div style={{ padding: '2px', borderRadius: '50%', background: state !== 'pending' ? `${color}20` : 'transparent', border: `2px solid ${color}`, display: 'flex' }}>
                                <Icon size={16} color={color} />
                            </div>
                            {!isLast && <div style={{ width: 2, flex: 1, minHeight: 28, background: `linear-gradient(180deg, ${color}40, rgba(255,255,255,0.05))`, marginTop: 4 }} />}
                        </div>
                        {/* label */}
                        <div style={{ paddingBottom: isLast ? 0 : '1.25rem', paddingTop: '1px' }}>
                            <p style={{ fontWeight: state === 'current' ? 700 : 500, color: state === 'pending' ? 'var(--text-muted)' : 'var(--text-primary)', fontSize: '0.875rem', margin: 0, lineHeight: 1.4 }}>
                                {STEP_LABELS[step] || step}
                            </p>
                            {state === 'current' && (
                                <p style={{ fontSize: '0.75rem', color: 'var(--primary)', margin: '0.15rem 0 0', fontWeight: 500 }}>In progress…</p>
                            )}
                        </div>
                    </div>
                );
            })}
        </div>
    );
}
