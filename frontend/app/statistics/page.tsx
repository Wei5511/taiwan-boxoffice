'use client';

import { useEffect, useState, useMemo } from 'react';
import Navbar from '@/components/Navbar';
import MultiSelect from '@/components/MultiSelect';
import { fetchMarketGrowthStats, MarketStat, fetchPeriodStats, PeriodStatsResponse } from '@/lib/api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, BarChart, Bar, ReferenceArea } from 'recharts';
import { Calendar, TrendingUp, Award } from 'lucide-react';
import axios from 'axios';

const getBoxOfficeWeekRange = (year: number, week: number) => {
    if (!year || week === undefined) return { short: `W${week}`, full: `Week ${week}` };
    const validWeek = week === 0 ? 1 : week;
    const jan4 = new Date(year, 0, 4);
    const day = jan4.getDay() || 7;
    const week1Monday = new Date(year, 0, 4 - day + 1);
    const targetMonday = new Date(week1Monday.getTime() + (validWeek - 1) * 7 * 24 * 60 * 60 * 1000);
    const targetSunday = new Date(targetMonday.getTime() + 6 * 24 * 60 * 60 * 1000);
    const format = (d: Date) => `${d.getMonth() + 1}/${d.getDate()}`;
    return {
        short: format(targetSunday),
        full: `${format(targetMonday)} ~ ${format(targetSunday)}`
    };
};

