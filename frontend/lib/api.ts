import axios from 'axios';

const api = axios.create({
    baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8001',
    timeout: 10000,
});

export interface Movie {
    id: number;
    name: string;
    release_date: string | null;
    distributor: string | null;
    country: string | null;
    total_revenue: number;
    weekly_revenue: number;
    theater_count: number;
    is_active: boolean;
}

export interface PaginatedMoviesResponse {
    movies: Movie[];
    total: number;
    page: number;
    limit: number;
    total_pages: number;
}

export interface MarketShareRegion {
    region: string;
    count: number;
}

export interface MarketShareResponse {
    date: string;
    market_share: MarketShareRegion[];
}

export interface MovieFilters {
    q?: string;
    country?: string;
    sort_by?: 'weekly_revenue' | 'total_revenue';
    year?: number;
    week?: number;
}

export interface WeekOption {
    year: number;
    week: number;
    label: string;
}

export const fetchMovies = async (page = 1, limit = 20, filters?: MovieFilters): Promise<PaginatedMoviesResponse> => {
    const response = await api.get('/movies', {
        params: {
            page,
            limit,
            ...filters
        }
    });
    return response.data;
};

export const fetchMarketShare = async (): Promise<MarketShareResponse> => {
    const response = await api.get('/dashboard/market-share');
    return response.data;
};


export interface DashboardStats {
    market_share: Array<{ country: string; revenue: number }>;
    four_week_trend: Array<{ week: string; revenue: number; date: string }>;
    kpis: {
        current_week_total: number;
        current_month_total: number;
        active_movie_count: number;
        weekly_new_releases: number;
        monthly_new_releases: number;
    };
}

export const fetchDashboardStats = async (): Promise<DashboardStats> => {
    const response = await api.get('/dashboard-stats');
    return response.data;
};

// Legacy stats endpoint (still used by footer) - RENAMED to avoid conflict
export interface FooterStats {
    active_movie_count: number;
    weekly_total_revenue: number;
    monthly_new_releases: number;
}

export const fetchFooterStats = async (): Promise<FooterStats> => {
    const response = await api.get('/stats');
    return response.data;
};

// NEW Market Statistics Page API
export interface MarketStat {
    year: number;
    week: number;
    start_date: string;
    end_date: string;
    total_revenue: number;
    movie_count: number;
    top_movie: string;
    growth_rate: number;
}

export const fetchMarketGrowthStats = async (): Promise<MarketStat[]> => {
    const response = await api.get('/market-stats');
    return response.data;
};

export const fetchMovieDetail = async (movieId: number) => {
    const response = await api.get(`/movies/${movieId}`);
    return response.data;
};

export const fetchAvailableWeeks = async (): Promise<WeekOption[]> => {
    const response = await api.get('/weeks');
    return response.data;
};

// NEW: Interactive Period Report API
export interface PeriodStatsResponse {
    summary: {
        start_date: string;
        end_date: string;
        total_revenue: number;
        growth_rate: number;
        movie_count: number;
    };
    rankings: Array<{
        rank: number;
        id?: number;
        name: string;
        revenue: number;
        tickets?: number | null;
        release_date: string | null;
    }>;
}

export const fetchPeriodStats = async (type: 'week' | 'month' | 'year' | 'all_time', year: number, number?: number): Promise<PeriodStatsResponse> => {
    const response = await api.get('/period-stats', {
        params: { type, year, number }
    });
    return response.data;
};

export default api;
