// StatCard — KPI card with trend
import { TrendingUp, TrendingDown } from 'lucide-react';

export default function StatCard({ title, value, subtitle, icon: Icon, trend, trendLabel, color = 'var(--primary)', style = {} }) {
    const isUp = trend > 0;
    return (
        <div className="glass" style={{ padding: '1.5rem', position: 'relative', overflow: 'hidden', ...style }}>
            {/* Glow blob */}
            <div style={{ position: 'absolute', top: '-30px', right: '-30px', width: '120px', height: '120px', borderRadius: '50%', background: `radial-gradient(circle, ${color}22, transparent 70%)`, pointerEvents: 'none' }} />

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                <div>
                    <p style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '0.35rem' }}>{title}</p>
                    <h2 style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--text-primary)', lineHeight: 1 }}>{value}</h2>
                </div>
                {Icon && (
                    <div style={{ background: `${color}20`, border: `1px solid ${color}40`, borderRadius: '12px', padding: '0.75rem', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                        <Icon size={22} color={color} />
                    </div>
                )}
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                {trend !== undefined && (
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.2rem', fontSize: '0.8125rem', fontWeight: 700, color: isUp ? 'var(--success)' : 'var(--danger)' }}>
                        {isUp ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                        {Math.abs(trend)}%
                    </span>
                )}
                {(subtitle || trendLabel) && (
                    <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>{subtitle || trendLabel}</span>
                )}
            </div>
        </div>
    );
}
