import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, BarChart3, AlertCircle, Settings, Menu, X } from 'lucide-react';
import { cn } from '../../lib/utils';

const navItems = [
    { icon: LayoutDashboard, label: 'Dashboard', path: '/' },
    { icon: BarChart3, label: 'Analytics', path: '/analytics' },
    { icon: AlertCircle, label: 'Violations', path: '/violations' },
    { icon: Settings, label: 'Settings', path: '/settings' },
];

export function Sidebar({ isOpen, setIsOpen }: { isOpen: boolean; setIsOpen: (val: boolean) => void }) {
    return (
        <>
            <div
                className={cn(
                    "fixed inset-0 bg-black/50 backdrop-blur-sm z-40 lg:hidden transition-opacity",
                    isOpen ? "opacity-100" : "opacity-0 pointer-events-none"
                )}
                onClick={() => setIsOpen(false)}
            />

            <aside className={cn(
                "fixed left-0 top-0 bottom-0 z-50 w-72 glass-card rounded-none border-r border-white/5 transition-transform duration-300 lg:translate-x-0 bg-background/80",
                !isOpen && "-translate-x-full"
            )}>
                <div className="flex flex-col h-full p-6">
                    <div className="flex items-center gap-3 mb-10 px-2">
                        <div className="w-10 h-10 rounded-xl bg-primary flex items-center justify-center shadow-[0_0_20px_rgba(56,189,248,0.3)]">
                            <LayoutDashboard className="text-primary-foreground w-6 h-6" />
                        </div>
                        <div>
                            <h1 className="font-bold text-xl tracking-tight">SmartCity</h1>
                            <p className="text-[10px] uppercase tracking-widest text-primary font-bold">Traffic Control</p>
                        </div>
                    </div>

                    <nav className="flex-1 space-y-2">
                        {navItems.map((item) => (
                            <NavLink
                                key={item.path}
                                to={item.path}
                                className={({ isActive }) => cn(
                                    "nav-link",
                                    isActive && "nav-link-active"
                                )}
                            >
                                <item.icon className="w-5 h-5" />
                                <span className="font-medium">{item.label}</span>
                            </NavLink>
                        ))}
                    </nav>

                    <div className="pt-6 border-t border-white/5">
                        <div className="glass-card p-4 bg-primary/5 border-primary/10">
                            <p className="text-xs text-muted-foreground mb-2">System Status</p>
                            <div className="flex items-center gap-2">
                                <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                                <span className="text-sm font-medium">All systems active</span>
                            </div>
                        </div>
                    </div>
                </div>
            </aside>
        </>
    );
}