export default function StatisticsPage() {
    // --- Chart Data State ---
    const [stats, setStats] = useState<MarketStat[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedYears, setSelectedYears] = useState<number[]>([]);
    const [chartView, setChartView] = useState<'weekly' | 'cumulative'>('weekly');

    // --- Report Data State ---
    const [reportType, setReportType] = useState<'week' | 'month' | 'year' | 'all_time'>('month');
    const [reportYear, setReportYear] = useState<number>(new Date().getFullYear());
    const [reportMonth, setReportMonth] = useState<number>(new Date().getMonth() + 1);
    const [reportNumber, setReportNumber] = useState<number>(new Date().getMonth() + 1); // For week/month value
    const [page, setPage] = useState(1);
    const [limit] = useState(30);
    const [reportData, setReportData] = useState<PeriodStatsResponse | null>(null);
    const [reportLoading, setReportLoading] = useState(false);

    // --- Modal State ---
    const [selectedMovieDetails, setSelectedMovieDetails] = useState<any>(null);
    const [isModalOpen, setIsModalOpen] = useState(false);

    // 1. Fetch Overall Market Stats (for Chart)
    useEffect(() => {
        const loadData = async () => {
            try {
                const data = await fetchMarketGrowthStats();
                setStats(data);

                // Default select last 2 years (Sort descending first)
                const years = Array.from(new Set(data.map(s => s.year))).sort((a, b) => b - a);
                setSelectedYears(years.slice(0, 3)); // Default top 3 recent years
            } catch (error) {
                console.error('Error fetching market stats:', error);
            } finally {
                setLoading(false);
            }
        };
        loadData();
    }, []);

    // 2. Fetch Period Report Data
    useEffect(() => {
        const loadReport = async () => {
            setPage(1); // Reset to first page
            setReportLoading(true);
            try {
                // Validate inputs
                if (reportType === 'week' && (reportNumber < 1 || reportNumber > 53)) return;
                if (reportType === 'month' && (reportNumber < 1 || reportNumber > 12)) return;

                const data = await fetchPeriodStats(reportType, reportYear, reportNumber);
                setReportData(data);
            } catch (error) {
                console.error('Error fetching report:', error);
                setReportData(null);
            } finally {
                setReportLoading(false);
            }
        };
        loadReport();
    }, [reportType, reportYear, reportNumber]);

    // Derived filtered weeks based on selected month
    const filteredWeeks = useMemo(() => {
        if (reportType !== 'week') return [];
        // Approximate calculation: weeks 1-4 belong to month 1, 5-8 to month 2, etc.
        // A more precise calculation would determine the exact ISO weeks for a given month/year.
        // For simplicity, we use an approximation:
        const startWeek = (reportMonth - 1) * 4 + 1 + (reportMonth > 8 ? 1 : 0); // slight adjustment
        const endWeek = reportMonth === 12 ? 53 : startWeek + 3 + (reportMonth % 3 === 0 ? 1 : 0);
        return Array.from({ length: endWeek - startWeek + 1 }, (_, i) => startWeek + i);
    }, [reportMonth, reportType]);

    // Fetch Movie Details
    const handleMovieClick = async (movieId: number) => {
        try {
            const res = await axios.get(`http://127.0.0.1:8001/movies/${movieId}/details`);
            setSelectedMovieDetails(res.data);
            setIsModalOpen(true);
        } catch (error) {
            console.error("Failed to fetch movie details:", error);
        }
    };

    // --- Chart Data Processing ---
    // Sort years ascending for the dropdown list options
    const uniqueYears = useMemo(() => Array.from(new Set(stats.map(s => s.year))).sort((a, b) => b - a), [stats]);

    const chartData = useMemo(() => {
        if (loading || stats.length === 0) return [];
        const weeks = Array.from({ length: 53 }, (_, i) => i + 1);
        const data: any[] = [];

        // Find max week with data for each selected year to avoid rendering flatlines into the future
        const maxWeeks: Record<number, number> = {};
        selectedYears.forEach(y => {
            const yearStats = stats.filter(s => s.year === y);
            maxWeeks[y] = yearStats.length > 0 ? Math.max(...yearStats.map(s => s.week)) : 0;
        });

        const cumulativeTotals: Record<number, number> = {};
        selectedYears.forEach(y => cumulativeTotals[y] = 0);

        weeks.forEach(week => {
            const point: any = { week };
            let hasDataForAnyYear = false;

            selectedYears.forEach(year => {
                const stat = stats.find(s => s.year === year && s.week === week);

                if (chartView === 'cumulative') {
                    if (stat) {
                        cumulativeTotals[year] += stat.total_revenue;
                    }

                    // Only add the cumulative point if we haven't exceeded the max week for this year
                    if (week <= maxWeeks[year] && maxWeeks[year] > 0) {
                        point[year] = cumulativeTotals[year];
                        hasDataForAnyYear = true;
                    }
                } else {
                    if (stat) {
                        point[year] = stat.total_revenue;
                        hasDataForAnyYear = true;
                    }
                }
            });

            // Always push the point to ensure all 53 weeks are plotted on the XAxis
            data.push(point);
        });
        return data;
    }, [stats, loading, selectedYears, chartView]);

    // Fixed Color Map: Year % Length
    const COLORS = ['#8b5cf6', '#10b981', '#f59e0b', '#ec4899', '#3b82f6', '#6366f1'];
    const getYearColor = (year: number) => COLORS[year % COLORS.length];

    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
                <div className="text-white text-xl">Loading Statistics...</div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
            <Navbar />

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">

                {/* Header */}
                <div className="bg-white/10 backdrop-blur-md rounded-2xl p-8 border border-white/20 shadow-2xl">
                    <h1 className="text-3xl font-bold text-white mb-2">全台票房統計資料</h1>
                    <p className="text-purple-200">Interactive Market Analysis & Reports</p>
                </div>

                {/* 1. Interactive Trend Chart */}
                <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-white/20 shadow-2xl">
                    <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
                        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                            <TrendingUp className="w-6 h-6 text-purple-400" />
                            年度票房趨勢比較
                        </h2>

                        {/* Controls Group */}
                        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 z-10">
                            {/* Toggle View */}
                            <div className="flex bg-black/30 rounded-lg p-1 border border-white/10 shrink-0">
                                <button
                                    onClick={() => setChartView('weekly')}
                                    className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all ${chartView === 'weekly' ? 'bg-purple-600 text-white shadow' : 'text-gray-400 hover:text-white'}`}
                                >
                                    每週票房
                                </button>
                                <button
                                    onClick={() => setChartView('cumulative')}
                                    className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all ${chartView === 'cumulative' ? 'bg-purple-600 text-white shadow' : 'text-gray-400 hover:text-white'}`}
                                >
                                    累積票房
                                </button>
                            </div>

                            {/* MultiSelect Year Filter */}
                            <div className="shrink-0">
                                <MultiSelect
                                    label="選擇年份"
                                    options={uniqueYears}
                                    selected={selectedYears}
                                    onChange={setSelectedYears}
                                />
                            </div>
                        </div>
                    </div>

                    <div className="h-[400px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                                <XAxis
                                    dataKey="week"
                                    stroke="#e9d5ff"
                                    label={{ value: '週次 (Week)', position: 'insideBottomRight', offset: -5, fill: '#e9d5ff' }}
                                />
                                <YAxis
                                    stroke="#e9d5ff"
                                    tickFormatter={(value) => `${(value / 100000000).toFixed(1)}億`}
                                    width={60}
                                />
                                <Tooltip
                                    contentStyle={{ backgroundColor: 'rgba(0,0,0,0.9)', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '8px' }}
                                    formatter={(value: any, name: any) => [`$${value.toLocaleString()}`, `${name}年`]}
                                    labelFormatter={(label) => `第 ${label} 週`}
                                />
                                <Legend />

                                {/* Quarterly Background Zones */}
                                <ReferenceArea x1={1} x2={13} fill="#a855f7" fillOpacity={0.04} strokeOpacity={0} label={{ position: 'insideTop', value: 'Q1', fill: 'rgba(255,255,255,0.2)', fontSize: 32, fontWeight: 'bold' }} />
                                <ReferenceArea x1={13} x2={26} fill="#0ea5e9" fillOpacity={0.05} strokeOpacity={0} label={{ position: 'insideTop', value: 'Q2', fill: 'rgba(255,255,255,0.2)', fontSize: 32, fontWeight: 'bold' }} />
                                <ReferenceArea x1={26} x2={39} fill="#f97316" fillOpacity={0.05} strokeOpacity={0} label={{ position: 'insideTop', value: 'Q3', fill: 'rgba(255,255,255,0.2)', fontSize: 32, fontWeight: 'bold' }} />
                                <ReferenceArea x1={39} x2={53} fill="#22c55e" fillOpacity={0.05} strokeOpacity={0} label={{ position: 'insideTop', value: 'Q4', fill: 'rgba(255,255,255,0.2)', fontSize: 32, fontWeight: 'bold' }} />

                                {selectedYears.map(year => (
                                    <Line
                                        key={year}
                                        type="monotone"
                                        dataKey={year}
                                        name={`${year}`}
                                        stroke={getYearColor(year)}
                                        strokeWidth={3}
                                        dot={{ r: 3 }}
                                        activeDot={{ r: 6 }}
                                        connectNulls={true}
                                    />
                                ))}
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* 2. Interactive Period Explorer (Drill Down) */}
                <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-white/20 shadow-2xl">
                    <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-6 border-b border-white/10 pb-6">
                        <div className="flex items-center gap-2">
                            <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                                <Award className="w-6 h-6 text-yellow-400" />
                                區間市場報表
                            </h2>

                            {/* Info Icon with Tooltip */}
                            <div className="relative group cursor-help mt-1">
                                <svg className="w-5 h-5 text-gray-400 hover:text-purple-400 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                                {/* Tooltip Box */}
                                <div className="absolute left-1/2 -translate-x-1/2 top-full mt-2 w-80 p-3 bg-[#1F2937] border border-gray-600 rounded-lg text-xs text-gray-300 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 shadow-2xl leading-relaxed">
                                    本系統數據由「每週票房」動態加總運算。因跨月/跨年之週次邊界無法精準切割至單日，且部分微型電影未列入官方週報，故與官方發布之月報/年報可能存在些微合理誤差。
                                </div>
                            </div>
                        </div>

                        {/* Controls */}
                        <div className="flex flex-wrap items-center gap-4">
                            {/* Type Selector */}
                            <div className="flex bg-black/30 rounded-lg p-1 overflow-x-auto">
                                {['week', 'month', 'year', 'all_time'].map((t) => (
                                    <button
                                        key={t}
                                        onClick={() => setReportType(t as any)}
                                        className={`px-4 py-2 rounded-md text-sm font-medium transition-all whitespace-nowrap ${reportType === t
                                            ? t === 'all_time' ? 'bg-gradient-to-r from-yellow-600 to-yellow-800 text-white shadow-lg border border-yellow-400/50' : 'bg-purple-600 text-white shadow'
                                            : 'text-gray-400 hover:text-white'
                                            }`}
                                    >
                                        {t === 'week' ? '週報表' : t === 'month' ? '月報表' : t === 'year' ? '年報表' : '👑 歷史總榜'}
                                    </button>
                                ))}
                            </div>

                            {/* Year Selector (Hidden for All-Time) */}
                            {reportType !== 'all_time' && (
                                <select
                                    value={reportYear}
                                    onChange={(e) => setReportYear(Number(e.target.value))}
                                    className="bg-black/30 border border-white/20 text-white rounded-lg px-4 py-2 outline-none focus:border-purple-500"
                                >
                                    {uniqueYears.map(y => <option key={y} value={y}>{y}年</option>)}
                                </select>
                            )}

                            {/* Month Selector (For Month and Week Reports) */}
                            {reportType !== 'year' && reportType !== 'all_time' && (
                                <select
                                    value={reportType === 'month' ? reportNumber : reportMonth}
                                    onChange={(e) => {
                                        const newMonth = Number(e.target.value);
                                        if (reportType === 'month') {
                                            setReportNumber(newMonth);
                                        } else {
                                            setReportMonth(newMonth);
                                        }
                                    }}
                                    className="bg-black/30 border border-white/20 text-white rounded-lg px-4 py-2 outline-none focus:border-purple-500"
                                >
                                    {Array.from({ length: 12 }, (_, i) => i + 1).map(m => (
                                        <option key={m} value={m}>{m}月</option>
                                    ))}
                                </select>
                            )}

                            {/* Week Selector (Only for Week Report) - Filtered by Month */}
                            {reportType === 'week' && (
                                <select
                                    value={reportNumber}
                                    onChange={(e) => setReportNumber(Number(e.target.value))}
                                    className="bg-black/30 border border-white/20 text-white rounded-lg px-4 py-2 outline-none focus:border-purple-500"
                                >
                                    {filteredWeeks.map((w, index) => (
                                        <option key={w} value={w}>第 {index + 1} 週</option>
                                    ))}
                                </select>
                            )}
                        </div>
                    </div>

                    {/* Report Content */}
                    {reportLoading ? (
                        <div className="h-64 flex items-center justify-center text-white/50">Loading Report...</div>
                    ) : reportData ? (
                        <div className="space-y-8">
                            {/* Summary Cards */}
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <div className="bg-black/20 rounded-xl p-4 border border-white/10">
                                    <div className="text-purple-300 text-sm mb-1">區間總票房</div>
                                    <div className="text-2xl font-bold text-emerald-400 font-mono">
                                        ${reportData.summary.total_revenue.toLocaleString()}
                                    </div>
                                    <div className={`text-sm mt-2 ${reportData.summary.growth_rate >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                                        {reportData.summary.growth_rate >= 0 ? '▲' : '▼'} {Math.abs(reportData.summary.growth_rate * 100).toFixed(1)}% (vs 上期)
                                    </div>
                                </div>
                                <div className="bg-black/20 rounded-xl p-4 border border-white/10">
                                    <div className="text-purple-300 text-sm mb-1">上映電影數</div>
                                    <div className="text-2xl font-bold text-white">
                                        {reportData.summary.movie_count} 部
                                    </div>
                                </div>
                                <div className="bg-black/20 rounded-xl p-4 border border-white/10">
                                    <div className="text-purple-300 text-sm mb-1">統計區間</div>
                                    <div className="text-lg font-medium text-white">
                                        {reportData.summary.start_date} ~ {reportData.summary.end_date}
                                    </div>
                                </div>
                            </div>

                            {/* Rankings Table */}
                            <div className="overflow-x-auto">
                                <table className="w-full">
                                    <thead>
                                        <tr className="border-b border-white/20">
                                            <th className="text-left py-3 px-4 text-purple-300 font-semibold w-16">排名</th>
                                            <th className="text-left py-3 px-4 text-purple-300 font-semibold">片名</th>
                                            <th className="text-left py-3 px-4 text-purple-300 font-semibold">上映日期</th>
                                            <th className="text-right py-3 px-4 text-purple-300 font-semibold">區間票房</th>
                                            <th className="text-right py-3 px-4 text-purple-300 font-semibold">區間票數</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {reportData.rankings.length > 0 ? (
                                            reportData.rankings.slice((page - 1) * limit, page * limit).map((item, index) => (
                                                <tr key={item.id || index} onClick={item.id ? () => handleMovieClick(item.id!) : undefined} className="border-b border-white/10 last:border-b-0 hover:bg-white/5 transition-colors cursor-pointer">
                                                    <td className="py-4 px-4 text-purple-300 font-medium">{(page - 1) * limit + index + 1}</td>
                                                    <td className="py-4 px-4 text-white font-medium whitespace-normal break-words">{item.name}</td>
                                                    <td className="py-4 px-4 text-purple-200 whitespace-nowrap">{item.release_date || 'N/A'}</td>
                                                    <td className="py-4 px-4 text-right text-green-400 font-semibold whitespace-nowrap min-w-[120px]">
                                                        ${item.revenue.toLocaleString()}
                                                    </td>
                                                    <td className="py-4 px-4 text-right text-blue-300 whitespace-nowrap min-w-[100px]">
                                                        {item.tickets ? item.tickets.toLocaleString() : '未提供'}
                                                    </td>
                                                </tr>
                                            ))
                                        ) : (
                                            <tr>
                                                <td colSpan={5} className="py-8 text-center text-white/50">
                                                    此區間無資料
                                                </td>
                                            </tr>
                                        )}
                                    </tbody>
                                </table>
                            </div>

                            {/* Pagination Controls */}
                            <div className="flex justify-center items-center gap-4 pt-4 border-t border-white/10">
                                <button
                                    onClick={() => setPage(p => Math.max(1, p - 1))}
                                    disabled={page === 1}
                                    className={`px-4 py-2 rounded-lg font-medium transition-colors ${page === 1 ? 'bg-white/5 text-gray-600' : 'bg-purple-600 text-white hover:bg-purple-500'
                                        }`}
                                >
                                    上一頁
                                </button>
                                <span className="text-gray-400 text-sm">第 {page} 頁 / 共 {Math.ceil((reportData?.rankings?.length ?? 0) / limit)} 頁</span>
                                <button
                                    onClick={() => setPage(p => p + 1)}
                                    disabled={!reportData || reportData.rankings.length <= page * limit}
                                    className={`px-4 py-2 rounded-lg font-medium transition-colors ${!reportData || reportData.rankings.length <= page * limit ? 'bg-white/5 text-gray-600' : 'bg-purple-600 text-white hover:bg-purple-500'
                                        }`}
                                >
                                    下一頁
                                </button>
                            </div>
                        </div>
                    ) : (
                        <div className="py-12 text-center text-red-400">無法載入報表數據</div>
                    )}
                </div>

            </main>

            {/* MOVIE DETAIL MODAL */}
            {isModalOpen && selectedMovieDetails && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4" onClick={() => setIsModalOpen(false)}>
                    <div className="bg-[#1F2937] rounded-xl w-full max-w-5xl max-h-[90vh] overflow-y-auto border border-gray-700 shadow-2xl" onClick={e => e.stopPropagation()}>
                        <div className="flex justify-between items-start p-6 border-b border-gray-700 sticky top-0 bg-[#1F2937] z-10">
                            <div>
                                <h2 className="text-3xl font-bold text-white mb-2">{selectedMovieDetails.info.name}</h2>
                                <div className="flex gap-4 text-sm text-gray-400 mb-4">
                                    <span>發行日期: {selectedMovieDetails.info.release_date}</span>
                                    <span>國家: {selectedMovieDetails.info.country}</span>
                                </div>

                                <div className="flex flex-col gap-1 text-sm text-gray-300 bg-[#111827] p-4 rounded-lg border border-gray-800 mb-6">
                                    <div className="flex items-start gap-2">
                                        <span className="text-gray-500 font-bold min-w-[70px]">出品公司:</span>
                                        <span>{selectedMovieDetails.info.distributor || "未提供 (資料庫無紀錄)"}</span>
                                    </div>
                                </div>
                            </div>
                            <button onClick={() => setIsModalOpen(false)} className="text-gray-400 hover:text-white text-3xl">&times;</button>
                        </div>

                        {/* Charts Content */}
                        <div className="p-6 grid grid-cols-1 lg:grid-cols-2 gap-8">
                            {/* Line Chart: Weekly Revenue */}
                            <div className="bg-[#111827] p-4 rounded-lg border border-gray-800">
                                <h3 className="text-lg font-bold text-purple-400 mb-4">每週票房走勢 (Weekly)</h3>
                                <div className="h-[300px]">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <LineChart data={selectedMovieDetails.history}>
                                            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                                            <XAxis
                                                dataKey="week"
                                                stroke="#9CA3AF"
                                                tickFormatter={(val, index) => {
                                                    const item = selectedMovieDetails?.history[index];
                                                    return item ? getBoxOfficeWeekRange(item.year, item.week).short : `W${val}`;
                                                }}
                                                tick={{ fontSize: 12 }}
                                            />
                                            <YAxis stroke="#9CA3AF" tickFormatter={(val) => `${(val / 10000).toFixed(0)}萬`} width={60} />
                                            <Tooltip
                                                content={({ active, payload }) => {
                                                    if (active && payload && payload.length > 0) {
                                                        const item = payload[0].payload;
                                                        const revenue = payload[0].value as number;
                                                        const tickets = item.weekly_tickets;
                                                        const dateLabel = getBoxOfficeWeekRange(item.year, item.week).full;
                                                        return (
                                                            <div className="bg-[#1F2937] p-3 border border-gray-600 rounded-lg shadow-xl">
                                                                <p className="text-white font-bold mb-2 text-sm">{dateLabel}</p>
                                                                <div className="flex flex-col gap-1 text-sm">
                                                                    <span className="text-blue-400">票房: ${Number(revenue).toLocaleString()}</span>
                                                                    <span className="text-green-400">票數: {tickets ? Number(tickets).toLocaleString() : '無資料'}</span>
                                                                </div>
                                                            </div>
                                                        );
                                                    }
                                                    return null;
                                                }}
                                            />
                                            <Line type="monotone" dataKey="weekly_revenue" stroke="#a855f7" strokeWidth={3} dot={{ r: 4, fill: '#a855f7' }} />
                                        </LineChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>

                            {/* Bar Chart: Cumulative Revenue */}
                            <div className="bg-[#111827] p-4 rounded-lg border border-gray-800">
                                <h3 className="text-lg font-bold text-green-400 mb-4">累積票房增長 (Cumulative)</h3>
                                <div className="h-[300px]">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <BarChart data={selectedMovieDetails.history}>
                                            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                                            <XAxis
                                                dataKey="week"
                                                stroke="#9CA3AF"
                                                tickFormatter={(val, index) => {
                                                    const item = selectedMovieDetails?.history[index];
                                                    return item ? getBoxOfficeWeekRange(item.year, item.week).short : `W${val}`;
                                                }}
                                                tick={{ fontSize: 12 }}
                                            />
                                            <YAxis stroke="#9CA3AF" tickFormatter={(val) => `${(val / 10000).toFixed(0)}萬`} width={60} />
                                            <Tooltip
                                                content={({ active, payload }) => {
                                                    if (active && payload && payload.length > 0) {
                                                        const item = payload[0].payload;
                                                        const revenue = payload[0].value as number;
                                                        const tickets = item.cumulative_tickets;
                                                        const dateLabel = getBoxOfficeWeekRange(item.year, item.week).full;
                                                        return (
                                                            <div className="bg-[#1F2937] p-3 border border-gray-600 rounded-lg shadow-xl">
                                                                <p className="text-white font-bold mb-2 text-sm">{dateLabel}</p>
                                                                <div className="flex flex-col gap-1 text-sm">
                                                                    <span className="text-blue-400">票房: ${Number(revenue).toLocaleString()}</span>
                                                                    <span className="text-green-400">票數: {tickets ? Number(tickets).toLocaleString() : '無資料'}</span>
                                                                </div>
                                                            </div>
                                                        );
                                                    }
                                                    return null;
                                                }}
                                            />
                                            <Bar dataKey="cumulative_revenue" fill="#22c55e" radius={[4, 4, 0, 0]} />
                                        </BarChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
