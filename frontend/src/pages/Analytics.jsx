// Analytics page
import { useEffect, useState } from 'react';
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
    LineChart, Line, PieChart, Pie, Cell, AreaChart, Area,
} from 'recharts';
import { fetchMonthlyData, fetchStatusDistribution, fetchFraudTrend } from '../api/claims';

const TIP_STYLE = { background: '#0f1932', border: '1px solid rgba(90,130,255,0.3)', borderRadius: 8, color: '#e8edf8', fontSize: '0.8125rem' };

const HOSPITAL_DATA = [
    { name: 'City General', claims: 142, amount: 2_800_000 },
    { name: 'Apollo Health', claims: 118, amount: 3_200_000 },
    { name: 'Sunrise Medical', claims: 95, amount: 1_900_000 },
    { name: 'Metro Clinic', claims: 82, amount: 1_400_000 },
    { name: 'Heritage Hospital', claims: 74, amount: 2_100_000 },
];

const AVG_PROC = [
    { month: 'Sep', health: 22, auto: 18, property: 35, life: 45 },
    { month: 'Oct', health: 20, auto: 17, property: 32, life: 42 },
    { month: 'Nov', health: 19, auto: 16, property: 30, life: 40 },
    { month: 'Dec', health: 25, auto: 19, property: 38, life: 50 },
    { month: 'Jan', health: 18, auto: 15, property: 28, life: 38 },
    { month: 'Feb', health: 15, auto: 13, property: 25, life: 35 },
];

function ChartCard({ title, subtitle, children }) {
    return (
        <div className="glass" style={{ padding: '1.5rem' }}>
            <div style={{ marginBottom: '1.25rem' }}>
                <h3>{title}</h3>
                {subtitle && <p style={{ fontSize: '0.8125rem', marginTop: '0.125rem' }}>{subtitle}</p>}
            </div>
            {children}
        </div>
    );
}

