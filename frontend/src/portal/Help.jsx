// Help & FAQ page for customer portal
import { useState } from 'react';
import { ChevronDown, ChevronUp, Phone, Mail, MessageCircle } from 'lucide-react';

const FAQS = [
    { q: 'How long does it take to process my claim?', a: 'Most claims are processed within 24–48 hours after all required documents are received. Complex claims requiring adjuster review may take up to 7 business days.' },
    { q: 'What documents do I need to submit?', a: 'It depends on your claim type. For health claims: medical records, hospital bills, and discharge summaries. For auto: police report and repair estimate. For property: photos, repair quotes, and proof of ownership.' },
    { q: 'How do I know if more documents are needed?', a: 'If your claim requires additional documents, its status will change to "Docs Needed" and you\'ll receive an email notification. You can also check your claim status anytime on the My Claims page.' },
    { q: 'Can I submit multiple claims?', a: 'Yes, you can submit as many claims as needed. Each claim gets its own tracking number and is processed independently.' },
    { q: 'When will I receive payment after approval?', a: 'Payment is typically disbursed within 3–5 business days after your claim is approved. The amount will be transferred to your registered bank account.' },
    { q: 'Can I edit my claim after submission?', a: 'You cannot change claim details after submission, but you may upload additional supporting documents at any time using the Upload Documents page.' },
    { q: 'What does "Under Review" mean?', a: 'This means a claims adjuster has picked up your claim and is actively reviewing the details and documentation to make a determination.' },
    { q: 'How do I appeal a rejected claim?', a: 'Contact our support team within 30 days of the rejection decision. We will initiate an appeal process and assign a senior adjuster to review your case.' },
];

function FaqItem({ q, a }) {
    const [open, setOpen] = useState(false);
    return (
        <div style={{ borderBottom: '1px solid var(--portal-border)' }}>
            <button
                onClick={() => setOpen(o => !o)}
                style={{ width: '100%', background: 'none', border: 'none', cursor: 'pointer', padding: '1.125rem 0', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '1rem', textAlign: 'left' }}
            >
                <span style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.9375rem', flex: 1 }}>{q}</span>
                {open ? <ChevronUp size={16} color="#818cf8" /> : <ChevronDown size={16} color="var(--text-muted)" />}
            </button>
            {open && (
                <p className="animate-fade" style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', lineHeight: 1.7, paddingBottom: '1.125rem', margin: 0 }}>{a}</p>
            )}
        </div>
    );
}

export default function Help() {
    return (
        <div className="animate-fade" style={{ display: 'flex', flexDirection: 'column', gap: '2rem', maxWidth: 760, margin: '0 auto' }}>
            <div>
                <h1 style={{ marginBottom: '0.25rem' }}>Help & FAQ</h1>
                <p>Answers to the most common questions about your claims</p>
            </div>

            {/* FAQ */}
            <div className="portal-glass" style={{ padding: '1.5rem 2rem' }}>
                <h3 style={{ marginBottom: '0.5rem' }}>Frequently Asked Questions</h3>
                <div style={{ marginTop: '0.75rem' }}>
                    {FAQS.map((f, i) => <FaqItem key={i} q={f.q} a={f.a} />)}
                </div>
            </div>

            {/* Contact */}
            <div>
                <h3 style={{ marginBottom: '1rem' }}>Still need help?</h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px,1fr))', gap: '1rem' }}>
                    {[
                        { icon: Phone, label: 'Phone Support', detail: '1-800-CLAIMS-1', sub: 'Mon–Fri, 9am–6pm', color: '#10b981' },
                        { icon: Mail, label: 'Email Support', detail: 'claims@portal.io', sub: 'Response within 24h', color: '#818cf8' },
                        { icon: MessageCircle, label: 'Live Chat', detail: 'Chat with an agent', sub: 'Available now', color: '#f59e0b' },
                    ].map(({ icon: Icon, label, detail, sub, color }) => (
                        <div key={label} className="portal-glass portal-card" style={{ padding: '1.5rem', textAlign: 'center', cursor: 'pointer' }}>
                            <div style={{ background: `${color}18`, border: `1px solid ${color}30`, borderRadius: 12, width: 48, height: 48, display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 0.875rem' }}>
                                <Icon size={20} color={color} />
                            </div>
                            <p style={{ fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>{label}</p>
                            <p style={{ fontSize: '0.875rem', color, fontWeight: 600, marginBottom: '0.2rem' }}>{detail}</p>
                            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{sub}</p>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
