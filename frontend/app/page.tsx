"use client";
import React, { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import {
  PieChart, Pie, Cell, ResponsiveContainer,
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend
} from 'recharts';
import axios from 'axios';

// --- CONSTANTS ---
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8001";
const COLORS: Record<string, string> = {
  "台灣": "#ef4444", "美國": "#3b82f6", "日本": "#eab308",
  "韓國": "#22c55e", "香港": "#a855f7", "東南亞": "#f97316", "其他": "#9ca3af"
};
const COMPARE_COLORS = ["#a855f7", "#22c55e", "#3b82f6", "#f97316", "#ef4444"];

const getBoxOfficeWeekRange = (year: number, week: number) => {
  if (!year || week === undefined) return { short: `W${week}`, full: `Week ${week}` };

  // Treat week 0 as week 1 (common SQLite strftime quirk)
  const validWeek = week === 0 ? 1 : week;

  // Jan 4th is always in ISO Week 1
  const jan4 = new Date(year, 0, 4);
  const day = jan4.getDay() || 7; // Convert Sun(0) to 7
  const week1Monday = new Date(year, 0, 4 - day + 1);

  // Add weeks
  const targetMonday = new Date(week1Monday.getTime() + (validWeek - 1) * 7 * 24 * 60 * 60 * 1000);
  const targetSunday = new Date(targetMonday.getTime() + 6 * 24 * 60 * 60 * 1000);

  const format = (d: Date) => `${d.getMonth() + 1}/${d.getDate()}`;
  return {
    short: format(targetSunday), // e.g., "12/17" (For X-Axis)
    full: `${format(targetMonday)} ~ ${format(targetSunday)}` // e.g., "12/11 ~ 12/17" (For Tooltip)
  };
};

const formatRevenueAxis = (val: number) => {
  if (val >= 100000000) return `${(val / 100000000).toFixed(1)}億`;
  return `${(val / 10000).toFixed(0)}萬`;
};

export default function Home() {
  // --- STATE ---
  const [activeIndex, setActiveIndex] = useState(0);
  const [movies, setMovies] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [countryData, setCountryData] = useState<any[]>([]);
  const [cityData, setCityData] = useState<any[]>([]);
  const [last4WeeksData, setLast4WeeksData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState("weekly_revenue");

  const debounceTimer = useRef<NodeJS.Timeout | null>(null);

  // Search & Filter States
  const [searchTerm, setSearchTerm] = useState("");
  const [suggestions, setSuggestions] = useState<any[]>([]);
  const [selectedCountry, setSelectedCountry] = useState("所有國家");

  const [selectedMovie, setSelectedMovie] = useState<any>(null);

  // New States for Detailed Modal
  const [selectedMovieDetails, setSelectedMovieDetails] = useState<any>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Box Office Comparison State
  const [compareList, setCompareList] = useState<any[]>([]);
  const [compareData, setCompareData] = useState<any[]>([]);
  const [compareMoviesInfo, setCompareMoviesInfo] = useState<any[]>([]);

  // Dedicated Compare Search State
  const [compareSearch, setCompareSearch] = useState("");
  const [compareSuggestions, setCompareSuggestions] = useState<any[]>([]);

  // Pagination State
  const [currentPage, setCurrentPage] = useState(1);

  const loadCompareData = async (ids: number[]) => {
    if (ids.length === 0) {
      setCompareData([]);
      setCompareMoviesInfo([]);
      return;
    }
    try {
      const res = await axios.get(`http://127.0.0.1:8001/movies/compare`, {
        params: { movie_ids: ids.join(",") }
      });
      setCompareData(res.data.data || []);
      setCompareMoviesInfo(res.data.movies || []);
    } catch (e) {
      console.error("Compare error", e);
    }
  };

  const toggleCompare = (e: React.MouseEvent, movie: any) => {
    e.stopPropagation();
    setCompareList(prev => {
      let newList = [...prev];
      if (newList.some(m => m.id === movie.id)) {
        newList = newList.filter(m => m.id !== movie.id);
      } else {
        if (newList.length >= 5) {
          alert("最多只能比較 5 部電影");
          return prev;
        }
        newList.push(movie);
      }
      const ids = newList.map(m => m.id);
      loadCompareData(ids);
      return newList;
    });
  };

  const removeFromCompare = (id: number) => {
    setCompareList(prev => {
      const newList = prev.filter(m => m.id !== id);
      loadCompareData(newList.map(m => m.id));
      return newList;
    });
  };

  // --- DATA FETCHING ---
  const loadData = async (query = searchTerm, currentSort = sortBy, currentCountry = selectedCountry) => {
    setCurrentPage(1);
    try {
      setLoading(true);
      // 1. Fetch Movies (Search or Default)
      // FORCE Explicit IPv4 URL to prevent Network Errors
      const movieRes = await axios.get(`http://127.0.0.1:8001/movies`, {
        params: {
          search: query,
          sort_by: currentSort,
          country: currentCountry !== "所有國家" ? currentCountry : undefined
        }
      });
      // Fix: API returns { movies: [], total: ... }
      setMovies(movieRes.data.movies || []);

      // 2. Fetch Stats (Only if not searching, to keep context)
      if (!query) {
        // FORCE Explicit IPv4 URL to prevent Network Errors
        const dashboardRes = await axios.get(`http://127.0.0.1:8001/dashboard-stats`);
        const d = dashboardRes.data;
        setStats(d.kpis);

        // Process Country Data for Pie Chart
        // Fix: item.revenue, not total_revenue
        const processedCountries = d.market_share.map((item: any) => ({
          name: item.country,
          value: item.revenue
        }));
        setCountryData(processedCountries);
        setCityData(d.city_distribution || []); // Mock or Real

        // Fix: API returns four_week_trend (now includes year, week, revenue)
        const trendData = d.four_week_trend || d.trend || [];
        setLast4WeeksData(trendData.map((item: any) => ({
          name: item.week_label || `W${item.week}`,
          year: item.year,
          week: item.week,
          revenue: item.revenue
        })));
      }
    } catch (error) {
      console.error("Data load failed:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setSearchTerm(val);

    // Clear the previous timer if the user keeps typing
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    if (val.trim().length > 0) {
      // Wait 400ms after the user STOPS typing before hitting the API
      debounceTimer.current = setTimeout(async () => {
        try {
          // FORCE Explicit IPv4 URL to prevent Network Errors
          const res = await axios.get(`http://127.0.0.1:8001/movies`, {
            params: { search: val }
          });
          setSuggestions(res.data.movies ? res.data.movies.slice(0, 6) : []);
        } catch (error) {
          console.error("Autocomplete Error:", error);
          // Silently fail autocomplete rather than crashing the UI
        }
      }, 400);
    } else {
      setSuggestions([]);
      loadData("", sortBy, selectedCountry);
    }
  };

  const handleMovieClick = async (movieId: number) => {
    try {
      const res = await axios.get(`${API_BASE}/movies/${movieId}/details`);
      setSelectedMovieDetails(res.data);
      setIsModalOpen(true);
    } catch (error) {
      console.error("Failed to fetch movie details:", error);
    }
  };

  const totalMarketValue = countryData.reduce((sum, item) => sum + (item.value || 0), 0);
  const activeItem = countryData[activeIndex] || { name: '無資料', value: 0 };
  const activePercent = totalMarketValue > 0 ? ((activeItem.value / totalMarketValue) * 100).toFixed(1) : "0.0";

  const ITEMS_PER_PAGE = 15;
  const totalPages = Math.ceil(movies.length / ITEMS_PER_PAGE);
  const paginatedMovies = movies.slice((currentPage - 1) * ITEMS_PER_PAGE, currentPage * ITEMS_PER_PAGE);

  // --- RENDER ---
  return (
    <div className="min-h-screen bg-[#111827] text-white p-8 font-sans">
      {/* HEADER */}
      <header className="mb-8 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-purple-600 rounded-lg flex items-center justify-center">
            <span className="text-2xl">🎬</span>
          </div>
          <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-pink-600">
            台灣電影票房戰情室
          </h1>
        </div>
        <div className="text-sm text-gray-400 flex items-center">
          <Link href="/" className="mr-6 text-purple-400 hover:text-purple-300 transition flex items-center gap-1 font-medium">↗ 即時戰情</Link>
          <Link href="/statistics" className="hover:text-white transition flex items-center gap-1">📊 票房統計</Link>
        </div>
      </header>

      {/* SECTION TITLE: MONTHLY OVERVIEW */}
      <div className="mb-6 flex items-center gap-3">
        <div className="w-1.5 h-8 bg-purple-500 rounded-full shadow-[0_0_15px_rgba(168,85,247,0.6)]"></div>
        <h2 className="text-2xl font-bold text-white tracking-wide">本月概況</h2>
      </div>

      {/* MAIN DASHBOARD GRID (3 Cols) */}
      <div className="grid grid-cols-12 gap-6 mb-10">

        {/* COL 1: KPI CARDS (Span 3) */}
        <div className="col-span-12 md:col-span-3 flex flex-col gap-4">
          <div className="bg-[#1F2937] p-5 rounded-xl border border-gray-700/50 hover:border-purple-500/50 transition-all group relative overflow-hidden">
            <div className="absolute top-0 right-0 w-20 h-20 bg-purple-500/10 rounded-bl-full -mr-4 -mt-4 transition-transform group-hover:scale-110" />
            <h3 className="text-gray-400 text-sm font-medium mb-1">本週票房</h3>
            <p className="text-3xl font-bold text-white group-hover:text-purple-400 transition-colors font-mono">
              ${stats?.current_week_total ? (stats.current_week_total / 10000).toFixed(0) : 0}萬
            </p>
          </div>
          <div className="bg-[#1F2937] p-5 rounded-xl border border-gray-700/50 hover:border-green-500/50 transition-all group relative overflow-hidden">
            <div className="absolute top-0 right-0 w-20 h-20 bg-green-500/10 rounded-bl-full -mr-4 -mt-4 transition-transform group-hover:scale-110" />
            <h3 className="text-gray-400 text-sm font-medium mb-1">本月總票房</h3>
            <p className="text-3xl font-bold text-white group-hover:text-green-400 transition-colors font-mono">
              ${stats?.current_month_total ? (stats.current_month_total / 10000).toFixed(0) : 0}萬
            </p>
          </div>
          <div className="bg-[#1F2937] p-5 rounded-xl border border-gray-700/50 hover:border-blue-500/50 transition-all group">
            <h3 className="text-gray-400 text-sm font-medium mb-1">本週新片</h3>
            <p className="text-3xl font-bold text-white group-hover:text-blue-400 transition-colors">
              {stats?.weekly_new_releases || 0} <span className="text-sm font-normal text-gray-500">部</span>
            </p>
          </div>
          <div className="bg-[#1F2937] p-5 rounded-xl border border-gray-700/50 hover:border-red-500/50 transition-all group">
            <h3 className="text-gray-400 text-sm font-medium mb-1">本月新片</h3>
            <p className="text-3xl font-bold text-white group-hover:text-red-400 transition-colors">
              {stats?.monthly_new_releases || 0} <span className="text-sm font-normal text-gray-500">部</span>
            </p>
          </div>
        </div>

        {/* COL 2: DONUT CHART (Span 5) */}
        <div className="col-span-12 md:col-span-5 bg-[#1F2937] rounded-xl p-6 border border-gray-700/50 flex flex-col items-center justify-center relative min-h-[420px]">
          <h3 className="absolute top-6 left-6 text-lg font-bold text-gray-200 flex items-center gap-2">
            當月銷售國別市佔率
            <span className="text-xs font-normal text-gray-500 px-2 py-1 bg-gray-800 rounded">Interactive</span>
          </h3>

          <div className="w-full h-[320px] mt-8 relative flex items-center justify-center">
            {/* CSS Overlay - Always works even if slice is 0% */}
            <div className="absolute flex flex-col items-center justify-center pointer-events-none mt-2 z-10">
              <span className="text-2xl font-bold text-white">{activeItem.name}</span>
              <span className="text-sm text-gray-400 mt-1">${(activeItem.value / 10000).toFixed(0)}萬</span>
              <span className="text-xs text-gray-500 mt-1">({activePercent}%)</span>
            </div>

            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={countryData}
                  cx="50%" cy="50%"
                  innerRadius={80} outerRadius={110}
                  dataKey="value"
                  onMouseEnter={(_, index) => setActiveIndex(index)}
                  stroke="none"
                  isAnimationActive={false}
                >
                  {countryData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[entry.name] || '#999'} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </div>
          {/* Legend */}
          <div className="mt-2 flex flex-wrap justify-center gap-3 px-4 w-full">
            {countryData.map((entry, index) => (
              <div
                key={entry.name}
                onMouseEnter={() => setActiveIndex(index)}
                className={`cursor-pointer flex items-center gap-2 px-3 py-1.5 rounded-full border transition-all ${activeIndex === index ? 'bg-white/10 border-white/30 text-white scale-105' : 'border-transparent text-gray-400 hover:bg-white/5'}`}
              >
                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[entry.name] || '#999' }} />
                <span className="text-xs font-bold">{entry.name}</span>
              </div>
            ))}
          </div>
        </div>

        {/* COL 3: BAR CHART (Span 4) */}
        <div className="col-span-12 md:col-span-4 bg-[#1F2937] rounded-xl p-6 border border-gray-700/50 min-h-[420px] flex flex-col">
          <h3 className="text-lg font-bold text-gray-200 mb-6">前四週銷售金額趨勢</h3>
          <div className="flex-1 w-full min-h-[200px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={last4WeeksData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
                <XAxis
                  dataKey="week"
                  stroke="#9CA3AF"
                  tick={{ fontSize: 12 }}
                  tickLine={false}
                  axisLine={false}
                  dy={10}
                  tickFormatter={(val, index) => {
                    const item = last4WeeksData[index];
                    if (item && item.year && item.week) {
                      return getBoxOfficeWeekRange(item.year, item.week).short;
                    }
                    return `W${val}`;
                  }}
                />
                <YAxis stroke="#9CA3AF" tick={{ fontSize: 12 }} tickLine={false} axisLine={false} tickFormatter={formatRevenueAxis} width={80} />
                <Tooltip
                  cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                  content={({ active, payload }) => {
                    if (active && payload && payload.length > 0) {
                      const item = payload[0].payload;
                      const revenue = payload[0].value as number;
                      const dateLabel = (item.year && item.week)
                        ? getBoxOfficeWeekRange(item.year, item.week).full
                        : item.name;
                      return (
                        <div className="bg-[#111827] p-3 border border-gray-600 rounded-lg shadow-xl">
                          <p className="text-white font-bold mb-2 text-sm">{dateLabel}</p>
                          <div className="flex flex-col gap-1 text-sm">
                            <span className="text-purple-400">票房: ${Number(revenue).toLocaleString()}</span>
                          </div>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Bar dataKey="revenue" fill="#8b5cf6" radius={[6, 6, 0, 0]} barSize={40}>
                  {last4WeeksData.map((entry, index) => (
                    <Cell key={`bar-${index}`} fill={`rgba(139, 92, 246, ${0.5 + (index / last4WeeksData.length) * 0.5})`} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* SECTION 2: REGIONAL STATS (Full Width) */}
      <div className="bg-[#1F2937] rounded-xl p-6 mb-8 border border-gray-700/50">
        <div className="mb-6">
          <h3 className="text-xl font-bold text-white mb-1">全台地區票房分佈</h3>
          <p className="text-gray-400 text-sm">各地區上映場次與票房統計</p>
        </div>
        <div className="h-[300px]">
          {cityData && cityData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={cityData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
                <XAxis dataKey="name" stroke="#9CA3AF" tickLine={false} axisLine={false} />
                <YAxis stroke="#9CA3AF" tickLine={false} axisLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#111827', border: 'none', borderRadius: '8px', color: '#fff' }}
                  cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {cityData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={[`#ef4444`, `#3b82f6`, `#eab308`, `#22c55e`, `#a855f7`, `#f97316`][index % 6]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="w-full h-full flex items-center justify-center text-gray-500">
              目前無各地區票房數據 (No regional data available)
            </div>
          )}
        </div>
      </div>

      {/* SECTION 3: SEARCH & RANKING */}
      <div className="mb-8">
        <div className="flex gap-4 mb-6 relative z-30">
          {/* Search Bar with Autocomplete */}
          <div className="flex-1 bg-[#2D3748] rounded-lg flex items-center px-4 border border-gray-600 focus-within:border-purple-500 transition-all relative">
            <span className="text-gray-400 mr-2 text-xl">🔍</span>
            <input
              type="text"
              value={searchTerm}
              onChange={handleSearchChange}
              placeholder="搜尋電影名稱 (例如：陽光)..."
              className="bg-transparent border-none outline-none text-white w-full h-12 placeholder-gray-500"
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  setSuggestions([]);
                  loadData(searchTerm, sortBy, selectedCountry);
                }
              }}
            />
            {/* Autocomplete Dropdown */}
            {suggestions.length > 0 && (
              <ul className="absolute top-[110%] left-0 w-full bg-[#1F2937] border border-gray-600 rounded-lg shadow-2xl z-50 overflow-hidden">
                {suggestions.map((s, idx) => (
                  <li
                    key={idx}
                    onClick={() => {
                      setSearchTerm(s.name);
                      setSuggestions([]);
                      loadData(s.name, sortBy, selectedCountry);
                    }}
                    className="px-4 py-3 hover:bg-purple-600/50 cursor-pointer text-white border-b border-gray-700/50 last:border-0 flex justify-between items-center transition-colors"
                  >
                    <span className="font-bold">{s.name}</span>
                    <span className="text-xs text-gray-400 bg-black/20 px-2 py-1 rounded">{s.release_date}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
          {/* Dynamic Country Dropdown */}
          <select
            value={selectedCountry}
            onChange={(e) => {
              const val = e.target.value;
              setSelectedCountry(val);
              loadData(searchTerm, sortBy, val);
            }}
            className="bg-[#2D3748] text-white px-6 rounded-lg border border-gray-600 outline-none hover:border-purple-500 cursor-pointer appearance-none"
          >
            <option value="所有國家">所有國家</option>
            {countryData.map(c => (
              <option key={c.name} value={c.name}>{c.name}</option>
            ))}
          </select>
          {/* Sorting Buttons */}
          <button
            onClick={() => { setSortBy("weekly_revenue"); loadData(searchTerm, "weekly_revenue", selectedCountry); }}
            className={`px-8 rounded-lg font-bold transition-all ${sortBy === 'weekly_revenue' ? 'bg-purple-600 text-white shadow-lg shadow-purple-900/50 active:scale-95' : 'bg-[#2D3748] text-gray-300 hover:bg-[#374151] border border-gray-600'}`}
          >
            本週票房
          </button>
          <button
            onClick={() => { setSortBy("cumulative_revenue"); loadData(searchTerm, "cumulative_revenue", selectedCountry); }}
            className={`px-6 rounded-lg font-medium transition-all ${sortBy === 'cumulative_revenue' ? 'bg-purple-600 text-white shadow-lg shadow-purple-900/50 active:scale-95' : 'bg-[#2D3748] text-gray-300 hover:bg-[#374151] border border-gray-600'}`}
          >
            累積票房
          </button>
        </div>
        {/* RANKING LIST */}
        <div className="bg-[#1F2937]/50 rounded-xl p-8 border border-gray-700/30 min-h-[300px]">
          <h2 className="text-2xl font-bold mb-6 text-white flex items-center gap-2">
            本週票房排行
            {movies.length > 0 && <span className="text-sm font-normal text-gray-500 bg-gray-800 px-2 py-1 rounded-full">{movies.length} Results</span>}
          </h2>

          <div className="flex flex-col gap-0">
            <div className="grid grid-cols-12 text-gray-500 text-xs uppercase tracking-wider font-semibold pb-4 border-b border-gray-700 mb-2 px-4">
              <div className="col-span-1">排名</div>
              <div className="col-span-5">片名</div>
              <div className="col-span-2">出品國</div>
              <div className="col-span-2">上映日期</div>
              <div className="col-span-2 text-right">{sortBy === "weekly_revenue" ? "週票房" : "累積票房"}</div>
            </div>

            {loading ? (
              <div className="text-center py-20 text-gray-500 animate-pulse">載入數據中 Loading...</div>
            ) : movies.length > 0 ? (
              paginatedMovies.map((movie, index) => {
                const isComparing = compareList.some(m => m.id === movie.id);
                const absoluteIndex = (currentPage - 1) * ITEMS_PER_PAGE + index;
                return (
                  <div key={movie.id} onClick={() => handleMovieClick(movie.id)} className="grid grid-cols-12 items-center py-4 border-b border-gray-700/50 hover:bg-white/5 transition-colors px-4 rounded-lg group cursor-pointer relative">
                    <div className="col-span-1">
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-sm shadow-md ${absoluteIndex < 3 ? 'bg-gradient-to-br from-yellow-400 to-orange-500 text-black' : 'bg-gray-700 text-gray-300'}`}>
                        {absoluteIndex + 1}
                      </div>
                    </div>
                    <div className="col-span-4 lg:col-span-5 font-bold text-lg text-white group-hover:text-purple-400 transition-colors truncate pr-4">
                      {movie.name}
                      <div className="text-xs text-gray-500 font-normal truncate">{movie.english_name}</div>
                    </div>
                    <div className="col-span-2 text-gray-400 text-sm flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-gray-600 hidden sm:inline-block"></span>
                      <span className="truncate">{movie.country}</span>
                    </div>
                    <div className="col-span-2 text-gray-400 text-sm font-mono truncate">{movie.release_date}</div>
                    <div className="col-span-3 lg:col-span-2 text-right font-mono tracking-tight flex items-center justify-end gap-3">
                      <div className="flex flex-col items-end">
                        <span className="text-green-400 font-bold text-lg truncate">
                          {sortBy === 'cumulative_revenue'
                            ? (movie.cumulative_revenue ? `$${String(movie.cumulative_revenue).replace(/,/g, '')}`.replace(/\B(?=(\d{3})+(?!\d))/g, ",") : <span className="text-gray-500 text-sm font-sans">無資料</span>)
                            : (movie.weekly_revenue ? `$${String(movie.weekly_revenue).replace(/,/g, '')}`.replace(/\B(?=(\d{3})+(?!\d))/g, ",") : <span className="text-gray-500 text-sm font-sans">無資料</span>)
                          }
                        </span>
                        <span className="text-xs text-gray-400">票數: {movie.tickets ? movie.tickets.toLocaleString() : '未提供'}</span>
                      </div>
                      <button
                        onClick={(e) => toggleCompare(e, movie)}
                        className={`text-xs px-2 py-1 rounded-md border transition-colors whitespace-nowrap ${isComparing ? 'bg-orange-500/20 border-orange-500 text-orange-400' : 'bg-gray-800 border-gray-600 text-gray-400 hover:border-white hover:text-white'}`}
                        title={isComparing ? "取消比較" : "加入比較"}
                      >
                        {isComparing ? '❌' : '+ 比較'}
                      </button>
                    </div>
                  </div>
                )
              })
            ) : (
              <div className="text-center py-20 text-gray-500 flex flex-col items-center gap-4">
                <span className="text-6xl opacity-20">🦖</span>
                <p>沒有找到符合的電影資料</p>
                <button onClick={() => loadData("")} className="text-purple-400 hover:text-purple-300 underline text-sm">清除搜尋</button>
              </div>
            )}
          </div>

          {totalPages > 1 && (
            <div className="flex justify-center items-center gap-4 mt-6 pb-4">
              <button
                disabled={currentPage === 1}
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                className="px-4 py-2 bg-[#2D3748] text-white rounded-lg disabled:opacity-50 hover:bg-[#374151] transition"
              >
                上一頁
              </button>
              <span className="text-gray-400 text-sm">第 {currentPage} 頁 / 共 {totalPages} 頁</span>
              <button
                disabled={currentPage === totalPages}
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                className="px-4 py-2 bg-[#2D3748] text-white rounded-lg disabled:opacity-50 hover:bg-[#374151] transition"
              >
                下一頁
              </button>
            </div>
          )}
        </div>
      </div>

      {/* SECTION 4: BOX OFFICE COMPARISON */}
      <div className="bg-[#1F2937] rounded-xl p-6 mb-8 border border-gray-700/50 animate-fadeIn relative z-10 w-full min-h-[400px]">
        <div className="mb-6 flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
          <div>
            <h3 className="text-xl font-bold text-white mb-2 flex items-center gap-2">
              <span className="text-orange-500">📊</span> 票房趨勢比較分析 (Trend Comparison)
            </h3>

            <div className="relative mb-4 w-full md:w-96">
              <div className="flex bg-[#2D3748] rounded-lg items-center px-4 border border-gray-600 focus-within:border-purple-500">
                <span className="text-gray-400 mr-2">➕</span>
                <input
                  type="text"
                  value={compareSearch}
                  onChange={async (e) => {
                    const val = e.target.value;
                    setCompareSearch(val);
                    if (val.trim().length > 0) {
                      try {
                        const res = await axios.get(`http://127.0.0.1:8001/movies`, { params: { search: val } });
                        setCompareSuggestions(res.data.movies ? res.data.movies.slice(0, 5) : []);
                      } catch (e) {
                        console.error(e);
                      }
                    } else {
                      setCompareSuggestions([]);
                    }
                  }}
                  placeholder="搜尋並加入比較 (例如：阿凡達)..."
                  className="bg-transparent border-none outline-none text-white w-full h-10 text-sm"
                />
              </div>
              {compareSuggestions.length > 0 && (
                <ul className="absolute top-full left-0 w-full bg-[#1F2937] border border-gray-600 rounded-lg shadow-2xl z-50 overflow-hidden mt-1 max-h-60 overflow-y-auto">
                  {compareSuggestions.map(s => (
                    <li key={s.id}
                      onClick={() => {
                        if (compareList.length < 5 && !compareList.some(m => m.id === s.id)) {
                          toggleCompare({ stopPropagation: () => { } } as React.MouseEvent, s);
                        }
                        setCompareSearch("");
                        setCompareSuggestions([]);
                      }}
                      className="px-4 py-2 hover:bg-purple-600/50 cursor-pointer text-white text-sm border-b border-gray-700/50 last:border-0 flex justify-between"
                    >
                      <span className="truncate pr-2">{s.name}</span>
                      <span className="text-gray-400 flex-shrink-0">{s.release_date}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
          <div className="text-sm text-gray-400 bg-gray-800 px-3 py-1 rounded-full whitespace-nowrap">
            選擇: <span className="text-white font-bold">{compareList.length}</span>/5
          </div>
        </div>

        {compareList && compareList.length > 0 ? (
          <div className="flex flex-col gap-6">
            <div className="flex flex-wrap gap-2">
              {compareList.map((movie, index) => (
                <div key={movie.id} style={{ borderColor: COMPARE_COLORS[index % 5], color: COMPARE_COLORS[index % 5] }} className="bg-gray-800/50 px-3 py-1 rounded-full text-sm flex items-center gap-2 shadow-sm font-bold border">
                  <span className="max-w-[150px] truncate">{movie.name}</span>
                  <button onClick={() => removeFromCompare(movie.id)} className="hover:text-white ml-2 opacity-70 font-bold">&times;</button>
                </div>
              ))}
            </div>

            {compareData.length > 0 ? (
              <div className="space-y-4">
                <div className="bg-[#111827] p-4 rounded-lg border border-gray-800 min-h-[400px]">
                  <h4 className="text-sm font-bold text-gray-400 mb-6 text-center uppercase tracking-widest">累積票房成長趨勢 (Cumulative Revenue)</h4>
                  <div className="h-[350px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={compareData} margin={{ top: 10, right: 30, left: 20, bottom: 20 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
                        <XAxis
                          dataKey="relative_week"
                          stroke="#9CA3AF"
                          tickFormatter={(v) => `上${v}週`}
                          dy={10}
                          tick={{ fill: '#9CA3AF', fontSize: 12 }}
                        />
                        <YAxis
                          yAxisId="left"
                          stroke="#9CA3AF"
                          tickFormatter={formatRevenueAxis}
                          width={60}
                          tick={{ fill: '#9CA3AF', fontSize: 12 }}
                        />
                        <Tooltip
                          cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                          content={({ active, payload, label }) => {
                            if (active && payload && payload.length > 0) {
                              return (
                                <div className="bg-[#1F2937] p-4 border border-gray-600 rounded-lg shadow-xl min-w-[200px]">
                                  <p className="text-white font-bold mb-3 text-sm border-b border-gray-600 pb-2">上映第 {label} 週</p>
                                  {payload.map((entry: any, index: number) => {
                                    const movieId = String(entry.dataKey).split('_')[0];
                                    const ticketsKey = `${movieId}_tickets`;
                                    const tickets = entry.payload[ticketsKey];
                                    return (
                                      <div key={index} className="text-sm mb-2 flex flex-col gap-0.5">
                                        <span className="font-bold" style={{ color: entry.color }}>{entry.name}</span>
                                        <span className="text-blue-300 ml-2">票房: ${Number(entry.value).toLocaleString()}</span>
                                        <span className="text-green-300 ml-2">票數: {tickets ? Number(tickets).toLocaleString() : '無資料'}</span>
                                      </div>
                                    );
                                  })}
                                </div>
                              );
                            }
                            return null;
                          }}
                        />
                        <Legend verticalAlign="bottom" height={36} wrapperStyle={{ paddingTop: "20px" }} />
                        {compareMoviesInfo.map((m, i) => (
                          <Line
                            key={m.id}
                            yAxisId="left"
                            type="monotone"
                            dataKey={`${m.id}_cumulative`}
                            name={m.name}
                            stroke={COMPARE_COLORS[i % 5]}
                            strokeWidth={3}
                            dot={{ r: 4, fill: COMPARE_COLORS[i % 5], strokeWidth: 0 }}
                            activeDot={{ r: 6, stroke: '#fff', strokeWidth: 2 }}
                          />
                        ))}
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-20 text-gray-500 animate-pulse bg-[#111827] rounded-lg border border-gray-800">
                <span className="text-3xl opacity-50 block mb-2">⏳</span>
                正在計算趨勢數據...
              </div>
            )}
          </div>
        ) : (
          <div className="h-[300px] w-full flex flex-col items-center justify-center text-gray-500 border-2 border-dashed border-gray-700 rounded-lg bg-[#111827]/50 mt-4">
            <span className="text-4xl mb-3">📈</span>
            <p>目前尚無比較項目</p>
            <p className="text-sm mt-1">請從上方排行榜點擊「+ 比較」，或使用上方搜尋框加入電影</p>
          </div>
        )}
      </div>

      {/* MOVIE DETAIL MODAL */}
      {
        isModalOpen && selectedMovieDetails && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4" onClick={() => setIsModalOpen(false)}>
            <div className="bg-[#1F2937] rounded-xl w-full max-w-5xl max-h-[90vh] overflow-y-auto border border-gray-700 shadow-2xl" onClick={e => e.stopPropagation()}>
              {/* Header */}
              <div className="flex justify-between items-start p-6 border-b border-gray-700 sticky top-0 bg-[#1F2937] z-10">
                <div>
                  <h2 className="text-3xl font-bold text-white mb-2">{selectedMovieDetails.info.name}</h2>
                  <div className="flex gap-4 text-sm text-gray-400 mb-4">
                    <span>發行日期: {selectedMovieDetails.info.release_date}</span>
                    <span>國家: {selectedMovieDetails.info.country}</span>
                  </div>

                  {/* INJECT THIS NEW METADATA BLOCK */}
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
                        <YAxis stroke="#9CA3AF" tickFormatter={formatRevenueAxis} width={80} />
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
        )
      }
    </div>
  );
}
