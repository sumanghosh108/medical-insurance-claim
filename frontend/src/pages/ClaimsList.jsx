// Claims List page — filterable, searchable, paginated
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Filter, Eye, RefreshCw } from 'lucide-react';
import StatusBadge from '../components/StatusBadge';
import { fetchClaims } from '../api/claims';

const STATUSES = ['', 'submitted', 'processing', 'under_review', 'approved', 'rejected', 'pending_documents', 'paid', 'closed'];
const TYPES = ['', 'health', 'auto', 'property', 'life'];

function fmt(n) { return n != null ? `$${Number(n).toLocaleString()}` : '—'; }
function fmtDate(s) { return s ? new Date(s).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }) : '—'; }

export default function ClaimsList() {
    const nav = useNavigate();
    const [claims, setClaims] = useState([]);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');
    const [status, setStatus] = useState('');
    const [type, setType] = useState('');
    const [debouncedSearch, setDb] = useState('');

    useEffect(() => {
        const t = setTimeout(() => setDb(search), 300);
        return () => clearTimeout(t);
    }, [search]);

    const load = () => {
        setLoading(true);
        fetchClaims({ status: status || undefined, claim_type: type || undefined, search: debouncedSearch || undefined })
            .then(r => { setClaims(r.claims); setTotal(r.total_count); })
            .finally(() => setLoading(false));
    };

    useEffect(load, [status, type, debouncedSearch]);

    return (
        <div className="animate-fade" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                    <h1>Claims</h1>
                    <p>{total} total claims</p>
                </div>
                <button className="btn btn-primary" onClick={() => nav('/claims/new')}>+ Submit Claim</button>
            </div>

            {/* Filters */}
            <div className="glass" style={{ padding: '1rem 1.25rem', display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'center' }}>
                <div style={{ flex: '1 1 200px', display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(10,20,45,0.6)', border: '1px solid var(--border)', borderRadius: 8, padding: '0 0.75rem' }}>
                    <Search size={14} color="var(--text-muted)" />
                    <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search by number or name…" style={{ background: 'transparent', border: 'none', outline: 'none', color: 'var(--text-primary)', fontSize: '0.875rem', flex: 1, padding: '0.5rem 0' }} />
                </div>
                <select value={status} onChange={e => setStatus(e.target.value)} className="form-select" style={{ flex: '0 1 160px', padding: '0.5rem 2.5rem 0.5rem 0.75rem' }}>
                    {STATUSES.map(s => <option key={s} value={s}>{s ? s.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) : 'All Statuses'}</option>)}
                </select>
                <select value={type} onChange={e => setType(e.target.value)} className="form-select" style={{ flex: '0 1 140px', padding: '0.5rem 2.5rem 0.5rem 0.75rem' }}>
                    {TYPES.map(t => <option key={t} value={t}>{t ? t.charAt(0).toUpperCase() + t.slice(1) : 'All Types'}</option>)}
                </select>
                <button className="btn btn-ghost btn-icon" onClick={load} title="Refresh">
                    <RefreshCw size={15} color="var(--text-secondary)" style={loading ? { animation: 'spin 1s linear infinite' } : {}} />
                </button>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)', fontSize: '0.8125rem' }}>
                    <Filter size={13} /> {claims.length} results
                </div>
            </div>

            {/* Table */}
            <div className="glass" style={{ overflow: 'hidden' }}>
                <div className="table-wrap">
                    <table>
                        <thead>
                            <tr>
                                <th>Claim #</th>
                                <th>Claimant</th>
                                <th>Type</th>
                                <th>Amount</th>
                                <th>Status</th>
                                <th>Priority</th>
                                <th>Submitted</th>
                                <th>Fraud Risk</th>
                                <th style={{ width: 60 }}></th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading
                                ? [...Array(6)].map((_, i) => (
                                    <tr key={i}>
                                        {[...Array(9)].map((_, j) => (
                                            <td key={j}><div className="skeleton" style={{ height: 14, borderRadius: 4, width: j === 0 ? 100 : j === 8 ? 32 : '80%' }} /></td>
                                        ))}
                                    </tr>
                                ))
                                : claims.length === 0
                                    ? <tr><td colSpan={9} style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>No claims match your filters</td></tr>
                                    : claims.map(c => {
                                        const m = c.metadata;
                                        const data = c.claim_data;
                                        const fraud = c.fraud_score;
                                        return (
                                            <tr key={m.claim_id} style={{ cursor: 'pointer' }} onClick={() => nav(`/claims/${m.claim_id}`)}>
                                                <td><span style={{ fontWeight: 700, color: 'var(--primary)', fontFamily: 'monospace', fontSize: '0.8125rem' }}>{m.claim_number}</span></td>
                                                <td><span style={{ fontWeight: 600 }}>{data?.personal_info?.first_name} {data?.personal_info?.last_name}</span></td>
                                                <td><StatusBadge value={data?.claim_type} size="sm" /></td>
                                                <td><span style={{ fontWeight: 600 }}>{fmt(data?.amount?.claimed_amount)}</span></td>
                                                <td><StatusBadge value={m.status} size="sm" /></td>
                                                <td><StatusBadge value={m.priority} size="sm" /></td>
                                                <td style={{ color: 'var(--text-secondary)', fontSize: '0.8125rem' }}>{fmtDate(m.created_at)}</td>
                                                <td>
                                                    {fraud ? (
                                                        <span style={{ fontWeight: 700, fontSize: '0.8125rem', color: fraud.fraud_probability < 0.3 ? 'var(--success)' : fraud.fraud_probability < 0.6 ? 'var(--warning)' : 'var(--danger)' }}>
                                                            {Math.round(fraud.fraud_probability * 100)}%
                                                        </span>
                                                    ) : <span style={{ color: 'var(--text-muted)' }}>—</span>}
                                                </td>
                                                <td>
                                                    <button className="btn btn-ghost btn-icon btn-sm" onClick={e => { e.stopPropagation(); nav(`/claims/${m.claim_id}`); }}>
                                                        <Eye size={14} />
                                                    </button>
                                                </td>
                                            </tr>
                                        );
                                    })
                            }
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
