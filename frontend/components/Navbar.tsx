'use client';

import { useRouter, usePathname } from 'next/navigation';
import { Film, TrendingUp, BarChart2 } from 'lucide-react';
import Link from 'next/link';

export default function Navbar() {
    const router = useRouter();
    const pathname = usePathname();

    return (
        <nav className="bg-black/20 backdrop-blur-md border-b border-white/10 sticky top-0 z-50">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex items-center justify-between h-16">
                    <div
                        className="flex items-center gap-3 cursor-pointer"
                        onClick={() => router.push('/')}
                    >
                        <Film className="w-8 h-8 text-purple-400" />
                        <h1 className="text-2xl font-bold text-white hidden sm:block">台灣電影票房戰情室</h1>
                        <h1 className="text-xl font-bold text-white sm:hidden">戰情室</h1>
                    </div>

                    <div className="flex items-center gap-6">
                        <Link
                            href="/"
                            className={`flex items-center gap-2 text-sm font-medium transition-colors ${pathname === '/' ? 'text-white' : 'text-purple-300 hover:text-white'
                                }`}
                        >
                            <TrendingUp className="w-4 h-4" />
                            <span>即時戰情</span>
                        </Link>

                        <Link
                            href="/statistics"
                            className={`flex items-center gap-2 text-sm font-medium transition-colors ${pathname === '/statistics' ? 'text-white' : 'text-purple-300 hover:text-white'
                                }`}
                        >
                            <BarChart2 className="w-4 h-4" />
                            <span>票房統計</span>
                        </Link>
                    </div>
                </div>
            </div>
        </nav>
    );
}