export default function Analytics() {
    const [monthly, setMonthly] = useState([]);
    const [dist, setDist] = useState([]);
    const [fraud, setFraud] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        Promise.all([fetchMonthlyData(), fetchStatusDistribution(), fetchFraudTrend()])
            .then(([m, d, f]) => { setMonthly(m); setDist(d); setFraud(f); })
            .finally(() => setLoading(false));
    }, []);

    if (loading) return (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem' }}>
            {[...Array(4)].map((_, i) => <div key={i} className="skeleton" style={{ height: 280 }} />)}
        </div>
    );

    return (
        <div className="animate-fade" style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
            <div>
                <h1>Analytics</h1>
                <p>Claim trends, processing performance, and fraud intelligence</p>
            </div>

            {/* Row 1 */}
            <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: '1.25rem' }}>
                <ChartCard title="Monthly Claim Volume by Type" subtitle="Last 6 months">
                    <ResponsiveContainer width="100%" height={240}>
                        <BarChart data={monthly} barSize={10} barGap={2}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                            <XAxis dataKey="month" tick={{ fill: '#8fa3cc', fontSize: 12 }} axisLine={false} tickLine={false} />
                            <YAxis tick={{ fill: '#8fa3cc', fontSize: 12 }} axisLine={false} tickLine={false} />
                            <Tooltip contentStyle={TIP_STYLE} />
                            <Legend wrapperStyle={{ fontSize: 12, color: '#8fa3cc' }} />
                            <Bar dataKey="health" fill="#38bdf8" radius={[4, 4, 0, 0]} name="Health" />
                            <Bar dataKey="auto" fill="#a78bfa" radius={[4, 4, 0, 0]} name="Auto" />
                            <Bar dataKey="property" fill="#fbbf24" radius={[4, 4, 0, 0]} name="Property" />
                            <Bar dataKey="life" fill="#34d399" radius={[4, 4, 0, 0]} name="Life" />
                        </BarChart>
                    </ResponsiveContainer>
                </ChartCard>

                <ChartCard title="Status Distribution" subtitle="All-time breakdown">
                    <ResponsiveContainer width="100%" height={180}>
                        <PieChart>
                            <Pie data={dist} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} paddingAngle={2}>
                                {dist.map((d, i) => <Cell key={i} fill={d.color} />)}
                            </Pie>
                            <Tooltip contentStyle={TIP_STYLE} />
                        </PieChart>
                    </ResponsiveContainer>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.25rem 0.75rem', marginTop: '0.5rem' }}>
                        {dist.map(d => (
                            <div key={d.name} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem' }}>
                                <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', color: 'var(--text-secondary)' }}>
                                    <span style={{ width: 7, height: 7, borderRadius: '50%', background: d.color, flexShrink: 0 }} />{d.name}
                                </span>
                                <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{d.value}</span>
                            </div>
                        ))}
                    </div>
                </ChartCard>
            </div>

            {/* Row 2 */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem' }}>
                <ChartCard title="Fraud Detection Trend" subtitle="Monthly flagged claims">
                    <ResponsiveContainer width="100%" height={200}>
                        <AreaChart data={fraud}>
                            <defs>
                                <linearGradient id="fraud-grad" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#f87171" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="#f87171" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                            <XAxis dataKey="month" tick={{ fill: '#8fa3cc', fontSize: 12 }} axisLine={false} tickLine={false} />
                            <YAxis tick={{ fill: '#8fa3cc', fontSize: 12 }} axisLine={false} tickLine={false} />
                            <Tooltip contentStyle={TIP_STYLE} />
                            <Area type="monotone" dataKey="score" stroke="#f87171" strokeWidth={2.5} fill="url(#fraud-grad)" name="Fraud Cases" />
                        </AreaChart>
                    </ResponsiveContainer>
                </ChartCard>

                <ChartCard title="Avg Processing Time (hours)" subtitle="By claim type and month">
                    <ResponsiveContainer width="100%" height={200}>
                        <LineChart data={AVG_PROC}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                            <XAxis dataKey="month" tick={{ fill: '#8fa3cc', fontSize: 12 }} axisLine={false} tickLine={false} />
                            <YAxis tick={{ fill: '#8fa3cc', fontSize: 12 }} axisLine={false} tickLine={false} />
                            <Tooltip contentStyle={TIP_STYLE} />
                            <Legend wrapperStyle={{ fontSize: 11, color: '#8fa3cc' }} />
                            <Line type="monotone" dataKey="health" stroke="#38bdf8" strokeWidth={2} dot={false} name="Health" />
                            <Line type="monotone" dataKey="auto" stroke="#a78bfa" strokeWidth={2} dot={false} name="Auto" />
                            <Line type="monotone" dataKey="property" stroke="#fbbf24" strokeWidth={2} dot={false} name="Property" />
                            <Line type="monotone" dataKey="life" stroke="#34d399" strokeWidth={2} dot={false} name="Life" />
                        </LineChart>
                    </ResponsiveContainer>
                </ChartCard>
            </div>

            {/* Hospital table */}
            <ChartCard title="Top Hospitals by Claim Volume" subtitle="Ranked by number of submitted claims">
                <div className="table-wrap">
                    <table>
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Hospital</th>
                                <th>Claims</th>
                                <th>Total Amount</th>
                                <th>Avg per Claim</th>
                                <th>Volume Share</th>
                            </tr>
                        </thead>
                        <tbody>
                            {HOSPITAL_DATA.map((h, i) => {
                                const total = HOSPITAL_DATA.reduce((s, x) => s + x.claims, 0);
                                const share = ((h.claims / total) * 100).toFixed(1);
                                return (
                                    <tr key={h.name}>
                                        <td style={{ color: 'var(--text-muted)', fontWeight: 700 }}>#{i + 1}</td>
                                        <td style={{ fontWeight: 600 }}>{h.name}</td>
                                        <td><span style={{ fontWeight: 700, color: 'var(--primary)' }}>{h.claims}</span></td>
                                        <td>${(h.amount / 1_000_000).toFixed(1)}M</td>
                                        <td>${(h.amount / h.claims / 1000).toFixed(0)}K</td>
                                        <td>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
                                                <div className="progress-track" style={{ flex: 1 }}>
                                                    <div className="progress-fill" style={{ width: `${share}%` }} />
                                                </div>
                                                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', width: 36, textAlign: 'right' }}>{share}%</span>
                                            </div>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            </ChartCard>
        </div>
    );
}
