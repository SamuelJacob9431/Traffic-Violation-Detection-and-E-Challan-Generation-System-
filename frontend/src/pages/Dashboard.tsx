import React, { useState, useEffect } from 'react';
import { Camera, Activity, AlertTriangle, Car, ShieldAlert, Cpu } from 'lucide-react';
import axios from 'axios';
import { cn } from '../lib/utils';

const API_BASE = 'http://localhost:8000';

export function Dashboard() {
    const [signal, setSignal] = useState('GREEN');
    const [stats, setStats] = useState({
        activeVehicles: 0,
        violationsToday: 0,
        avgSpeed: 45,
        systemLoad: 24
    });
    const [violations, setViolations] = useState<any[]>([]);
    const [isCalibrating, setIsCalibrating] = useState(false);
    const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

    const updateSignal = async (newSignal: string) => {
        try {
            await axios.post(`${API_BASE}/update-signal?status=${newSignal}`);
            setSignal(newSignal);
        } catch (error) {
            console.error('Failed to update signal:', error);
        }
    };

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [statusRes, violationsRes] = await Promise.all([
                    axios.get(`${API_BASE}/status`),
                    axios.get(`${API_BASE}/violations/`)
                ]);
                setSignal(statusRes.data.signal);
                setViolations(violationsRes.data.reverse()); // Latest first
                setStats(prev => ({
                    ...prev,
                    violationsToday: violationsRes.data.length,
                    activeVehicles: 12 + Math.floor(Math.random() * 5) // Display mock live count
                }));
            } catch (err) {
                console.error("Dashboard polling failed:", err);
            }
        };

        fetchData();
        const interval = setInterval(fetchData, 5000); // 5s poll for demo
        return () => clearInterval(interval);
    }, []);

    const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
        if (!isCalibrating) return;
        const rect = e.currentTarget.getBoundingClientRect();

        // Calculate relative position (0 to 1)
        const relX = (e.clientX - rect.left) / rect.width;
        const relY = (e.clientY - rect.top) / rect.height;

        // Map to video resolution (640x360)
        setMousePos({
            x: Math.round(relX * 640),
            y: Math.round(relY * 360)
        });
    };

    return (
        <div className="space-y-8 max-w-7xl mx-auto">
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight mb-1">Live Intelligence</h2>
                    <p className="text-muted-foreground">Monitoring Intersection #04 - MG Road</p>
                </div>
                <div className="flex items-center gap-3">
                    <button
                        onClick={() => setIsCalibrating(!isCalibrating)}
                        className={cn(
                            "btn-premium btn-premium-secondary",
                            isCalibrating && "bg-primary/20 text-primary border-primary/30"
                        )}
                    >
                        {isCalibrating ? "Calibration Mode: ON" : "Calibration Mode"}
                    </button>
                    <div className="flex bg-white/5 p-1 rounded-xl border border-white/5">
                        {['RED', 'YELLOW', 'GREEN'].map((s) => (
                            <button
                                key={s}
                                onClick={() => updateSignal(s)}
                                className={cn(
                                    "px-4 py-2 rounded-lg text-xs font-bold transition-all",
                                    signal === s
                                        ? s === 'RED' ? "bg-rose-500 text-white shadow-[0_0_15px_rgba(244,63,94,0.4)]"
                                            : s === 'YELLOW' ? "bg-amber-500 text-white shadow-[0_0_15px_rgba(245,158,11,0.4)]"
                                                : "bg-emerald-500 text-white shadow-[0_0_15px_rgba(16,185,129,0.4)]"
                                        : "text-muted-foreground hover:bg-white/5"
                                )}
                            >
                                {s}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard icon={Car} label="Active Vehicles" value={stats.activeVehicles} trend="+12%" />
                <StatCard icon={ShieldAlert} label="Violations" value={stats.violationsToday} trend="+2" color="destructive" />
                <StatCard icon={Activity} label="Avg Speed" value={`${stats.avgSpeed} km/h`} trend="-5%" />
                <StatCard icon={Cpu} label="AI Node Load" value={`${stats.systemLoad}%`} trend="Normal" />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2 space-y-4">
                    <div className="flex items-center justify-between px-2">
                        <h3 className="font-bold flex items-center gap-2">
                            <Camera className="w-4 h-4 text-primary" />
                            Live Camera Feed
                        </h3>
                        <div className="flex items-center gap-2">
                            {isCalibrating && (
                                <div className="flex items-center gap-4 mr-4 px-3 py-1 bg-primary/10 rounded-full border border-primary/20">
                                    <span className="text-[10px] font-mono text-primary">X: {mousePos.x}</span>
                                    <span className="text-[10px] font-mono text-primary">Y: {mousePos.y}</span>
                                </div>
                            )}
                            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                            <span className="text-[10px] uppercase font-bold tracking-widest text-emerald-400">Video Demo Source</span>
                        </div>
                    </div>
                    <div
                        className={cn(
                            "glass-card aspect-video overflow-hidden group relative border-2 border-primary/10",
                            isCalibrating && "cursor-crosshair ring-2 ring-primary/50 ring-inset"
                        )}
                        onMouseMove={handleMouseMove}
                    >
                        <img
                            src={`${API_BASE}/video_feed`}
                            alt="Live Traffic Feed"
                            className="w-full h-full object-contain bg-black"
                        />
                        {isCalibrating && (
                            <div className="absolute inset-0 pointer-events-none">
                                {/* Crosshair lines */}
                                <div className="absolute top-0 bottom-0 border-l border-primary/30" style={{ left: `${(mousePos.x / 640) * 100}%` }} />
                                <div className="absolute left-0 right-0 border-t border-primary/30" style={{ top: `${(mousePos.y / 360) * 100}%` }} />
                                <div className="absolute bg-primary text-[10px] px-1.5 py-0.5 rounded text-white font-mono" style={{
                                    left: `${(mousePos.x / 640) * 100}%`,
                                    top: `${(mousePos.y / 360) * 100}%`,
                                    transform: 'translate(8px, 8px)'
                                }}>
                                    {mousePos.x}, {mousePos.y}
                                </div>
                            </div>
                        )}
                        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity p-6 flex flex-col justify-end">
                            <div className="flex gap-4">
                                <button className="btn-premium btn-premium-secondary btn-sm bg-white/10 text-white blur-none">Fullscreen</button>
                                <button className="btn-premium btn-premium-secondary btn-sm bg-white/10 text-white blur-none">Capture Frame</button>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="space-y-6">
                    <h3 className="font-bold flex items-center gap-2 px-2">
                        <AlertTriangle className="w-4 h-4 text-amber-500" />
                        Recent Alerts
                    </h3>
                    <div className="space-y-4">
                        {violations.slice(0, 5).map((alert: any, i: number) => (
                            <div key={alert.id || i} className="glass-card p-4 hover:bg-white/5 transition-colors group">
                                <div className="flex justify-between items-start mb-2">
                                    <span className={cn(
                                        "badge-premium",
                                        alert.type === 'Over Speed' ? 'badge-danger' : 'badge-warning'
                                    )}>{alert.type}</span>
                                    <span className="text-[10px] text-muted-foreground">
                                        {new Date(alert.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                    </span>
                                </div>
                                <p className="font-bold font-mono text-lg mb-1">{alert.plate_number}</p>
                                <div className="flex justify-between items-center">
                                    <span className="text-xs text-muted-foreground">Fine: <span className="text-foreground">₹{alert.fine}</span></span>
                                    <button className="text-xs text-primary font-bold opacity-0 group-hover:opacity-100 transition-opacity">Details →</button>
                                </div>
                            </div>
                        ))}
                        {violations.length === 0 && (
                            <div className="text-center py-8 text-muted-foreground text-sm italic">
                                Monitoring for violations...
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

function StatCard({ icon: Icon, label, value, trend, color = 'primary' }: any) {
    return (
        <div className="stat-card group">
            <div className="flex items-center justify-between mb-2">
                <div className={cn(
                    "p-2 rounded-lg bg-white/5 group-hover:bg-primary/10 transition-colors",
                    color === 'destructive' && "group-hover:bg-rose-500/10"
                )}>
                    <Icon className={cn(
                        "w-5 h-5 text-muted-foreground group-hover:text-primary transition-colors",
                        color === 'destructive' && "group-hover:text-rose-500"
                    )} />
                </div>
                <span className={cn(
                    "text-[10px] font-bold",
                    trend.startsWith('+') ? "text-emerald-400" : trend.startsWith('-') ? "text-rose-400" : "text-muted-foreground"
                )}>{trend}</span>
            </div>
            <p className="text-xs text-muted-foreground font-medium">{label}</p>
            <p className="text-2xl font-bold tracking-tight">{value}</p>
        </div>
    );
}
