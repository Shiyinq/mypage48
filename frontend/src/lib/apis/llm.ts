import { client } from './client';
import { logger } from '$lib/utils/logger';
import type { AnalysisResult } from '../types';

export const extractTicketData = async (base64Image: string): Promise<AnalysisResult> => {
	try {
		return await client<AnalysisResult>('/llm/analyze-ticket', {
			method: 'POST',
			body: { image: base64Image }
		});
	} catch (error) {
		logger.error('Error extracting ticket data', error, { context: 'LLMInterface' });
		throw new Error('Failed to analyze ticket. Please try again or enter manually.');
	}
};
