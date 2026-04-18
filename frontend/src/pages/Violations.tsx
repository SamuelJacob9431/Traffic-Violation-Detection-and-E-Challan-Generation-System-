import React, { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import {
    Download, Search, Filter, ShieldCheck, ShieldAlert,
    FileText, CreditCard, Bell, X, RefreshCw, CheckCircle2
} from 'lucide-react';

const API_BASE = 'http://localhost:8000';
const REFRESH_INTERVAL = 10000; // 10 seconds

// ─── Toast Notification ───────────────────────────────────────────────────────
interface Toast {
    id: number;
    message: string;
    type: 'success' | 'info' | 'error';
}

function ToastContainer({ toasts, removeToast }: { toasts: Toast[]; removeToast: (id: number) => void }) {
    return (
        <div className="fixed top-4 right-4 z-50 flex flex-col gap-2">
            {toasts.map(t => (
                <div
                    key={t.id}
                    className={`flex items-center gap-3 px-4 py-3 rounded-xl shadow-2xl text-white text-sm font-medium
            backdrop-blur-xl border transition-all duration-300
            ${t.type === 'success' ? 'bg-emerald-600/90 border-emerald-400/30' :
                            t.type === 'error' ? 'bg-rose-600/90 border-rose-400/30' :
                                'bg-blue-600/90 border-blue-400/30'}`}
                    style={{ minWidth: 280, maxWidth: 380 }}
                >
                    {t.type === 'success' ? <CheckCircle2 className="w-4 h-4 shrink-0" /> :
                        t.type === 'error' ? <ShieldAlert className="w-4 h-4 shrink-0" /> :
                            <Bell className="w-4 h-4 shrink-0" />}
                    <span className="flex-1">{t.message}</span>
                    <button onClick={() => removeToast(t.id)} className="hover:opacity-70 transition">
                        <X className="w-4 h-4" />
                    </button>
                </div>
            ))}
        </div>
    );
}

// ─── Main Component ───────────────────────────────────────────────────────────
export function Violations() {
    const [violations, setViolations] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');
    const [payingId, setPayingId] = useState<number | null>(null);
    const [toasts, setToasts] = useState<Toast[]>([]);
    const [lastCount, setLastCount] = useState<number | null>(null);
    const [countdownSecs, setCountdownSecs] = useState(10);
    const toastIdRef = useRef(0);

    const addToast = useCallback((message: string, type: Toast['type'] = 'info') => {
        const id = ++toastIdRef.current;
        setToasts(prev => [...prev, { id, message, type }]);
        setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 4000);
    }, []);

    const removeToast = useCallback((id: number) => {
        setToasts(prev => prev.filter(t => t.id !== id));
    }, []);

    const fetchViolations = useCallback(async (silent = false) => {
        try {
            const res = await axios.get(`${API_BASE}/violations/`);
            const data: any[] = res.data;
            setViolations(data);

            // Detect new violations for popup
            setLastCount(prev => {
                if (prev !== null && data.length > prev) {
                    const newViolations = data.length - prev;
                    addToast(
                        `🚨 ${newViolations} new violation${newViolations > 1 ? 's' : ''} detected!`,
                        'info'
                    );
                }
                return data.length;
            });
        } catch (err) {
            if (!silent) console.error('Failed to fetch violations:', err);
        } finally {
            if (!silent) setLoading(false);
        }
    }, [addToast]);

    // Initial load
    useEffect(() => {
        fetchViolations(false);
    }, [fetchViolations]);

    // Auto-refresh every 10 seconds + countdown
    useEffect(() => {
        setCountdownSecs(10);
        const interval = setInterval(() => {
            fetchViolations(true);
            setCountdownSecs(10);
        }, REFRESH_INTERVAL);

        const countdown = setInterval(() => {
            setCountdownSecs(s => (s <= 1 ? 10 : s - 1));
        }, 1000);

        return () => {
            clearInterval(interval);
            clearInterval(countdown);
        };
    }, [fetchViolations]);

    // ── Pay Now handler ──────────────────────────────────────────────────────────
    const handlePayNow = async (v: any) => {
        if (v.status === 'Paid') return;
        setPayingId(v.id);
        try {
            await axios.post(`${API_BASE}/pay-challan/${v.id}`);
            addToast(`✅ Challan ${v.challan_number} marked as Paid!`, 'success');
            await fetchViolations(true);
        } catch (err: any) {
            addToast(`Payment failed: ${err?.response?.data?.detail || 'Unknown error'}`, 'error');
        } finally {
            setPayingId(null);
        }
    };

    // ── Download PDF handler ─────────────────────────────────────────────────────
    const handleDownloadPdf = (v: any) => {
        window.open(`${API_BASE}/violations/${v.id}/pdf`, '_blank');
    };

    // ── Filter ───────────────────────────────────────────────────────────────────
    const filtered = violations.filter(v =>
        !search ||
        v.plate_number?.toLowerCase().includes(search.toLowerCase()) ||
        v.challan_number?.toLowerCase().includes(search.toLowerCase())
    );

    const paidCount = violations.filter(v => v.status === 'Paid').length;
    const pendingCount = violations.filter(v => v.status !== 'Paid').length;

    return (
        <>
            <ToastContainer toasts={toasts} removeToast={removeToast} />

            <div className="space-y-8 max-w-7xl mx-auto">
                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
                    <div>
                        <h2 className="text-3xl font-bold tracking-tight mb-1">E-Challan Records</h2>
                        <p className="text-muted-foreground">Manage, pay and download traffic challans</p>
                    </div>
                    <div className="flex items-center gap-3">
                        {/* Live countdown badge */}
                        <span className="flex items-center gap-1.5 text-xs text-muted-foreground bg-white/5 border border-white/10 px-3 py-1.5 rounded-full">
                            <RefreshCw className="w-3 h-3 animate-spin" style={{ animationDuration: '3s' }} />
                            Refreshing in {countdownSecs}s
                        </span>
                        <button
                            onClick={() => { fetchViolations(true); addToast('Data refreshed', 'success'); }}
                            className="btn-premium btn-premium-secondary"
                        >
                            <RefreshCw className="w-4 h-4" />
                            Refresh
                        </button>
                    </div>
                </div>

                {/* KPI strip */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {[
                        { label: 'Total Challans', value: violations.length, color: 'text-blue-400' },
                        { label: 'Paid', value: paidCount, color: 'text-emerald-400' },
                        { label: 'Pending', value: pendingCount, color: 'text-rose-400' },
                        { label: 'Total Fines', value: `₹${violations.reduce((s, v) => s + (v.fine || 0), 0).toLocaleString()}`, color: 'text-yellow-400' },
                    ].map(k => (
                        <div key={k.label} className="glass-card p-4 flex flex-col gap-1">
                            <span className="text-xs text-muted-foreground uppercase tracking-widest">{k.label}</span>
                            <span className={`text-2xl font-bold ${k.color}`}>{k.value}</span>
                        </div>
                    ))}
                </div>

                {/* Table card */}
                <div className="glass-card overflow-hidden">
                    <div className="p-6 border-b border-white/5 flex flex-col md:flex-row md:items-center justify-between gap-4">
                        <div className="relative w-full md:w-96">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                            <input
                                type="text"
                                placeholder="Search plate or challan number..."
                                value={search}
                                onChange={e => setSearch(e.target.value)}
                                className="bg-white/5 border border-white/5 rounded-xl pl-10 pr-4 py-2 w-full text-sm outline-none focus:border-primary/30 transition-colors"
                            />
                        </div>
                        <div className="flex items-center gap-3 text-xs text-muted-foreground">
                            <span className="flex items-center gap-1">
                                <span className="w-2 h-2 rounded-full bg-emerald-500" /> Paid
                            </span>
                            <span className="flex items-center gap-1">
                                <span className="w-2 h-2 rounded-full bg-rose-500" /> Pending
                            </span>
                        </div>
                    </div>

                    <div className="overflow-x-auto">
                        <table className="w-full text-left">
                            <thead>
                                <tr className="bg-white/5">
                                    {['Challan No.', 'Vehicle Plate', 'Owner', 'Violation', 'Fine', 'Date/Time', 'Status', 'Actions'].map(h => (
                                        <th key={h} className="px-4 py-4 text-xs font-bold uppercase tracking-widest text-muted-foreground whitespace-nowrap">
                                            {h}
                                        </th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-white/5">
                                {loading ? (
                                    [1, 2, 3].map(i => (
                                        <tr key={i} className="animate-pulse">
                                            <td colSpan={8} className="px-4 py-8">
                                                <div className="h-4 bg-white/5 rounded w-full" />
                                            </td>
                                        </tr>
                                    ))
                                ) : filtered.length === 0 ? (
                                    <tr>
                                        <td colSpan={8} className="px-4 py-12 text-center text-muted-foreground">
                                            {search ? 'No matching records found.' : 'No violations recorded yet.'}
                                        </td>
                                    </tr>
                                ) : (
                                    filtered.map(v => {
                                        const isPaid = v.status === 'Paid';
                                        const isPaying = payingId === v.id;
                                        return (
                                            <tr
                                                key={v.id}
                                                className={`hover:bg-white/5 transition-colors group ${isPaid ? 'opacity-90' : ''}`}
                                            >
                                                {/* Challan number */}
                                                <td className="px-4 py-4 font-mono text-xs text-blue-300 whitespace-nowrap">
                                                    {v.challan_number || `#${v.id}`}
                                                </td>

                                                {/* Plate */}
                                                <td className="px-4 py-4 font-bold tracking-wider whitespace-nowrap">
                                                    {v.plate_number}
                                                </td>

                                                {/* Owner */}
                                                <td className="px-4 py-4 text-sm text-muted-foreground whitespace-nowrap">
                                                    {v.owner_name || '—'}
                                                </td>

                                                {/* Type */}
                                                <td className="px-4 py-4 italic text-sm whitespace-nowrap">{v.type}</td>

                                                {/* Fine */}
                                                <td className="px-4 py-4 font-bold text-yellow-400 whitespace-nowrap">₹{v.fine}</td>

                                                {/* Date */}
                                                <td className="px-4 py-4 text-xs text-muted-foreground whitespace-nowrap">
                                                    {v.timestamp ? new Date(v.timestamp).toLocaleString('en-IN') : '—'}
                                                </td>

                                                {/* Status badge */}
                                                <td className="px-4 py-4 whitespace-nowrap">
                                                    {isPaid ? (
                                                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                                                            <ShieldCheck className="w-3 h-3" /> Paid
                                                        </span>
                                                    ) : (
                                                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30">
                                                            <ShieldAlert className="w-3 h-3" /> Pending
                                                        </span>
                                                    )}
                                                    {isPaid && v.payment_date && (
                                                        <div className="text-xs text-emerald-500/70 mt-1">
                                                            {new Date(v.payment_date).toLocaleDateString('en-IN')}
                                                        </div>
                                                    )}
                                                </td>

                                                {/* Actions */}
                                                <td className="px-4 py-4 whitespace-nowrap">
                                                    <div className="flex items-center gap-2">
                                                        {/* Pay Now button */}
                                                        {!isPaid && (
                                                            <button
                                                                onClick={() => handlePayNow(v)}
                                                                disabled={isPaying}
                                                                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all
                                  ${isPaying
                                                                        ? 'bg-yellow-500/20 text-yellow-300 cursor-wait'
                                                                        : 'bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/40 border border-emerald-500/30 hover:scale-105'
                                                                    }`}
                                                                title="Pay Challan"
                                                            >
                                                                <CreditCard className="w-3.5 h-3.5" />
                                                                {isPaying ? 'Processing…' : 'Pay Now'}
                                                            </button>
                                                        )}

                                                        {/* Download PDF button */}
                                                        <button
                                                            onClick={() => handleDownloadPdf(v)}
                                                            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold bg-blue-500/20 text-blue-400 hover:bg-blue-500/40 border border-blue-500/30 transition-all hover:scale-105"
                                                            title="Download E-Challan PDF"
                                                        >
                                                            <FileText className="w-3.5 h-3.5" />
                                                            Download
                                                        </button>
                                                    </div>
                                                </td>
                                            </tr>
                                        );
                                    })
                                )}
                            </tbody>
                        </table>
                    </div>

                    {/* Footer */}
                    {violations.length > 0 && (
                        <div className="px-6 py-3 border-t border-white/5 text-xs text-muted-foreground flex justify-between">
                            <span>Showing {filtered.length} of {violations.length} records</span>
                            <span>Auto-refreshing every 10s</span>
                        </div>
                    )}
                </div>
            </div>
        </>
    );
}
