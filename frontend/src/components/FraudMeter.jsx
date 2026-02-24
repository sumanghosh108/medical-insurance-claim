// FraudMeter — radial gauge for fraud probability
import { RadialBarChart, RadialBar, PolarAngleAxis, ResponsiveContainer } from 'recharts';

export default function FraudMeter({ probability = 0, riskLevel = 'low', size = 160 }) {
    const pct = Math.round(probability * 100);
    const color = probability < 0.3 ? '#34d399' : probability < 0.6 ? '#fbbf24' : '#f87171';
    const data = [{ value: pct, fill: color }];

    return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem' }}>
            <div style={{ position: 'relative', width: size, height: size }}>
                <ResponsiveContainer width="100%" height="100%">
                    <RadialBarChart
                        innerRadius="65%"
                        outerRadius="100%"
                        data={data}
                        startAngle={210}
                        endAngle={-30}
                    >
                        <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
                        {/* Track */}
                        <RadialBar
                            dataKey="value"
                            cornerRadius={8}
                            background={{ fill: 'rgba(255,255,255,0.05)' }}
                            data={[{ value: 100 }]}
                        />
                        <RadialBar
                            dataKey="value"
                            cornerRadius={8}
                            data={data}
                        />
                    </RadialBarChart>
                </ResponsiveContainer>
                {/* Center label */}
                <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                    <span style={{ fontSize: '1.5rem', fontWeight: 800, color }}>{pct}%</span>
                    <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Risk</span>
                </div>
            </div>
            <span style={{ fontSize: '0.8125rem', fontWeight: 700, color, textTransform: 'capitalize' }}>
                {riskLevel.replace('_', ' ')} Risk
            </span>
        </div>
    );
}
