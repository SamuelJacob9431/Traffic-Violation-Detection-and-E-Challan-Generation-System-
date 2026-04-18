import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Menu, Bell, User, Search } from 'lucide-react';

export function Layout() {
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);

    return (
        <div className="min-h-screen flex">
            <Sidebar isOpen={isSidebarOpen} setIsOpen={setIsSidebarOpen} />

            <main className="flex-1 flex flex-col min-w-0 lg:pl-72">
                {/* Navbar */}
                <header className="h-20 flex items-center justify-between px-6 lg:px-10 border-b border-white/5 sticky top-0 bg-background/50 backdrop-blur-md z-30">
                    <button
                        onClick={() => setIsSidebarOpen(true)}
                        className="p-2 lg:hidden text-muted-foreground hover:text-foreground"
                    >
                        <Menu className="w-6 h-6" />
                    </button>

                    <div className="hidden md:flex items-center gap-4 bg-white/5 px-4 py-2 rounded-xl border border-white/5 w-96">
                        <Search className="w-4 h-4 text-muted-foreground" />
                        <input
                            type="text"
                            placeholder="Search data, violations..."
                            className="bg-transparent border-none outline-none text-sm w-full placeholder:text-muted-foreground"
                        />
                    </div>

                    <div className="flex items-center gap-4">
                        <button className="p-2.5 rounded-xl bg-white/5 border border-white/5 text-muted-foreground hover:text-primary transition-colors relative">
                            <Bell className="w-5 h-5" />
                            <span className="absolute top-2 right-2 w-2 h-2 bg-primary rounded-full border-2 border-background" />
                        </button>
                        <div className="flex items-center gap-3 pl-4 border-l border-white/10">
                            <div className="text-right hidden sm:block">
                                <p className="text-sm font-semibold">Admin User</p>
                                <p className="text-[10px] text-muted-foreground">Traffic Authority</p>
                            </div>
                            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-blue-600 flex items-center justify-center font-bold shadow-lg">
                                AD
                            </div>
                        </div>
                    </div>
                </header>

                {/* Content */}
                <div className="flex-1 p-6 lg:p-10 custom-scrollbar overflow-y-auto">
                    <Outlet />
                </div>
            </main>
        </div>
    );
}
