'use client';

import { useEffect, useState, use } from 'react';
import { useRouter } from 'next/navigation';
import { fetchMovieDetail } from '@/lib/api';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, Cell } from 'recharts';
import { ArrowLeft, TrendingUp, MapPin } from 'lucide-react';
import Navbar from '@/components/Navbar';

interface WeeklyRecord {
    report_date_start: string;
    report_date_end: string;
    weekly_revenue: number;
    cumulative_revenue: number;
    theater_count: number;
}

interface MovieMetadata {
    id: number;
    name: string;
    release_date: string | null;
    country: string | null;
    distributor: string | null;
}

interface ShowtimeStats {
    date: string;
    total_count: number;
    by_region: { [key: string]: number };
}

interface MovieDetailData {
    metadata: MovieMetadata;
    box_office_history: WeeklyRecord[];
    showtime_stats: ShowtimeStats;
}

export default function MovieDetailPage({ params }: { params: Promise<{ id: string }> }) {
    const router = useRouter();
    const { id } = use(params); // Unwrap the Promise using React.use()
    const [data, setData] = useState<MovieDetailData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const loadData = async () => {
            try {
                console.log(`🔍 Fetching movie detail for ID: ${id}`);
                console.log(`🌐 API URL: http://localhost:8000/movies/${id}`);

                const movieData = await fetchMovieDetail(parseInt(id));

                console.log('✅ Movie data received:', movieData);
                setData(movieData);
                setError(null);
            } catch (error: any) {
                console.error('❌ Error fetching movie detail:', error);
                console.error('Error details:', {
                    message: error.message,
                    response: error.response?.data,
                    status: error.response?.status,
                    statusText: error.response?.statusText
                });
                setError(error.response?.data?.detail || error.message || 'Failed to load movie details');
            } finally {
                setLoading(false);
            }
        };

        loadData();
    }, [id]);

    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
                <div className="text-white text-xl">載入中...</div>
            </div>
        );
    }

    if (!data) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
                <div className="text-center">
                    <div className="text-white text-xl mb-4">
                        {error || '找不到電影資訊'}
                    </div>
                    <button
                        onClick={() => router.push('/')}
                        className="text-purple-400 hover:text-purple-300 underline"
                    >
                        ← 返回首頁
                    </button>
                </div>
            </div>
        );
    }

    // Prepare chart data
    const revenueData = data.box_office_history.map(record => ({
        date: record.report_date_end,
        weekly: record.weekly_revenue,
        cumulative: record.cumulative_revenue,
    }));

    const regionalData = Object.entries(data.showtime_stats.by_region).map(([region, count]) => ({
        region,
        count,
    }));

    const totalRevenue = data.box_office_history.length > 0
        ? data.box_office_history[data.box_office_history.length - 1].cumulative_revenue
        : 0;

    // Smart offline detection: check if movie has recent revenue
    const hasRecentRevenue = data.box_office_history.length > 0 &&
        data.box_office_history[data.box_office_history.length - 1].weekly_revenue > 0;

    const isReallyOffline = regionalData.length === 0 && !hasRecentRevenue;

    const COLORS = ['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#14b8a6', '#6366f1', '#a855f7'];

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
            <Navbar />

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {/* Movie Header */}
                <div className="bg-white/10 backdrop-blur-md rounded-2xl p-8 border border-white/20 shadow-2xl mb-8">
                    <h1 className="text-4xl font-bold text-white mb-4">{data.metadata.name}</h1>
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-purple-200">
                        <div>
                            <span className="text-purple-400 text-sm">上映日期</span>
                            <p className="text-white font-medium">{data.metadata.release_date || 'N/A'}</p>
                        </div>
                        <div>
                            <span className="text-purple-400 text-sm">出品國家</span>
                            <p className="text-white font-medium">{data.metadata.country === '中華民國' ? '台灣' : (data.metadata.country || 'N/A')}</p>
                        </div>
                        <div>
                            <span className="text-purple-400 text-sm">發行片商</span>
                            <p className="text-white font-medium">{data.metadata.distributor || 'N/A'}</p>
                        </div>
                        <div>
                            <span className="text-purple-400 text-sm">累積票房</span>
                            <p className="text-green-400 text-2xl font-bold">
                                ${totalRevenue.toLocaleString()}
                            </p>
                        </div>
                    </div>
                </div>

                {/* Revenue Trend Chart */}
                <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-white/20 shadow-2xl mb-8">
                    <div className="flex items-center gap-2 mb-4">
                        <TrendingUp className="w-6 h-6 text-purple-400" />
                        <h2 className="text-2xl font-bold text-white">票房走勢趨勢</h2>
                    </div>
                    <p className="text-purple-200 mb-6">每週票房與累積票房變化</p>

                    {revenueData.length > 0 ? (
                        <ResponsiveContainer width="100%" height={400}>
                            <LineChart data={revenueData} margin={{ left: 40, right: 20, top: 10, bottom: 50 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                                <XAxis
                                    dataKey="date"
                                    stroke="#e9d5ff"
                                    angle={-45}
                                    textAnchor="end"
                                    height={80}
                                />
                                <YAxis
                                    stroke="#e9d5ff"
                                    tickFormatter={(value) => `${(value / 10000).toFixed(0)}萬`}
                                    width={80}
                                />
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: 'rgba(0,0,0,0.8)',
                                        border: '1px solid rgba(255,255,255,0.2)',
                                        borderRadius: '8px',
                                        color: '#fff'
                                    }}
                                    formatter={(value: any) => `$${value?.toLocaleString() || 0}`}
                                />
                                <Legend
                                    formatter={(value) => value === 'weekly' ? '每週票房' : '累積票房'}
                                />
                                <Line type="monotone" dataKey="weekly" stroke="#8b5cf6" strokeWidth={2} name="weekly" />
                                <Line type="monotone" dataKey="cumulative" stroke="#10b981" strokeWidth={2} name="cumulative" />
                            </LineChart>
                        </ResponsiveContainer>
                    ) : (
                        <p className="text-purple-200 text-center">無票房資料</p>
                    )}
                </div>

                {/* Regional Distribution Chart */}
                <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-white/20 shadow-2xl">
                    <div className="flex items-center gap-2 mb-4">
                        <MapPin className="w-6 h-6 text-purple-400" />
                        <h2 className="text-2xl font-bold text-white">全台地區銷售分佈</h2>
                    </div>
                    <p className="text-purple-200 mb-6">本週各地區上映場次統計 ({data.showtime_stats.date})</p>

                    {regionalData.length > 0 ? (
                        <ResponsiveContainer width="100%" height={300}>
                            <BarChart data={regionalData} margin={{ left: 10, right: 10, top: 10, bottom: 10 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                                <XAxis dataKey="region" stroke="#e9d5ff" />
                                <YAxis stroke="#e9d5ff" />
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: 'rgba(0,0,0,0.8)',
                                        border: '1px solid rgba(255,255,255,0.2)',
                                        borderRadius: '8px',
                                        color: '#fff'
                                    }}
                                    formatter={(value: any) => [`${value} 場次`, '上映場次']}
                                />
                                <Bar dataKey="count" radius={[8, 8, 0, 0]}>
                                    {regionalData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    ) : (
                        <div className="flex items-center justify-center h-48 bg-gray-800/30 rounded-lg">
                            <p className="text-gray-400 text-center">
                                {isReallyOffline
                                    ? '本片目前已下檔，無上映場次資訊'
                                    : '無法取得即時場次分佈，但本片仍在熱映中'}
                            </p>
                        </div>
                    )}
                </div>
                {/* Detailed Weekly Data Table */}
                <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-white/20 shadow-2xl">
                    <h2 className="text-2xl font-bold text-white mb-6">每週票房詳細資料</h2>
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b border-white/20">
                                    <th className="text-left py-3 px-4 text-purple-300 font-semibold whitespace-nowrap">日期</th>
                                    <th className="text-right py-3 px-4 text-purple-300 font-semibold whitespace-nowrap">週票房</th>
                                    <th className="text-right py-3 px-4 text-purple-300 font-semibold whitespace-nowrap">累計票房</th>
                                    <th className="text-right py-3 px-4 text-purple-300 font-semibold whitespace-nowrap">漲跌幅</th>
                                    <th className="text-right py-3 px-4 text-purple-300 font-semibold whitespace-nowrap">上映院數</th>
                                </tr>
                            </thead>
                            <tbody>
                                {[...data.box_office_history].sort((a, b) => new Date(b.report_date_end).getTime() - new Date(a.report_date_end).getTime()).map((record, index, array) => {
                                    // Calculate change: (Current - Next(PreviousWeek)) / Next * 100
                                    // Because we sorted DESC, the "previous week" is at index + 1
                                    const prevRecord = array[index + 1];
                                    let change = null;
                                    if (prevRecord && prevRecord.weekly_revenue > 0) {
                                        change = ((record.weekly_revenue - prevRecord.weekly_revenue) / prevRecord.weekly_revenue) * 100;
                                    }

                                    return (
                                        <tr key={record.report_date_end} className="border-b border-white/10 hover:bg-white/5 transition-colors">
                                            <td className="py-3 px-4 text-white font-medium whitespace-nowrap">
                                                {record.report_date_start} ~ {record.report_date_end}
                                            </td>
                                            <td className="py-3 px-4 text-right text-emerald-400 font-mono font-bold">
                                                ${record.weekly_revenue.toLocaleString()}
                                            </td>
                                            <td className="py-3 px-4 text-right text-white font-mono">
                                                ${record.cumulative_revenue.toLocaleString()}
                                            </td>
                                            <td className={`py-3 px-4 text-right font-bold ${change === null ? 'text-gray-400' :
                                                change > 0 ? 'text-green-500' :
                                                    change < 0 ? 'text-red-500' : 'text-gray-400'
                                                }`}>
                                                {change !== null ? `${change > 0 ? '+' : ''}${change.toFixed(1)}%` : '-'}
                                            </td>
                                            <td className="py-3 px-4 text-right text-purple-200">
                                                {record.theater_count}
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                </div>
            </main>
        </div>
    );
}
