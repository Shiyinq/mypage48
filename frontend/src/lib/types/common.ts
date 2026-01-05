/**
 * Common/shared types used across multiple domains.
 */

export interface PaginationMeta {
    current_page: number;
    last_page: number;
    total_data: number;
    per_page: number;
    next_page: number | null;
}

export interface PaginationState {
    page: number;
    hasMore: boolean;
}

export interface GenericResponse {
    message: string;
}

export interface ApiError {
    detail:
    | string
    | { loc: (string | number)[]; msg: string; type: string }[]
    | Record<string, unknown>;
}

export type ViewState =
    | 'DASHBOARD'
    | 'UPLOAD'
    | 'HISTORY'
    | 'SHOWS'
    | 'ACHIEVEMENTS'
    | 'PROFILE'
    | 'MEMORIES'
    | 'TOP2SHOT';
