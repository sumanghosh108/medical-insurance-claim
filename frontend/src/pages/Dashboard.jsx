// Dashboard page
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
    PieChart, Pie, Cell, LineChart, Line, CartesianGrid, Legend,
} from 'recharts';
import { FileText, Clock, Shield, TrendingUp, ArrowRight, DollarSign } from 'lucide-react';
import StatCard from '../components/StatCard';
import StatusBadge from '../components/StatusBadge';
import { fetchStats, fetchMonthlyData, fetchStatusDistribution, fetchFraudTrend, fetchClaims } from '../api/claims';

const fmt = (n) => n >= 1_000_000 ? `$${(n / 1_000_000).toFixed(1)}M` : n >= 1000 ? `$${(n / 1000).toFixed(0)}K` : `$${n}`;

export default function Dashboard() {
    const nav = useNavigate();
    const [stats, setStats] = useState(null);
    const [monthly, setMonthly] = useState([]);
    const [dist, setDist] = useState([]);
    const [fraud, setFraud] = useState([]);
    const [recent, setRecent] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        Promise.all([fetchStats(), fetchMonthlyData(), fetchStatusDistribution(), fetchFraudTrend(), fetchClaims({ limit: 5 })])
            .then(([s, m, d, f, c]) => { setStats(s); setMonthly(m); setDist(d); setFraud(f); setRecent(c.claims.slice(0, 5)); })
            .finally(() => setLoading(false));
    }, []);

    if (loading) return (
        <div style={{ display: 'grid', gap: '1.5rem' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px,1fr))', gap: '1rem' }}>
                {[...Array(4)].map((_, i) => <div key={i} className="skeleton" style={{ height: 120 }} />)}
            </div>
        </div>
    );

    return (
        <div className="animate-fade" style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
            <div>
                <h1 style={{ marginBottom: '0.25rem' }}>Dashboard</h1>
                <p>Insurance claims overview — real-time snapshot</p>
            </div>

            {/* KPI Row */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px,1fr))', gap: '1rem' }}>
                <StatCard title="Total Claims" value={stats.total_claims.toLocaleString()} icon={FileText} trend={12} trendLabel="vs last month" color="var(--primary)" />
                <StatCard title="Pending Review" value={stats.pending_review} icon={Clock} trend={-5} trendLabel="vs last week" color="var(--warning)" />
                <StatCard title="Avg Processing" value={`${stats.avg_processing_hours}h`} icon={TrendingUp} trend={-8} trendLabel="improvement" color="var(--success)" />
                <StatCard title="Fraud Detected" value={stats.fraud_detected} icon={Shield} trend={4} trendLabel="this month" color="var(--danger)" />
                <StatCard title="Approval Rate" value={`${(stats.approval_rate * 100).toFixed(0)}%`} icon={TrendingUp} trend={2} trendLabel="vs last month" color="var(--accent)" />
                <StatCard title="Amount Approved" value={fmt(stats.total_amount_approved)} icon={DollarSign} trend={18} trendLabel="vs last month" color="#34d399" />
            </div>

            {/* Charts Row */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: '1.25rem', alignItems: 'start' }}>
                {/* Bar Chart */}
                <div className="glass" style={{ padding: '1.5rem' }}>
                    <h3 style={{ marginBottom: '1.25rem' }}>Claims by Type — Monthly</h3>
                    <ResponsiveContainer width="100%" height={240}>
                        <BarChart data={monthly} barSize={12} barGap={3}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                            <XAxis dataKey="month" tick={{ fill: '#8fa3cc', fontSize: 12 }} axisLine={false} tickLine={false} />
                            <YAxis tick={{ fill: '#8fa3cc', fontSize: 12 }} axisLine={false} tickLine={false} />
                            <Tooltip contentStyle={{ background: '#0f1932', border: '1px solid rgba(90,130,255,0.3)', borderRadius: 8, color: '#e8edf8' }} />
                            <Legend wrapperStyle={{ fontSize: 12, color: '#8fa3cc' }} />
                            <Bar dataKey="health" fill="#38bdf8" radius={[4, 4, 0, 0]} />
                            <Bar dataKey="auto" fill="#a78bfa" radius={[4, 4, 0, 0]} />
                            <Bar dataKey="property" fill="#fbbf24" radius={[4, 4, 0, 0]} />
                            <Bar dataKey="life" fill="#34d399" radius={[4, 4, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>

                {/* Donut */}
                <div className="glass" style={{ padding: '1.5rem', minWidth: 260 }}>
                    <h3 style={{ marginBottom: '1.25rem' }}>Status Distribution</h3>
                    <ResponsiveContainer width="100%" height={200}>
                        <PieChart>
                            <Pie data={dist} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={55} outerRadius={85} paddingAngle={3}>
                                {dist.map((d, i) => <Cell key={i} fill={d.color} />)}
                            </Pie>
                            <Tooltip contentStyle={{ background: '#0f1932', border: '1px solid rgba(90,130,255,0.3)', borderRadius: 8, color: '#e8edf8' }} formatter={(v, n) => [v, n]} />
                        </PieChart>
                    </ResponsiveContainer>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', marginTop: '0.75rem' }}>
                        {dist.slice(0, 4).map(d => (
                            <div key={d.name} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.75rem' }}>
                                <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--text-secondary)' }}>
                                    <span style={{ width: 8, height: 8, borderRadius: '50%', background: d.color, flexShrink: 0 }} />
                                    {d.name}
                                </span>
                                <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{d.value}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Fraud trend + Recent Claims */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.4fr', gap: '1.25rem' }}>
                {/* Fraud trend */}
                <div className="glass" style={{ padding: '1.5rem' }}>
                    <h3 style={{ marginBottom: '1.25rem' }}>Fraud Detections — Trend</h3>
                    <ResponsiveContainer width="100%" height={180}>
                        <LineChart data={fraud}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                            <XAxis dataKey="month" tick={{ fill: '#8fa3cc', fontSize: 12 }} axisLine={false} tickLine={false} />
                            <YAxis tick={{ fill: '#8fa3cc', fontSize: 12 }} axisLine={false} tickLine={false} />
                            <Tooltip contentStyle={{ background: '#0f1932', border: '1px solid rgba(90,130,255,0.3)', borderRadius: 8, color: '#e8edf8' }} />
                            <Line type="monotone" dataKey="score" stroke="#f87171" strokeWidth={2.5} dot={{ fill: '#f87171', r: 4 }} activeDot={{ r: 6 }} />
                        </LineChart>
                    </ResponsiveContainer>
                </div>

                {/* Recent Claims */}
                <div className="glass" style={{ padding: '1.5rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                        <h3>Recent Claims</h3>
                        <button className="btn btn-ghost btn-sm" onClick={() => nav('/claims')} style={{ color: 'var(--primary)', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                            View all <ArrowRight size={13} />
                        </button>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0' }}>
                        {recent.map((c, i) => (
                            <div key={c.metadata.claim_id}
                                onClick={() => nav(`/claims/${c.metadata.claim_id}`)}
                                style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem 0', cursor: 'pointer', transition: 'var(--transition)', borderBottom: i < recent.length - 1 ? '1px solid var(--border)' : 'none' }}
                                onMouseEnter={e => e.currentTarget.style.paddingLeft = '0.5rem'}
                                onMouseLeave={e => e.currentTarget.style.paddingLeft = '0'}
                            >
                                <div>
                                    <p style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.875rem', margin: 0 }}>{c.metadata.claim_number}</p>
                                    <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', margin: 0 }}>{c.claim_data?.personal_info?.first_name} {c.claim_data?.personal_info?.last_name} · {c.claim_data?.claim_type}</p>
                                </div>
                                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.25rem' }}>
                                    <StatusBadge value={c.metadata.status} size="sm" />
                                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>${c.claim_data?.amount?.claimed_amount?.toLocaleString()}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}
