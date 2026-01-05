import { client } from './client';
import type { AnalysisResult } from '../types';

export const extractTicketData = async (base64Image: string): Promise<AnalysisResult> => {
    try {
        return await client<AnalysisResult>('/llm/analyze-ticket', {
            method: 'POST',
            body: { image: base64Image }
        });
    } catch (error) {
        console.error('Error extracting ticket data:', error);
        throw new Error('Failed to analyze ticket. Please try again or enter manually.');
    }
};
