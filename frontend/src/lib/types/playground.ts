export interface OpenAPIParameter {
	name: string;
	in: 'path' | 'query' | 'header' | 'body';
	required: boolean;
	description?: string;
	schema: any;
}

export interface OpenAPIResponse {
	description: string;
	content?: Record<string, { schema: unknown }>;
}

export interface OpenAPIEndpoint {
	id: string; // Internal ID (e.g. "GET:/api/users")
	method: string;
	path: string;
	details: {
		summary?: string;
		description?: string;
		tags?: string[];
		parameters?: OpenAPIParameter[];
		requestBody?: {
			content: Record<string, { schema: unknown }>;
		};
		responses?: Record<string, OpenAPIResponse>;
	};
}

export interface OpenAPISchema {
	openapi: string;
	info: {
		title: string;
		version: string;
	};
	paths: Record<string, Record<string, unknown>>;
	components?: {
		schemas?: Record<string, unknown>;
		securitySchemes?: Record<string, unknown>;
	};
}

export interface ExecutionPayload {
	method: string;
	path: string;
	params: Record<string, string>;
	body: unknown;
	headers: Record<string, string>;
}

export interface ExecutionResult {
	status: number;
	statusText: string;
	data: unknown;
	headers: Record<string, string>;
	duration: number;
}
