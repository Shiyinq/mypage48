<script lang="ts">
	import { Save, AlertCircle } from 'lucide-svelte';
	import type { IDNLivePlusConfig } from '$lib/apis/admin';
	import { showToast } from '$lib/stores';
	import { adminStore } from '$lib/stores/admin.svelte';
	import SEO from '$lib/components/SEO.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { onMount } from 'svelte';

	const { t } = useTranslation();

	let config: IDNLivePlusConfig = {
		auth_token: '',
		access_token: '',
		session_id: '',
		api_key: '',
		aes_key: ''
	};
	let loading = false;
	let error = '';

	onMount(async () => {
		loading = true;
		await adminStore.loadIdnLivePlusConfig();
		if (adminStore.idnLivePlusConfig.data) {
			config = { ...adminStore.idnLivePlusConfig.data };
		}
		loading = false;
	});

	async function handleSave() {
		try {
			loading = true;
			error = '';
			const updatedConfig = await adminStore.updateIdnLivePlusConfig(config);
			config = { ...updatedConfig.data };
			showToast(t('admin.settings.saveSuccess'), 'success');
		} catch (err) {
			console.error('Error saving config:', err);
			const e = err as Error;
			error = e.message || t('admin.settings.saveFailed');
			showToast(t('admin.settings.saveFailed'), 'error');
		} finally {
			loading = false;
		}
	}
</script>

<SEO
	title="{t('admin.settings.title')} | MyPage48 Admin"
	description={t('admin.settings.subtitle')}
/>

<div class="space-y-6">
	<div>
		<h1 class="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
			{t('admin.settings.title')}
		</h1>
		<p class="text-slate-500 dark:text-slate-400">
			{t('admin.settings.subtitle')}
		</p>
	</div>

	{#if error}
		<div
			class="rounded-lg bg-red-50 p-4 dark:bg-red-900/50 border border-red-200 dark:border-red-800"
		>
			<div class="flex items-center gap-3">
				<AlertCircle class="h-5 w-5 text-red-600 dark:text-red-400" />
				<p class="text-sm font-medium text-red-800 dark:text-red-200">{error}</p>
			</div>
		</div>
	{/if}

	<div
		class="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900"
	>
		<div class="mb-6">
			<h2 class="text-lg font-semibold text-slate-900 dark:text-white">
				{t('admin.settings.idnLivePlus.title')}
			</h2>
			<p class="text-sm text-slate-500 dark:text-slate-400 mt-1">
				{t('admin.settings.idnLivePlus.description')}
			</p>
		</div>

		<form on:submit|preventDefault={handleSave} autocomplete="off" class="space-y-5">
			<div class="space-y-2">
				<label for="auth_token" class="text-sm font-medium text-slate-700 dark:text-slate-300">
					{t('admin.settings.idnLivePlus.authToken')}
				</label>
				<input
					type="text"
					id="auth_token"
					bind:value={config.auth_token}
					placeholder="eyJh..."
					class="w-full rounded-lg border border-slate-300 bg-transparent px-3 py-2 text-sm placeholder:text-slate-400 focus:border-red-500 focus:outline-none focus:ring-1 focus:ring-red-500 dark:border-slate-700 dark:text-white dark:focus:border-red-500"
				/>
				<p class="text-xs text-slate-500">{t('admin.settings.idnLivePlus.authTokenHelp')}</p>
			</div>

			<div class="space-y-2">
				<label for="access_token" class="text-sm font-medium text-slate-700 dark:text-slate-300">
					{t('admin.settings.idnLivePlus.accessToken')}
				</label>
				<input
					type="text"
					id="access_token"
					bind:value={config.access_token}
					placeholder="eyJh..."
					class="w-full rounded-lg border border-slate-300 bg-transparent px-3 py-2 text-sm placeholder:text-slate-400 focus:border-red-500 focus:outline-none focus:ring-1 focus:ring-red-500 dark:border-slate-700 dark:text-white dark:focus:border-red-500"
				/>
				<p class="text-xs text-slate-500">{t('admin.settings.idnLivePlus.accessTokenHelp')}</p>
			</div>

			<div class="space-y-2">
				<label for="session_id" class="text-sm font-medium text-slate-700 dark:text-slate-300">
					{t('admin.settings.idnLivePlus.sessionId')}
				</label>
				<input
					type="text"
					id="session_id"
					bind:value={config.session_id}
					placeholder="c89ae2b3..."
					class="w-full rounded-lg border border-slate-300 bg-transparent px-3 py-2 text-sm placeholder:text-slate-400 focus:border-red-500 focus:outline-none focus:ring-1 focus:ring-red-500 dark:border-slate-700 dark:text-white dark:focus:border-red-500"
				/>
				<p class="text-xs text-slate-500">{t('admin.settings.idnLivePlus.sessionIdHelp')}</p>
			</div>

			<div class="space-y-2">
				<label for="api_key" class="text-sm font-medium text-slate-700 dark:text-slate-300">
					{t('admin.settings.idnLivePlus.apiKey')}
				</label>
				<input
					type="text"
					id="api_key"
					bind:value={config.api_key}
					placeholder="123f4c..."
					class="w-full rounded-lg border border-slate-300 bg-transparent px-3 py-2 text-sm placeholder:text-slate-400 focus:border-red-500 focus:outline-none focus:ring-1 focus:ring-red-500 dark:border-slate-700 dark:text-white dark:focus:border-red-500"
				/>
				<p class="text-xs text-slate-500">{t('admin.settings.idnLivePlus.apiKeyHelp')}</p>
			</div>

			<div class="space-y-2">
				<label for="aes_key" class="text-sm font-medium text-slate-700 dark:text-slate-300">
					{t('admin.settings.idnLivePlus.aesKey')}
				</label>
				<input
					type="text"
					id="aes_key"
					bind:value={config.aes_key}
					placeholder="8dDR1n..."
					class="w-full rounded-lg border border-slate-300 bg-transparent px-3 py-2 text-sm placeholder:text-slate-400 focus:border-red-500 focus:outline-none focus:ring-1 focus:ring-red-500 dark:border-slate-700 dark:text-white dark:focus:border-red-500"
				/>
				<p class="text-xs text-slate-500">
					{t('admin.settings.idnLivePlus.aesKeyHelp')}
				</p>
			</div>

			<div class="flex justify-end pt-4">
				<button
					type="submit"
					disabled={loading}
					class="inline-flex cursor-pointer items-center gap-2 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 dark:focus:ring-offset-slate-900"
				>
					{#if loading}
						<div
							class="h-4 w-4 animate-spin rounded-full border-2 border-white/20 border-t-white"
						></div>
						{t('admin.settings.saving')}
					{:else}
						<Save class="h-4 w-4" />
						{t('admin.settings.saveConfig')}
					{/if}
				</button>
			</div>
		</form>
	</div>
</div>
