export interface OpenAPIParameter {
	name: string;
	in: 'path' | 'query' | 'header' | 'body';
	required: boolean;
	description?: string;
	schema: any;
}

export interface OpenAPIResponse {
	description: string;
	content?: Record<string, { schema: any }>;
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
			content: Record<string, { schema: any }>;
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
	paths: Record<string, Record<string, any>>;
	components?: {
		schemas?: Record<string, any>;
		securitySchemes?: Record<string, any>;
	};
}

export interface ExecutionPayload {
	method: string;
	path: string;
	params: Record<string, string>;
	body: any;
	headers: Record<string, string>;
}

export interface ExecutionResult {
	status: number;
	statusText: string;
	data: any;
	headers: Record<string, string>;
	duration: number;
}
