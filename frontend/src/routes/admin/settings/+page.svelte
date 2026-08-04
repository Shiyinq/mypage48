<script lang="ts">
	import { Save, AlertCircle } from 'lucide-svelte';
	import type { IDNLivePlusConfig } from '$lib/apis/admin';
	import { showToast } from '$lib/stores';
	import { adminStore } from '$lib/stores/admin.svelte';
	import SEO from '$lib/components/SEO.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { onMount, onDestroy } from 'svelte';

	const { t, locale } = useTranslation();

	let config: IDNLivePlusConfig = {
		auth_token: '',
		access_token: '',
		session_id: '',
		api_key: '',
		aes_key: '',
		refresh_token: '',
		cognito_client_id: '',
		updated_at: '',
		enabled: true
	};
	let loading = false;
	let error = '';

	let expiryInterval: ReturnType<typeof setInterval> | undefined;

	onMount(async () => {
		loading = true;
		await adminStore.loadIdnLivePlusConfig();
		if (adminStore.idnLivePlusConfig.data) {
			config = { ...adminStore.idnLivePlusConfig.data };
		}
		loading = false;

		expiryInterval = setInterval(() => {}, 60000);
	});

	onDestroy(() => {
		if (expiryInterval) clearInterval(expiryInterval);
	});

	function getJwtExp(token: string | null): Date | null {
		if (!token) return null;
		try {
			const payload = JSON.parse(atob(token.split('.')[1]));
			return payload.exp ? new Date(payload.exp * 1000) : null;
		} catch {
			return null;
		}
	}

	function formatWIB(date: Date | null): string {
		if (!date) return '';
		const localeMap: Record<string, string> = { id: 'id-ID', en: 'en-US', ja: 'ja-JP' };
		return date.toLocaleString(localeMap[locale.value] || 'id-ID', {
			day: 'numeric',
			month: 'short',
			year: 'numeric',
			hour: '2-digit',
			minute: '2-digit',
			timeZone: 'Asia/Jakarta'
		});
	}

	function expiresIn(expDate: Date | null): string {
		if (!expDate) return '';
		const diff = expDate.getTime() - Date.now();
		if (diff <= 0) return t('admin.settings.idnLivePlus.expired');
		const h = Math.floor(diff / 3600000);
		const m = Math.floor((diff % 3600000) / 60000);
		return t('admin.settings.idnLivePlus.expiresIn', { h: `${h}`, m: `${m}` });
	}

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
		<h1 class="text-2xl font-bold tracking-tight text-zinc-900 dark:text-white">
			{t('admin.settings.title')}
		</h1>
		<p class="text-zinc-500 dark:text-zinc-400">
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
		class="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900"
	>
		<div class="mb-6">
			<h2 class="text-lg font-semibold text-zinc-900 dark:text-white">
				{t('admin.settings.idnLivePlus.title')}
			</h2>
			<p class="text-sm text-zinc-500 dark:text-zinc-400 mt-1">
				{t('admin.settings.idnLivePlus.description')}
			</p>
		</div>

		<form on:submit|preventDefault={handleSave} autocomplete="off" class="space-y-5">
			<div
				class="flex items-center justify-between rounded-lg border border-zinc-200 bg-zinc-50 p-4 dark:border-zinc-700 dark:bg-zinc-800/50"
			>
				<div>
					<p class="text-sm font-medium text-zinc-700 dark:text-zinc-300">
						{t('admin.settings.idnLivePlus.enabled')}
					</p>
					<p class="text-xs text-zinc-500">{t('admin.settings.idnLivePlus.enabledHelp')}</p>
				</div>
				<button
					type="button"
					role="switch"
					aria-checked={config.enabled}
					aria-label={t('admin.settings.idnLivePlus.enabled')}
					on:click={() => (config.enabled = !config.enabled)}
					class="relative inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent transition-colors focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 dark:focus:ring-offset-zinc-900 {config.enabled
						? 'bg-red-600'
						: 'bg-zinc-300 dark:bg-zinc-600'}"
				>
					<span
						class="inline-block h-5 w-5 transform rounded-full bg-white shadow-sm ring-0 transition-transform {config.enabled
							? 'translate-x-5'
							: 'translate-x-0'}"
					></span>
				</button>
			</div>

			<div class="space-y-2">
				<label for="auth_token" class="text-sm font-medium text-zinc-700 dark:text-zinc-300">
					{t('admin.settings.idnLivePlus.authToken')}
				</label>
				<input
					type="text"
					id="auth_token"
					bind:value={config.auth_token}
					placeholder="eyJh..."
					class="w-full rounded-lg border border-zinc-300 bg-transparent px-3 py-2 text-sm placeholder:text-zinc-400 focus:border-red-500 focus:outline-none focus:ring-1 focus:ring-red-500 dark:border-zinc-700 dark:text-white dark:focus:border-red-500"
				/>
				<p class="text-xs text-zinc-500">
					{t('admin.settings.idnLivePlus.authTokenHelp')}
					{#if getJwtExp(config.auth_token)}
						<br />
						{t('admin.settings.idnLivePlus.expiresAt')}: {formatWIB(getJwtExp(config.auth_token))} WIB
						&middot; {expiresIn(getJwtExp(config.auth_token))}
					{/if}
				</p>
			</div>

			<div class="space-y-2">
				<label for="access_token" class="text-sm font-medium text-zinc-700 dark:text-zinc-300">
					{t('admin.settings.idnLivePlus.accessToken')}
				</label>
				<input
					type="text"
					id="access_token"
					bind:value={config.access_token}
					placeholder="eyJh..."
					class="w-full rounded-lg border border-zinc-300 bg-transparent px-3 py-2 text-sm placeholder:text-zinc-400 focus:border-red-500 focus:outline-none focus:ring-1 focus:ring-red-500 dark:border-zinc-700 dark:text-white dark:focus:border-red-500"
				/>
				<p class="text-xs text-zinc-500">
					{t('admin.settings.idnLivePlus.accessTokenHelp')}
					{#if getJwtExp(config.access_token)}
						<br />
						{t('admin.settings.idnLivePlus.expiresAt')}: {formatWIB(getJwtExp(config.access_token))} WIB
						&middot; {expiresIn(getJwtExp(config.access_token))}
					{/if}
				</p>
			</div>

			<div class="space-y-2">
				<label for="session_id" class="text-sm font-medium text-zinc-700 dark:text-zinc-300">
					{t('admin.settings.idnLivePlus.sessionId')}
				</label>
				<input
					type="text"
					id="session_id"
					bind:value={config.session_id}
					placeholder="c89ae2b3..."
					class="w-full rounded-lg border border-zinc-300 bg-transparent px-3 py-2 text-sm placeholder:text-zinc-400 focus:border-red-500 focus:outline-none focus:ring-1 focus:ring-red-500 dark:border-zinc-700 dark:text-white dark:focus:border-red-500"
				/>
				<p class="text-xs text-zinc-500">{t('admin.settings.idnLivePlus.sessionIdHelp')}</p>
			</div>

			<div class="space-y-2">
				<label for="api_key" class="text-sm font-medium text-zinc-700 dark:text-zinc-300">
					{t('admin.settings.idnLivePlus.apiKey')}
				</label>
				<input
					type="text"
					id="api_key"
					bind:value={config.api_key}
					placeholder="123f4c..."
					class="w-full rounded-lg border border-zinc-300 bg-transparent px-3 py-2 text-sm placeholder:text-zinc-400 focus:border-red-500 focus:outline-none focus:ring-1 focus:ring-red-500 dark:border-zinc-700 dark:text-white dark:focus:border-red-500"
				/>
				<p class="text-xs text-zinc-500">{t('admin.settings.idnLivePlus.apiKeyHelp')}</p>
			</div>

			<div class="space-y-2">
				<label for="aes_key" class="text-sm font-medium text-zinc-700 dark:text-zinc-300">
					{t('admin.settings.idnLivePlus.aesKey')}
				</label>
				<input
					type="text"
					id="aes_key"
					bind:value={config.aes_key}
					placeholder="8dDR1n..."
					class="w-full rounded-lg border border-zinc-300 bg-transparent px-3 py-2 text-sm placeholder:text-zinc-400 focus:border-red-500 focus:outline-none focus:ring-1 focus:ring-red-500 dark:border-zinc-700 dark:text-white dark:focus:border-red-500"
				/>
				<p class="text-xs text-zinc-500">
					{t('admin.settings.idnLivePlus.aesKeyHelp')}
				</p>
			</div>

			<div class="space-y-2">
				<label for="refresh_token" class="text-sm font-medium text-zinc-700 dark:text-zinc-300">
					{t('admin.settings.idnLivePlus.refreshToken')}
				</label>
				<input
					type="text"
					id="refresh_token"
					bind:value={config.refresh_token}
					placeholder="eyJ..."
					class="w-full rounded-lg border border-zinc-300 bg-transparent px-3 py-2 text-sm placeholder:text-zinc-400 focus:border-red-500 focus:outline-none focus:ring-1 focus:ring-red-500 dark:border-zinc-700 dark:text-white dark:focus:border-red-500"
				/>
				<p class="text-xs text-zinc-500">{t('admin.settings.idnLivePlus.refreshTokenHelp')}</p>
			</div>

			<div class="space-y-2">
				<label for="cognito_client_id" class="text-sm font-medium text-zinc-700 dark:text-zinc-300">
					{t('admin.settings.idnLivePlus.cognitoClientId')}
				</label>
				<input
					type="text"
					id="cognito_client_id"
					bind:value={config.cognito_client_id}
					placeholder="Cognito Client ID"
					class="w-full rounded-lg border border-zinc-300 bg-transparent px-3 py-2 text-sm placeholder:text-zinc-400 focus:border-red-500 focus:outline-none focus:ring-1 focus:ring-red-500 dark:border-zinc-700 dark:text-white dark:focus:border-red-500"
				/>
				<p class="text-xs text-zinc-500">{t('admin.settings.idnLivePlus.cognitoClientIdHelp')}</p>
			</div>

			{#if config.updated_at}
				<div class="text-xs text-zinc-500">
					{t('admin.settings.idnLivePlus.lastRefreshed')}: {formatWIB(new Date(config.updated_at))} WIB
				</div>
			{/if}

			<div class="flex justify-end pt-4">
				<button
					type="submit"
					disabled={loading}
					class="inline-flex cursor-pointer items-center gap-2 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 dark:focus:ring-offset-zinc-900"
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
