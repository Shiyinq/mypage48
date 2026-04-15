<script lang="ts">
	import { Play, Terminal, Hash, Globe, Server, RefreshCw, Copy, AlertCircle } from 'lucide-svelte';
	import { playgroundStore } from '$lib/stores/playground.svelte';
	import { accessToken } from '$lib/stores/accessToken.svelte';

	import { fade } from 'svelte/transition';
	import { showToast } from '$lib/stores';
	import type { OpenAPIEndpoint, OpenAPISchema, ExecutionPayload } from '$lib/types';
	import { useTranslation } from '$lib/i18n/useTranslation';

	const { t } = useTranslation();

	interface Props {
		endpoint?: OpenAPIEndpoint | null;
		openapi?: OpenAPISchema | null;
		executing?: boolean;
		onexecute?: (payload: ExecutionPayload) => void;
	}

	let { endpoint = null, openapi = null, executing = false, onexecute }: Props = $props();

	let parameters: Record<string, string> = $state({});
	let body: string = $state('');
	let headers: Record<string, string> = $state({});
	let lastEndpointId: string | null = $state(null);

	function resolveSchema(schema: unknown): unknown {
		if (!schema || typeof schema !== 'object') return schema;
		const s = schema as Record<string, unknown>;
		if (typeof s.$ref === 'string') {
			const refPath = s.$ref.replace('#/components/schemas/', '');
			const components = openapi?.components as Record<string, unknown> | undefined;
			const schemas = components?.schemas as Record<string, unknown> | undefined;
			return resolveSchema(schemas?.[refPath]);
		}
		return schema;
	}

	function generateExample(schema: unknown): unknown {
		const resolved = resolveSchema(schema);
		if (!resolved || typeof resolved !== 'object') return null;

		const r = resolved as Record<string, unknown>;

		if (r.type === 'object' || r.properties) {
			const obj: Record<string, unknown> = {};
			const props = (r.properties as Record<string, unknown>) || {};
			Object.entries(props).forEach(([key, prop]: [string, unknown]) => {
				obj[key] = generateExample(prop);
			});
			return obj;
		} else if (r.type === 'array') {
			return [generateExample(r.items)];
		} else {
			if (r.example !== undefined) return r.example;
			if (r.default !== undefined) return r.default;

			switch (r.type) {
				case 'string':
					return r.format === 'date' ? '2024-01-01' : 'string';
				case 'number':
				case 'integer':
					return 0;
				case 'boolean':
					return false;
				default:
					return null;
			}
		}
	}

	$effect(() => {
		if (endpoint && endpoint.id !== lastEndpointId) {
			lastEndpointId = endpoint.id;
			parameters = {};
			body = '';
			headers = {};

			// Initialize default values for parameters
			endpoint.details.parameters?.forEach((p) => {
				parameters[p.name] = '';
			});

			// Initialize body if it's a POST/PUT request
			if (endpoint.details.requestBody) {
				const content = endpoint.details.requestBody.content?.['application/json'];
				if (content?.schema) {
					const example = generateExample(content.schema);
					body = JSON.stringify(example, null, 2);
				}
			}
		}
	});

	function handleExecute() {
		if (!endpoint) return;
		let finalPath = endpoint.path;
		const queryParams = new URLSearchParams();
		const finalHeaders = { ...headers };

		endpoint.details.parameters?.forEach((p) => {
			if (p.in === 'path') {
				finalPath = finalPath.replace(`{${p.name}}`, parameters[p.name] || `{${p.name}}`);
			} else if (p.in === 'query' && parameters[p.name]) {
				queryParams.append(p.name, parameters[p.name]);
			} else if (p.in === 'header' && parameters[p.name]) {
				finalHeaders[p.name] = parameters[p.name];
			}
		});

		const queryString = queryParams.toString();
		const url = queryString ? `${finalPath}?${queryString}` : finalPath;

		onexecute?.({
			method: endpoint.method,
			path: url,
			params: parameters,
			body: body ? JSON.parse(body) : null,
			headers: finalHeaders
		});
	}

	function copyCurl() {
		if (!endpoint) return;
		let finalPath = endpoint.path;
		const queryParams = new URLSearchParams();
		// In playground, we typically use the session, but for cURL we'll include placeholders or known headers
		const curlHeaders = ["-H 'Content-Type: application/json'"];

		endpoint.details.parameters?.forEach((p) => {
			if (p.in === 'path') {
				finalPath = finalPath.replace(`{${p.name}}`, parameters[p.name] || `{${p.name}}`);
			} else if (p.in === 'query' && parameters[p.name]) {
				queryParams.append(p.name, parameters[p.name]);
			} else if (p.in === 'header' && parameters[p.name]) {
				curlHeaders.push(`-H '${p.name}: ${parameters[p.name]}'`);
			}
		});

		const queryString = queryParams.toString();
		let cleanPath = finalPath;
		if (cleanPath.startsWith('/api')) cleanPath = cleanPath.slice(4);
		else if (cleanPath.startsWith('api')) cleanPath = cleanPath.slice(3);

		if (cleanPath.startsWith('/')) cleanPath = cleanPath.slice(1);
		const fullUrl = `${window.location.origin}/api/${cleanPath}${queryString ? '?' + queryString : ''}`;

		const token = playgroundStore.useSession ? accessToken.value : playgroundStore.apiKey;
		if (token) {
			curlHeaders.push(`-H 'Authorization: Bearer ${token}'`);
		}

		let curlCommand = `curl -X ${endpoint.method.toUpperCase()} "${fullUrl}" \\\n${curlHeaders.join(' \\\n')}`;

		if (endpoint.method.toLowerCase() !== 'get' && body) {
			const escapedBody = body.replace(/'/g, "'\\''");
			curlCommand += ` \\\n-d '${escapedBody}'`;
		}

		navigator.clipboard.writeText(curlCommand);
		showToast(t('playground.curlCopied'), 'success');
	}

	const methodStyles: Record<string, string> = {
		get: 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/10 border-blue-100 dark:border-blue-900/20',
		post: 'text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/10 border-emerald-100 dark:border-emerald-900/20',
		put: 'text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/10 border-amber-100 dark:border-amber-900/20',
		delete:
			'text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-900/10 border-rose-100 dark:border-rose-900/20',
		patch:
			'text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-900/10 border-purple-100 dark:border-purple-900/20'
	};
</script>

<div class="flex-1 flex flex-col h-full overflow-hidden bg-white dark:bg-zinc-900 p-6">
	{#if endpoint}
		<div in:fade={{ duration: 200 }} class="space-y-8 flex-1 overflow-y-auto pr-4 custom-scrollbar">
			<!-- Header -->
			<div class="space-y-4">
				<div class="flex items-center gap-3">
					<span
						class="px-3 py-1 rounded-xl text-xs font-black uppercase border {methodStyles[
							endpoint.method.toLowerCase()
						]}"
					>
						{endpoint.method}
					</span>
					<h1 class="text-2xl font-black tracking-tight text-gray-900 dark:text-white">
						{endpoint.details.summary || t('playground.title')}
					</h1>
				</div>
				<p class="text-sm text-gray-500 dark:text-gray-400 font-medium">
					{endpoint.details.description || t('playground.noDescription')}
				</p>
				<div
					class="flex items-center justify-between gap-2 p-3 bg-gray-50 dark:bg-zinc-800 rounded-2xl border border-gray-100 dark:border-white/5 font-mono text-sm group"
				>
					<div class="flex items-center gap-2 overflow-hidden">
						<Globe class="w-4 h-4 text-gray-400 shrink-0" />
						<span class="text-gray-900 dark:text-gray-100 truncate">{endpoint.path}</span>
					</div>
					<button
						onclick={copyCurl}
						class="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white dark:bg-zinc-700 border border-gray-200 dark:border-white/10 text-[10px] font-bold text-gray-600 dark:text-gray-300 hover:text-red-500 dark:hover:text-red-400 hover:border-red-200 transition-all cursor-pointer shadow-sm active:scale-95"
					>
						<Copy class="w-3 h-3" />
						{t('playground.copyCurl')}
					</button>
				</div>
			</div>

			<!-- Parameters -->
			{#if endpoint.details.parameters && endpoint.details.parameters.length > 0}
				<div class="space-y-4">
					<div class="flex items-center gap-2 text-gray-900 dark:text-white">
						<Hash class="w-5 h-5 text-red-500" />
						<h2 class="text-lg font-bold">{t('playground.parameters')}</h2>
					</div>
					<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
						{#each endpoint.details.parameters as p}
							<div class="space-y-2">
								<div class="flex items-center justify-between">
									<label
										for="param-{p.name}"
										class="text-xs font-black uppercase text-gray-500 dark:text-gray-400 flex items-center gap-1.5"
									>
										{p.name}
										{#if p.required}
											<span class="text-red-500">*</span>
										{/if}
										<span
											class="px-1.5 py-0.5 rounded-md bg-gray-100 dark:bg-zinc-800 text-[10px] lowercase text-gray-400"
										>
											{p.in}
										</span>
									</label>
								</div>
								<input
									id="param-{p.name}"
									type="text"
									bind:value={parameters[p.name]}
									placeholder={p.schema?.type || 'value'}
									class="w-full px-4 py-2.5 bg-gray-50 dark:bg-zinc-800/50 border border-gray-100 dark:border-white/5 rounded-xl text-sm focus:ring-2 focus:ring-red-500/20 focus:border-red-500 transition-all outline-none"
								/>

								{#if p.description}
									<p class="text-[10px] text-gray-400 italic">{p.description}</p>
								{/if}
							</div>
						{/each}
					</div>
				</div>
			{/if}

			<!-- Request Body -->
			{#if body !== ''}
				<div class="space-y-4">
					<div class="flex items-center gap-2 text-gray-900 dark:text-white">
						<Server class="w-5 h-5 text-red-500" />
						<h2 class="text-lg font-bold">{t('playground.requestBody')}</h2>
					</div>
					<div class="relative group">
						<div class="absolute right-4 top-4 z-10">
							<span
								class="px-2 py-1 rounded-lg bg-gray-900/50 dark:bg-zinc-700/50 text-[10px] font-bold text-white uppercase backdrop-blur-md"
							>
								JSON
							</span>
						</div>
						<textarea
							bind:value={body}
							rows="8"
							spellcheck="false"
							class="w-full p-6 bg-gray-900 dark:bg-zinc-950 text-emerald-400 font-mono text-sm rounded-3xl border border-white/5 focus:ring-2 focus:ring-red-500/20 transition-all outline-none resize-none"
						></textarea>
					</div>
				</div>
			{/if}

			<!-- Action -->
			<div class="pt-6 border-t border-gray-100 dark:border-white/5 space-y-4">
				{#if !playgroundStore.apiKey && !playgroundStore.useSession}
					<div
						class="flex items-center gap-2 p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-600 dark:text-red-400 text-xs font-bold"
						in:fade
					>
						<AlertCircle class="w-4 h-4 shrink-0" />
						{t('playground.apiKeyRequired')}
					</div>
				{/if}

				<button
					onclick={handleExecute}
					disabled={executing || (!playgroundStore.apiKey && !playgroundStore.useSession)}
					class="w-full md:w-auto px-8 py-4 bg-gray-900 dark:bg-zinc-100 text-white dark:text-gray-900 rounded-2xl font-black text-sm uppercase tracking-widest hover:bg-black dark:hover:bg-white transition-all transform active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer flex items-center justify-center gap-3 shadow-xl shadow-gray-200 dark:shadow-none"
				>
					{#if executing}
						<RefreshCw class="w-4 h-4 animate-spin" />
						{t('playground.executing')}
					{:else}
						<Play class="w-4 h-4 fill-current" />
						{t('playground.execute')}
					{/if}
				</button>
			</div>
		</div>
	{:else}
		<div class="h-full flex flex-col items-center justify-center text-center space-y-6 opacity-40">
			<div
				class="w-20 h-20 rounded-full bg-gray-100 dark:bg-zinc-800 flex items-center justify-center"
			>
				<Terminal class="w-8 h-8 text-gray-400" />
			</div>
			<div class="max-w-xs">
				<h3 class="text-xl font-bold text-gray-900 dark:text-white mb-2">
					{t('playground.title')}
				</h3>
				<p class="text-sm text-gray-500">
					{t('playground.selectEndpoint')}
				</p>
			</div>
		</div>
	{/if}
</div>

<style>
	.custom-scrollbar::-webkit-scrollbar {
		width: 6px;
	}
	.custom-scrollbar::-webkit-scrollbar-track {
		background: transparent;
	}
	.custom-scrollbar::-webkit-scrollbar-thumb {
		background: rgba(0, 0, 0, 0.05);
		border-radius: 10px;
	}
	:global(.dark) .custom-scrollbar::-webkit-scrollbar-thumb {
		background: rgba(255, 255, 255, 0.05);
	}
</style>
