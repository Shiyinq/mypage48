import { client } from './client';
import type { OpenAPISchema, ExecutionPayload, ExecutionResult } from '$lib/types';

export const playgroundApi = {
	getSchema: async (): Promise<OpenAPISchema> => {
		return client<OpenAPISchema>('/playground/openapi.json');
	},

	executeRequest: async (payload: ExecutionPayload): Promise<ExecutionResult> => {
		const startTime = Date.now();
		
		const options: any = {
			method: payload.method,
			headers: payload.headers
		};

		if (payload.body && payload.method.toLowerCase() !== 'get') {
			options.body = payload.body;
		}

		try {
			// We use the raw Response for playground to get status, headers etc.
			// But the 'client' usually parses JSON. 
			// I'll check if client can return absolute response.
			// Actually, for playground, we want to see the full response object.
			
			// Let's use a try-catch for the client call.
			const data = await client<any>(payload.path, options);
			const duration = Date.now() - startTime;

			return {
				status: 200, // Client throws if not 2xx, so if we're here it's success-ish
				statusText: 'OK',
				data,
				headers: {}, // Client doesn't easily expose headers unless modified
				duration
			};
		} catch (err: any) {
			const duration = Date.now() - startTime;
			// The client adds 'status' to the error object.
			// We want to return the raw server response as 'data'.
			const { status, statusText, ...serverData } = err;
			
			return {
				status: status || 500,
				statusText: statusText || 'Error',
				data: Object.keys(serverData).length > 0 ? serverData : (err.message || err),
				headers: {},
				duration
			};
		}
	}
};
