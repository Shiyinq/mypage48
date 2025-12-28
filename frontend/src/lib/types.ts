export interface Ticket {
    _id: string;
    user_id: string | null;
    ticket_id: string;
    event: {
        title: string;
        date: string; // YYYY-MM-DD
        day: string;
        time: string;
        gate_open?: string;
        venue: string;
    };
    seat: {
        section: string;
        number: string | number;
    };
    price: number;
    currency: string;
    rules: {
        refund_allowed: boolean;
        exchange_allowed: boolean;
    };
    created_at: string;
    updated_at: string;
    imageUrl?: string; // Kept for local UI display functionality
    notes?: string; // User's personal notes/diary for the show
    two_shot?: {
        imageUrl?: string;
        member_name: string;
        type: 'Roulette' | 'Birthday';
        price: number;
    };
}

export type ViewState = 'DASHBOARD' | 'UPLOAD' | 'HISTORY' | 'SHOWS' | 'ACHIEVEMENTS' | 'PROFILE' | 'MEMORIES' | 'TOP2SHOT';

export interface AnalysisResult {
    title: string;
    date: string;
    time: string;
    gate_open: string;
    day: string;
    section: string;
    number: string;
    price: number;
    ticket_id: string;
}

// Auth Types
export interface UserOshi {
    name: string;
    nickname: string;
    generation: string;
    profilePicture: string;
    catchphrase: string;
    socials?: {
        twitter: string | null;
        instagram: string | null;
        tiktok: string | null;
        threads: string | null;
        showroom: string | null;
        idn_app: string | null;
    } | null;
}

export interface User {
    userId?: string;
    email: string;
    username: string;
    name?: string;
    memberId?: string;
    ofcStatus?: string;
    profilePicture?: string | null;
    oshi?: UserOshi | null;
}

export interface AuthResponse {
    access_token: string;
    token_type: string;
    user: User;
}

export interface LoginRequest {
    username: string; // OAuth2PasswordRequestForm usually uses username for email
    password: string;
}

export interface RegisterRequest {
    memberId: string;
    username: string;
    fullName: string;
    email: string;
    ofcStatus: string;
    password: string;
    confirmPassword: string;
}

export interface EmailVerificationRequest {
    email: string;
}

export interface VerifyEmailRequest {
    token: string;
}

export interface PasswordResetRequest {
    email: string;
}

export interface PasswordResetConfirmRequest {
    token: string;
    new_password: string;
}

export interface GenericResponse {
    message: string;
}

export interface ApiError {
    detail: string | Record<string, any>;
}

export interface APIKeysResponse {
    detail?: string;
    apiKey: string;
}
