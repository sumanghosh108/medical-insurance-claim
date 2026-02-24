// StatusBadge — claim status, priority and type
export default function StatusBadge({ value, type = 'status', size = 'md' }) {
    const cls = `badge badge-${value?.replace(/\s/g, '_').toLowerCase() || 'submitted'}`;
    const labels = {
        submitted: 'Submitted', processing: 'Processing', under_review: 'Under Review',
        approved: 'Approved', rejected: 'Rejected', pending_documents: 'Pending Docs',
        paid: 'Paid', closed: 'Closed',
        low: 'Low', medium: 'Medium', high: 'High', urgent: 'Urgent',
        health: 'Health', auto: 'Auto', property: 'Property', life: 'Life',
    };
    const label = labels[value] || value;
    return (
        <span className={cls} style={size === 'sm' ? { fontSize: '0.7rem', padding: '0.15rem 0.55rem' } : {}}>
            <span className="badge-dot" />
            {label}
        </span>
    );
}
