'use client';

import { useState, useEffect } from 'react';
import Navbar from '@/components/Navbar';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Search, Plus, X } from 'lucide-react';
import axios from 'axios';

// --- Types ---
interface Movie {
    id: number;
    name: string;
    release_date: string;
}

interface TrajectoryData {
    id: number;
    name: string;
    data: {
        week_num: number;
        revenue: number;
        cumulative: number;
        date: string;
    }[];
}

const API_BASE_URL = 'http://127.0.0.1:8001';

export default function ComparePage() {
    // Search State
    const [query, setQuery] = useState('');
    const [searchResults, setSearchResults] = useState<Movie[]>([]);
    const [isSearching, setIsSearching] = useState(false);

    // Selection State
    const [selectedMovies, setSelectedMovies] = useState<Movie[]>([]);
    const [trajectoryData, setTrajectoryData] = useState<TrajectoryData[]>([]);
    const [loadingData, setLoadingData] = useState(false);

    // 1. Search Logic
    useEffect(() => {
        const search = async () => {
            if (query.length < 1) {
                setSearchResults([]);
                return;
            }
            setIsSearching(true);
            try {
                // Using existing /movies endpoint for search
                const res = await axios.get(`${API_BASE_URL}/movies`, {
                    params: { q: query, limit: 5 }
                });
                setSearchResults(res.data.movies);
            } catch (err) {
                console.error(err);
            } finally {
                setIsSearching(false);
            }
        };

        const timeoutId = setTimeout(search, 300);
        return () => clearTimeout(timeoutId);
    }, [query]);

    // 2. Fetch Comparison Data
    useEffect(() => {
        const fetchTrajectories = async () => {
            if (selectedMovies.length === 0) {
                setTrajectoryData([]);
                return;
            }

            setLoadingData(true);
            try {
                const ids = selectedMovies.map(m => m.id).join(',');
                const res = await axios.get(`${API_BASE_URL}/movie-trajectory`, {
                    params: { movie_ids: ids }
                });
                setTrajectoryData(res.data);
            } catch (err) {
                console.error("Error fetching trajectories:", err);
            } finally {
                setLoadingData(false);
            }
        };

        fetchTrajectories();
    }, [selectedMovies]);

    // Helpers
    const addMovie = (movie: Movie) => {
        if (!selectedMovies.find(m => m.id === movie.id)) {
            if (selectedMovies.length >= 5) {
                alert("最多比較 5 部電影");
                return;
            }
            setSelectedMovies([...selectedMovies, movie]);
        }
        setQuery('');
        setSearchResults([]);
    };

    const removeMovie = (id: number) => {
        setSelectedMovies(selectedMovies.filter(m => m.id !== id));
    };

    // Chart Data Preparation
    // We need to merge all series into one array of objects keyed by 'week_num'
    // [{ week: 1, 'MovieA': 100, 'MovieB': 200 }, { week: 2, ... }]
    const chartData = [];
    const maxWeeks = Math.max(...trajectoryData.map(t => t.data.length), 0);

    for (let w = 1; w <= maxWeeks; w++) {
        const point: any = { week: w };
        trajectoryData.forEach(t => {
            const weekData = t.data.find(d => d.week_num === w);
            if (weekData) {
                point[t.name] = weekData.revenue; // Or cumulative? Let's use weekly revenue for trajectory
            }
        });
        chartData.push(point);
    }

    const COLORS = ['#F87171', '#60A5FA', '#FBBF24', '#34D399', '#A78BFA'];

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
            <Navbar />

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">

                {/* Header & Search */}
                <div className="bg-white/10 backdrop-blur-md rounded-2xl p-8 border border-white/20 shadow-2xl">
                    <h1 className="text-3xl font-bold text-white mb-6">電影票房軌跡比較</h1>

                    {/* Search Bar */}
                    <div className="relative max-w-xl">
                        <div className="relative">
                            <input
                                type="text"
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                placeholder="搜尋電影加入比較..."
                                className="w-full bg-black/30 border border-white/20 text-white rounded-xl py-3 pl-12 pr-4 focus:outline-none focus:ring-2 focus:ring-purple-500"
                            />
                            <Search className="absolute left-4 top-3.5 text-gray-400 w-5 h-5" />
                        </div>

                        {/* Search Results Dropdown */}
                        {searchResults.length > 0 && (
                            <div className="absolute top-full left-0 right-0 mt-2 bg-slate-800 border border-white/10 rounded-xl shadow-2xl z-50 overflow-hidden">
                                {searchResults.map(movie => (
                                    <button
                                        key={movie.id}
                                        onClick={() => addMovie(movie)}
                                        className="w-full text-left px-4 py-3 hover:bg-white/10 text-white flex justify-between items-center transition-colors border-b border-white/5 last:border-0"
                                    >
                                        <span className="font-medium">{movie.name}</span>
                                        <span className="text-sm text-gray-400">{movie.release_date}</span>
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Selected Tags */}
                    <div className="flex flex-wrap gap-3 mt-6">
                        {selectedMovies.map((movie, idx) => (
                            <div key={movie.id} className="flex items-center gap-2 bg-white/10 px-4 py-2 rounded-full border border-white/20">
                                <span className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[idx % COLORS.length] }}></span>
                                <span className="text-white font-medium">{movie.name}</span>
                                <button onClick={() => removeMovie(movie.id)} className="text-gray-400 hover:text-white">
                                    <X className="w-4 h-4" />
                                </button>
                            </div>
                        ))}
                        {selectedMovies.length === 0 && (
                            <div className="text-gray-400 italic">尚未選擇電影</div>
                        )}
                    </div>
                </div>

                {/* Trajectory Chart */}
                {selectedMovies.length > 0 && (
                    <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-white/20 shadow-2xl">
                        <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
                            票房走勢 (週票房 Widget)
                        </h2>

                        <div className="h-[500px] w-full">
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                                    <XAxis
                                        dataKey="week"
                                        stroke="#e9d5ff"
                                        label={{ value: '上映週次 (Release Week)', position: 'insideBottom', offset: -5, fill: '#e9d5ff' }}
                                    />
                                    <YAxis
                                        stroke="#e9d5ff"
                                        tickFormatter={(value) => `${(value / 10000).toFixed(0)}萬`}
                                        label={{ value: '週票房', angle: -90, position: 'insideLeft', fill: '#e9d5ff' }}
                                    />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: 'rgba(0,0,0,0.9)', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '8px' }}
                                        formatter={(value: any, name: any) => [`$${value.toLocaleString()}`, name]}
                                        labelFormatter={(label) => `第 ${label} 週`}
                                    />
                                    <Legend />
                                    {selectedMovies.map((movie, idx) => (
                                        <Line
                                            key={movie.id}
                                            type="monotone"
                                            dataKey={movie.name}
                                            stroke={COLORS[idx % COLORS.length]}
                                            strokeWidth={3}
                                            dot={{ r: 4 }}
                                            activeDot={{ r: 6 }}
                                        />
                                    ))}
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                )}

            </main>
        </div>
    );
}
