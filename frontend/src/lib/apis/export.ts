import { client } from './client';

export interface ExportResponse {
    status: 'IDLE' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
    message?: string;
    expires_at?: string;
}

export const exportApi = {
    getStatus: async (): Promise<ExportResponse> => {
        return client<ExportResponse>('/export/status');
    },

    initiateExport: async (): Promise<ExportResponse> => {
        return client<ExportResponse>('/export', { method: 'POST' });
    },


    download: async (): Promise<Blob> => {
        return client<Blob>('/export/download', {
            responseType: 'blob'
        });
    }
};
