<script lang="ts">
	import { goto } from '$app/navigation';
	import { showToast } from '$lib/stores';
	import { apiKeys } from '$lib/apis/api_keys';
	import {
		Settings,
		ArrowLeft,
		Key,
		Plus,
		Loader2,
		Copy,
		AlertTriangle,
		ChevronRight
	} from 'lucide-svelte';

	let generatingKey = false;
	let newApiKey: string | null = null;
	let showApiKeyModal = false;
	let showConfirmModal = false;

	const openConfirmModal = () => {
		showConfirmModal = true;
	};

	const closeConfirmModal = () => {
		showConfirmModal = false;
	};

	const confirmGenerateApiKey = async () => {
		showConfirmModal = false;
		generatingKey = true;
		try {
			const res = await apiKeys.create();
			newApiKey = res.apiKey;
			showApiKeyModal = true;
			showToast('API Key generated successfully', 'success');
		} catch (e) {
			console.error('Failed to generate API Key', e);
			showToast('Failed to generate API Key', 'error');
		} finally {
			generatingKey = false;
		}
	};

	const copyApiKey = () => {
		if (newApiKey) {
			navigator.clipboard.writeText(newApiKey);
			showToast('Copied to clipboard', 'success');
		}
	};

	const closeApiKeyModal = () => {
		showApiKeyModal = false;
		newApiKey = null;
	};
</script>

<div class="max-w-2xl mx-auto p-4 animate-fade-in pb-24">
	<!-- Page Header -->
	<div class="flex items-center justify-between mb-8">
		<div class="flex items-center gap-3">
			<button
				on:click={() => goto('/profile')}
				class="p-2 rounded-full bg-gray-100 text-gray-500 hover:bg-gray-200 hover:text-gray-700 transition-colors cursor-pointer"
				title="Back to Profile"
			>
				<ArrowLeft class="w-5 h-5" />
			</button>
			<div>
				<h2 class="text-2xl font-black idol-text-gradient leading-none relative w-fit">
					Settings
					<span
						class="absolute -bottom-1 left-0 w-full h-2 bg-red-200/60 -z-10 transform -skew-x-12 rounded-sm"
					></span>
				</h2>
				<p class="text-sm text-gray-500 mt-1">Manage your preferences</p>
			</div>
		</div>
	</div>

	<!-- Settings Content -->
	<div class="space-y-6">
		<!-- DEVELOPER ACCESS -->
		<div class="glass-panel p-6 rounded-3xl relative">
			<div class="flex items-center gap-3 mb-4">
				<div class="w-10 h-10 rounded-xl bg-gray-900 flex items-center justify-center shadow-lg">
					<Key class="w-5 h-5 text-white" />
				</div>
				<div>
					<h3 class="text-lg font-bold text-gray-900">Developer Access</h3>
					<p class="text-xs text-gray-500">Manage your API Keys</p>
				</div>
			</div>

			<div class="bg-gray-50 rounded-2xl p-4 border border-gray-100 mb-4">
				<p class="text-sm text-gray-600 leading-relaxed">
					Generate an API key to access <span class="font-bold text-gray-800">MYPAGE48</span> data programmatically.
					Use it to integrate with your own applications or scripts.
				</p>
				<div class="mt-3 flex items-start gap-2 bg-amber-50 p-3 rounded-xl border border-amber-100">
					<AlertTriangle class="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
					<p class="text-xs text-amber-700">
						<span class="font-bold">Important:</span> Your API key will only be shown once after generation.
						Make sure to copy and store it securely.
					</p>
				</div>
			</div>

			<button
				class="w-full py-3 rounded-xl bg-gray-900 text-white font-bold hover:bg-black transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-gray-300"
				on:click={openConfirmModal}
				disabled={generatingKey}
			>
				{#if generatingKey}
					<Loader2 class="w-4 h-4 animate-spin" />
					Generating...
				{:else}
					<Plus class="w-4 h-4" />
					Generate New API Key
				{/if}
			</button>
		</div>

		<!-- More Settings Coming Soon -->
		<div class="glass-panel p-6 rounded-3xl opacity-60">
			<div class="flex items-center justify-between">
				<div class="flex items-center gap-3">
					<div class="p-2.5 rounded-xl bg-gray-100 text-gray-400">
						<Settings class="w-5 h-5" />
					</div>
					<div>
						<h3 class="text-lg font-bold text-gray-400">More Settings</h3>
						<p class="text-xs text-gray-400">Coming soon...</p>
					</div>
				</div>
				<ChevronRight class="w-5 h-5 text-gray-300" />
			</div>
		</div>
	</div>
</div>

<!-- API Key Modal -->
{#if showApiKeyModal}
	<div
		class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fade-in"
	>
		<div
			class="bg-white rounded-2xl w-full max-w-md overflow-hidden shadow-2xl animate-scale-in p-6"
		>
			<div class="text-center mb-6">
				<div
					class="w-14 h-14 bg-gradient-to-br from-green-400 to-green-600 rounded-full flex items-center justify-center mx-auto mb-4 shadow-lg shadow-green-200"
				>
					<Key class="w-7 h-7 text-white" />
				</div>
				<h3 class="text-xl font-bold text-gray-900">API Key Generated!</h3>
				<p class="text-sm text-gray-500 mt-2">
					Please copy your API key now. You won't be able to see it again!
				</p>
			</div>

			<div class="bg-gray-50 p-4 rounded-xl border border-gray-200 mb-6 relative group">
				<code class="text-sm font-mono text-gray-800 break-all pr-10">{newApiKey}</code>
				<button
					class="absolute top-3 right-3 p-2 bg-white rounded-lg border border-gray-200 text-gray-500 hover:text-gray-900 hover:border-gray-300 transition-all shadow-sm cursor-pointer"
					on:click={copyApiKey}
					title="Copy to clipboard"
				>
					<Copy class="w-4 h-4" />
				</button>
			</div>

			<button
				class="w-full py-3 bg-gray-900 text-white rounded-xl font-bold hover:bg-black transition-colors cursor-pointer"
				on:click={closeApiKeyModal}
			>
				I have saved my key
			</button>
		</div>
	</div>
{/if}

<!-- Confirm Generate API Key Modal -->
{#if showConfirmModal}
	<div
		class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fade-in"
	>
		<div
			class="bg-white rounded-2xl w-full max-w-sm overflow-hidden shadow-2xl animate-scale-in p-6"
		>
			<div class="text-center mb-6">
				<div
					class="w-14 h-14 bg-gradient-to-br from-amber-400 to-amber-600 rounded-full flex items-center justify-center mx-auto mb-4 shadow-lg shadow-amber-200"
				>
					<AlertTriangle class="w-7 h-7 text-white" />
				</div>
				<h3 class="text-xl font-bold text-gray-900">Generate New API Key?</h3>
				<p class="text-sm text-gray-500 mt-2">
					This will revoke any existing API key. This action cannot be undone.
				</p>
			</div>

			<div class="flex gap-3">
				<button
					class="flex-1 py-3 bg-gray-100 text-gray-700 rounded-xl font-bold hover:bg-gray-200 transition-colors cursor-pointer"
					on:click={closeConfirmModal}
				>
					Cancel
				</button>
				<button
					class="flex-1 py-3 bg-red-600 text-white rounded-xl font-bold hover:bg-red-700 transition-colors cursor-pointer"
					on:click={confirmGenerateApiKey}
				>
					Generate
				</button>
			</div>
		</div>
	</div>
{/if}
