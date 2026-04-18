import React, { useState, useEffect } from 'react';
import { Settings as SettingsIcon, MapPin, Gauge, Video, Layers, Save, RefreshCw, CheckCircle2 } from 'lucide-react';
import axios from 'axios';
import { cn } from '../lib/utils';

const API_BASE = 'http://localhost:8000';

export function Settings() {
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [saved, setSaved] = useState(false);
    const [formData, setFormData] = useState({
        location_name: '',
        camera_source: '',
        speed_limit: 50,
        distance_meters: 5.0,
        presentation_mode: 1,
        helmet_detection: 1,
        lane_detection: 1,
        input_mode: 'VIDEO'
    });

    useEffect(() => {
        const fetchSettings = async () => {
            try {
                const res = await axios.get(`${API_BASE}/settings`);
                if (res.data) {
                    setFormData({
                        location_name: res.data.location_name,
                        camera_source: res.data.camera_source,
                        speed_limit: res.data.speed_limit,
                        distance_meters: res.data.distance_meters,
                        presentation_mode: res.data.presentation_mode,
                        helmet_detection: res.data.helmet_detection ?? 1,
                        lane_detection: res.data.lane_detection ?? 1,
                        input_mode: res.data.input_mode
                    });
                }
            } catch (err) {
                console.error("Failed to fetch settings:", err);
            } finally {
                setLoading(false);
            }
        };
        fetchSettings();
    }, []);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setSaving(true);
        setSaved(false);
        try {
            const params = new URLSearchParams();
            Object.entries(formData).forEach(([key, value]) => params.append(key, value.toString()));

            await axios.post(`${API_BASE}/settings`, params);
            setSaved(true);
            setTimeout(() => setSaved(false), 3000);
        } catch (err) {
            console.error("Failed to save settings:", err);
            alert("Failed to save settings. Please ensure backend is running.");
        } finally {
            setSaving(false);
        }
    };

    if (loading) return (
        <div className="flex items-center justify-center h-64">
            <RefreshCw className="w-8 h-8 text-primary animate-spin" />
        </div>
    );

    return (
        <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div>
                <h2 className="text-3xl font-bold tracking-tight mb-2 flex items-center gap-3">
                    <SettingsIcon className="w-8 h-8 text-primary" />
                    Control Room
                </h2>
                <p className="text-muted-foreground">Calibrate AI parameters and system environment in real-time.</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Identification */}
                    <div className="glass-card p-6 space-y-4">
                        <div className="flex items-center gap-3 mb-2">
                            <MapPin className="w-5 h-5 text-primary" />
                            <h3 className="font-bold">Deployment Meta</h3>
                        </div>
                        <div className="space-y-2">
                            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Junction Location Name</label>
                            <input
                                type="text"
                                value={formData.location_name}
                                onChange={e => setFormData({ ...formData, location_name: e.target.value })}
                                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all font-medium"
                                placeholder="e.g. MG Road - Signal 04"
                            />
                        </div>
                    </div>

                    {/* AI Calibration */}
                    <div className="glass-card p-6 space-y-4">
                        <div className="flex items-center gap-3 mb-2">
                            <Gauge className="w-5 h-5 text-primary" />
                            <h3 className="font-bold">AI Calibration</h3>
                        </div>
                        <div className="space-y-4">
                            <div className="space-y-2">
                                <div className="flex justify-between">
                                    <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Speed Limit (km/h)</label>
                                    <span className="text-xs font-bold text-primary">{formData.speed_limit} km/h</span>
                                </div>
                                <input
                                    type="range"
                                    min="5"
                                    max="120"
                                    step="5"
                                    value={formData.speed_limit}
                                    onChange={e => setFormData({ ...formData, speed_limit: parseInt(e.target.value) })}
                                    className="w-full accent-primary h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer"
                                />
                            </div>
                            <div className="space-y-2">
                                <div className="flex justify-between">
                                    <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Line Distance (meters)</label>
                                    <span className="text-xs font-bold text-primary">{formData.distance_meters}m</span>
                                </div>
                                <input
                                    type="range"
                                    min="0.5"
                                    max="20.0"
                                    step="0.5"
                                    value={formData.distance_meters}
                                    onChange={e => setFormData({ ...formData, distance_meters: parseFloat(e.target.value) })}
                                    className="w-full accent-primary h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer"
                                />
                            </div>
                        </div>
                    </div>

                    {/* Media Source */}
                    <div className="glass-card p-6 space-y-4">
                        <div className="flex items-center gap-3 mb-2">
                            <Video className="w-5 h-5 text-primary" />
                            <h3 className="font-bold">Media Source</h3>
                        </div>
                        <div className="space-y-4">
                            <div className="flex p-1 bg-white/5 rounded-xl border border-white/5">
                                {['VIDEO', 'CAMERA'].map(mode => (
                                    <button
                                        key={mode}
                                        type="button"
                                        onClick={() => setFormData({ ...formData, input_mode: mode })}
                                        className={cn(
                                            "flex-1 py-2 text-[10px] font-bold rounded-lg transition-all",
                                            formData.input_mode === mode ? "bg-primary text-white shadow-lg shadow-primary/20" : "text-muted-foreground hover:bg-white/5"
                                        )}
                                    >
                                        {mode === 'VIDEO' ? 'RECORDED VIDEO' : 'LIVE RTSP/IP'}
                                    </button>
                                ))}
                            </div>
                            <div className="space-y-2">
                                <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Source URI</label>
                                <input
                                    type="text"
                                    value={formData.camera_source}
                                    onChange={e => setFormData({ ...formData, camera_source: e.target.value })}
                                    className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-xs font-mono focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
                                    placeholder="RTSP URL or file path"
                                />
                            </div>
                        </div>
                    </div>

                    {/* Interface Logic */}
                    <div className="glass-card p-6 space-y-4">
                        <div className="flex items-center gap-3 mb-2">
                            <Layers className="w-5 h-5 text-primary" />
                            <h3 className="font-bold">Visual Engine</h3>
                        </div>
                        <div className="space-y-4">
                            <div className="flex items-center justify-between p-3 bg-white/5 rounded-xl border border-white/5">
                                <div className="space-y-0.5">
                                    <p className="text-sm font-semibold">Presentation Mode</p>
                                    <p className="text-[10px] text-muted-foreground">Show extra labels for jury demo</p>
                                </div>
                                <button
                                    type="button"
                                    onClick={() => setFormData({ ...formData, presentation_mode: formData.presentation_mode === 1 ? 0 : 1 })}
                                    className={cn(
                                        "w-12 h-6 rounded-full transition-colors relative",
                                        formData.presentation_mode === 1 ? "bg-primary" : "bg-white/10"
                                    )}
                                >
                                    <div className={cn(
                                        "absolute top-1 left-1 w-4 h-4 bg-white rounded-full transition-transform",
                                        formData.presentation_mode === 1 ? "translate-x-6" : "translate-x-0"
                                    )} />
                                </button>
                            </div>
                            <div className="flex items-center justify-between p-3 bg-white/5 rounded-xl border border-white/5">
                                <div className="space-y-0.5">
                                    <p className="text-sm font-semibold text-emerald-400">Helmet Detection</p>
                                    <p className="text-[10px] text-muted-foreground">Auto-fine bikes without helmets</p>
                                </div>
                                <button
                                    type="button"
                                    onClick={() => setFormData({ ...formData, helmet_detection: formData.helmet_detection === 1 ? 0 : 1 })}
                                    className={cn(
                                        "w-12 h-6 rounded-full transition-colors relative",
                                        formData.helmet_detection === 1 ? "bg-emerald-500" : "bg-white/10"
                                    )}
                                >
                                    <div className={cn(
                                        "absolute top-1 left-1 w-4 h-4 bg-white rounded-full transition-transform",
                                        formData.helmet_detection === 1 ? "translate-x-6" : "translate-x-0"
                                    )} />
                                </button>
                            </div>
                            <div className="flex items-center justify-between p-3 bg-white/5 rounded-xl border border-white/5">
                                <div className="space-y-0.5">
                                    <p className="text-sm font-semibold text-amber-400">Lane Enforcement</p>
                                    <p className="text-[10px] text-muted-foreground">Monitor wrong lane crossing</p>
                                </div>
                                <button
                                    type="button"
                                    onClick={() => setFormData({ ...formData, lane_detection: formData.lane_detection === 1 ? 0 : 1 })}
                                    className={cn(
                                        "w-12 h-6 rounded-full transition-colors relative",
                                        formData.lane_detection === 1 ? "bg-amber-500" : "bg-white/10"
                                    )}
                                >
                                    <div className={cn(
                                        "absolute top-1 left-1 w-4 h-4 bg-white rounded-full transition-transform",
                                        formData.lane_detection === 1 ? "translate-x-6" : "translate-x-0"
                                    )} />
                                </button>
                            </div>
                            <div className="p-3 bg-primary/5 border border-primary/10 rounded-xl">
                                <p className="text-[10px] text-primary font-medium leading-tight">
                                    Changes to AI parameters (Speed/Distance) are applied instantly to the live stream.
                                </p>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="flex items-center justify-end gap-4 pt-4">
                    {saved && (
                        <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm animate-in fade-in slide-in-from-right-2">
                            <CheckCircle2 className="w-4 h-4" />
                            Settings Applied
                        </div>
                    )}
                    <button
                        type="submit"
                        disabled={saving}
                        className="btn-premium flex items-center gap-2 shadow-xl shadow-primary/20 disabled:opacity-50"
                    >
                        {saving ? (
                            <RefreshCw className="w-4 h-4 animate-spin" />
                        ) : (
                            <Save className="w-4 h-4" />
                        )}
                        Sync to AI Engine
                    </button>
                </div>
            </form>
        </div>
    );
}
