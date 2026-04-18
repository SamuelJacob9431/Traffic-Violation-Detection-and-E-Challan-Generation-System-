import React, { useState, useEffect } from 'react';
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    AreaChart, Area, PieChart, Pie, Cell, LineChart, Line, Legend, RadialBarChart, RadialBar
} from 'recharts';
import { TrendingUp, AlertCircle, Clock, DollarSign, Shield, Users, RefreshCw, Zap, Target, Activity } from 'lucide-react';
import axios from 'axios';

const API_BASE = 'http://localhost:8000';

const COLORS = {
    red: '#f43f5e',
    blue: '#38bdf8',
    purple: '#a78bfa',
    green: '#34d399',
    amber: '#f59e0b',
    rose: '#fb7185',
};

const PIE_COLORS = [COLORS.red, COLORS.blue, COLORS.purple, COLORS.green, COLORS.amber];

export function Analytics() {
    const [data, setData] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [lastUpdate, setLastUpdate] = useState('');

    useEffect(() => {
        const fetchAnalytics = async () => {
            try {
                const res = await axios.get(`${API_BASE}/analytics/`);
                setData(res.data);
                setLastUpdate(new Date().toLocaleTimeString());
            } catch (err) {
                console.error('Analytics fetch failed:', err);
            } finally {
                setLoading(false);
            }
        };
        fetchAnalytics();
        const interval = setInterval(fetchAnalytics, 5000); // 5 seconds
        return () => clearInterval(interval);
    }, []);

    if (loading || !data) {
        return (
            <div className="flex items-center justify-center min-h-[60vh]">
                <div className="text-center space-y-4">
                    <RefreshCw className="w-8 h-8 text-primary animate-spin mx-auto" />
                    <p className="text-muted-foreground">Loading Analytics...</p>
                </div>
            </div>
        );
    }

    // Compute collection rate
    const collectionRate = data.total_violations > 0
        ? Math.round((data.paid / data.total_violations) * 100,)
        : 0;

    // Radial data for collection gauge
    const gaugeData = [
        { name: 'Collected', value: collectionRate, fill: COLORS.green },
    ];

    return (
        <div className="space-y-8 max-w-7xl mx-auto">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight mb-1">Traffic Insights</h2>
                    <p className="text-muted-foreground">Comprehensive analytics from live violation data</p>
                </div>
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/5">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                    <span className="text-[10px] uppercase font-bold tracking-widest text-emerald-400">Live</span>
                    <span className="text-xs text-muted-foreground ml-1">IST • Every 5s • {lastUpdate}</span>
                </div>
            </div>

            {/* ─── KPI CARDS ─── */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                <KPICard icon={AlertCircle} label="Total Violations" value={data.total_violations} color="rose" />
                <KPICard icon={DollarSign} label="Total Fines" value={`₹${data.total_fines.toLocaleString()}`} color="amber" />
                <KPICard icon={Target} label="Avg Fine" value={`₹${data.avg_fine}`} color="blue" />
                <KPICard icon={Shield} label="Pending" value={data.pending} color="red" />
                <KPICard icon={Zap} label="Paid" value={data.paid} color="green" />
                <KPICard icon={Activity} label="Collection" value={`${collectionRate}%`} color="purple" />
            </div>

            {/* ─── ROW 1: Hourly Stacked Area + Violation Type Pie ─── */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Hourly Stacked Area Chart (2/3 width) */}
                <div className="lg:col-span-2 glass-card p-6">
                    <div className="flex items-center justify-between mb-6">
                        <div>
                            <h3 className="font-bold text-lg">24-Hour Violation Heatmap</h3>
                            <p className="text-sm text-muted-foreground">Red Light vs Speeding by hour of day</p>
                        </div>
                        <Clock className="w-5 h-5 text-primary" />
                    </div>
                    <div className="h-[300px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={data.hourly} barGap={0}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff08" vertical={false} />
                                <XAxis dataKey="hour" stroke="#64748b" fontSize={10} tickLine={false} axisLine={false} interval={2} />
                                <YAxis stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px', boxShadow: '0 25px 50px rgba(0,0,0,0.5)' }}
                                    itemStyle={{ color: '#f8fafc', fontSize: 12 }}
                                    labelStyle={{ color: '#94a3b8', fontWeight: 'bold', marginBottom: 4 }}
                                />
                                <Legend iconType="circle" wrapperStyle={{ fontSize: 11, paddingTop: 8 }} />
                                <Bar dataKey="redLight" stackId="a" fill={COLORS.red} name="Red Light" />
                                <Bar dataKey="overSpeed" stackId="a" fill={COLORS.blue} name="Over Speed" />
                                <Bar dataKey="noHelmet" stackId="a" fill={COLORS.green} name="No Helmet" />
                                <Bar dataKey="wrongLane" stackId="a" fill={COLORS.amber} name="Wrong Lane" radius={[4, 4, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Violation Type Pie (1/3 width) */}
                <div className="glass-card p-6 flex flex-col">
                    <div className="mb-4">
                        <h3 className="font-bold text-lg">Type Distribution</h3>
                        <p className="text-sm text-muted-foreground">Breakdown by category</p>
                    </div>
                    <div className="flex-1 flex items-center justify-center min-h-[220px]">
                        {data.type_breakdown.length > 0 ? (
                            <ResponsiveContainer width="100%" height={250}>
                                <PieChart>
                                    <Pie
                                        data={data.type_breakdown}
                                        cx="50%"
                                        cy="50%"
                                        innerRadius={55}
                                        outerRadius={85}
                                        paddingAngle={5}
                                        dataKey="count"
                                        nameKey="name"
                                        label={({ name, percent }: any) => `${name} ${(percent * 100).toFixed(0)}%`}
                                        labelLine={false}
                                    >
                                        {data.type_breakdown.map((_: any, i: number) => (
                                            <Cell key={`cell-${i}`} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                                        ))}
                                    </Pie>
                                    <Tooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px' }} />
                                </PieChart>
                            </ResponsiveContainer>
                        ) : (
                            <p className="text-muted-foreground text-sm italic">Awaiting data...</p>
                        )}
                    </div>
                    {/* Legend */}
                    <div className="space-y-2 mt-2">
                        {data.type_breakdown.map((item: any, i: number) => (
                            <div key={i} className="flex items-center justify-between text-sm">
                                <div className="flex items-center gap-2">
                                    <span className="w-3 h-3 rounded-full" style={{ backgroundColor: PIE_COLORS[i % PIE_COLORS.length] }} />
                                    <span className="text-muted-foreground">{item.name}</span>
                                </div>
                                <span className="font-bold">{item.count}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* ─── ROW 2: Daily Trend Line + Top Offenders ─── */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Daily Trend */}
                <div className="glass-card p-6">
                    <div className="flex items-center justify-between mb-6">
                        <div>
                            <h3 className="font-bold text-lg">Daily Trend</h3>
                            <p className="text-sm text-muted-foreground">Violations per day</p>
                        </div>
                        <TrendingUp className="w-5 h-5 text-emerald-500" />
                    </div>
                    <div className="h-[260px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={data.daily_trend}>
                                <defs>
                                    <linearGradient id="gradViolations" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor={COLORS.purple} stopOpacity={0.4} />
                                        <stop offset="95%" stopColor={COLORS.purple} stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff08" vertical={false} />
                                <XAxis dataKey="date" stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} />
                                <YAxis stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} />
                                <Tooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px' }} />
                                <Area type="monotone" dataKey="violations" stroke={COLORS.purple} fill="url(#gradViolations)" strokeWidth={3} dot={{ r: 4, fill: COLORS.purple }} />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Top Offenders Table */}
                <div className="glass-card p-6">
                    <div className="flex items-center justify-between mb-6">
                        <div>
                            <h3 className="font-bold text-lg">Top Offenders</h3>
                            <p className="text-sm text-muted-foreground">Vehicles with most violations</p>
                        </div>
                        <Users className="w-5 h-5 text-rose-500" />
                    </div>
                    <div className="space-y-3">
                        {data.top_offenders.map((item: any, i: number) => {
                            const maxCount = data.top_offenders[0]?.count || 1;
                            const pct = Math.round((item.count / maxCount) * 100);
                            return (
                                <div key={i} className="space-y-1.5">
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-3">
                                            <span className="w-6 h-6 rounded-full bg-white/5 flex items-center justify-center text-[10px] font-bold text-muted-foreground">
                                                {i + 1}
                                            </span>
                                            <span className="font-mono font-bold text-sm">{item.plate}</span>
                                        </div>
                                        <span className="text-sm font-bold text-rose-400">{item.count} violations</span>
                                    </div>
                                    <div className="h-1.5 rounded-full bg-white/5 overflow-hidden">
                                        <div
                                            className="h-full rounded-full transition-all duration-500"
                                            style={{
                                                width: `${pct}%`,
                                                background: `linear-gradient(90deg, ${COLORS.red}, ${COLORS.amber})`
                                            }}
                                        />
                                    </div>
                                </div>
                            );
                        })}
                        {data.top_offenders.length === 0 && (
                            <p className="text-muted-foreground text-sm italic text-center py-8">No offenders yet...</p>
                        )}
                    </div>
                </div>
            </div>

            {/* ─── ROW 3: Recent Activity Timeline ─── */}
            <div className="glass-card p-6">
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h3 className="font-bold text-lg">Recent Activity</h3>
                        <p className="text-sm text-muted-foreground">Last 10 violations in real-time</p>
                    </div>
                    <div className="flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                        <span className="text-[10px] text-emerald-400 font-bold uppercase tracking-widest">Live Feed</span>
                    </div>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead>
                            <tr className="bg-white/5">
                                <th className="px-4 py-3 text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Date</th>
                                <th className="px-4 py-3 text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Time (IST)</th>
                                <th className="px-4 py-3 text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Plate</th>
                                <th className="px-4 py-3 text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Type</th>
                                <th className="px-4 py-3 text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Fine</th>
                                <th className="px-4 py-3 text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Status</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                            {data.recent_timeline.map((v: any, i: number) => (
                                <tr key={v.id || i} className="hover:bg-white/5 transition-colors">
                                    <td className="px-4 py-3 text-xs text-muted-foreground">{v.date}</td>
                                    <td className="px-4 py-3 font-mono text-sm text-muted-foreground">{v.time}</td>
                                    <td className="px-4 py-3 font-mono font-bold">{v.plate}</td>
                                    <td className="px-4 py-3">
                                        <span className={`text-xs font-bold px-2 py-1 rounded-full ${v.type === 'Red Light Jump' ? 'bg-rose-500/10 text-rose-400' : 'bg-sky-500/10 text-sky-400'}`}>
                                            {v.type}
                                        </span>
                                    </td>
                                    <td className="px-4 py-3 font-bold text-amber-400">₹{v.fine}</td>
                                    <td className="px-4 py-3">
                                        <span className={`text-xs font-bold ${v.status === 'Paid' ? 'text-emerald-400' : 'text-rose-400'}`}>
                                            {v.status}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                            {data.recent_timeline.length === 0 && (
                                <tr><td colSpan={6} className="px-4 py-8 text-center text-muted-foreground text-sm italic">Monitoring...</td></tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}

function KPICard({ icon: Icon, label, value, color }: any) {
    const colorMap: Record<string, string> = {
        rose: 'text-rose-400 bg-rose-500/10',
        amber: 'text-amber-400 bg-amber-500/10',
        blue: 'text-sky-400 bg-sky-500/10',
        red: 'text-red-400 bg-red-500/10',
        green: 'text-emerald-400 bg-emerald-500/10',
        purple: 'text-violet-400 bg-violet-500/10',
    };
    const cls = colorMap[color] || colorMap.blue;

    return (
        <div className="glass-card p-4 group hover:scale-[1.02] transition-transform">
            <div className={`w-9 h-9 rounded-lg flex items-center justify-center mb-3 ${cls}`}>
                <Icon className="w-4 h-4" />
            </div>
            <p className="text-[10px] text-muted-foreground font-semibold uppercase tracking-wider mb-0.5">{label}</p>
            <p className="text-xl font-bold tracking-tight">{value}</p>
        </div>
    );
}
