<script lang="ts">
	import { showToast } from '$lib/stores';
	import { logger } from '$lib/utils/logger';
	import { userProfile, isInitialDataLoaded } from '$lib/stores';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { Share2, Copy, ExternalLink } from 'lucide-svelte';
	import { ErrorState } from '$lib/components';

	const { t } = useTranslation();

	let isPublic = $userProfile.data?.isPublic || false;
	let selectedPublicYearStr: string = $userProfile.data?.publicYear?.toString() || '';
	let updatingStatus = false;

	// Generate available years (from 2011 to current year)
	const currentYear = new Date().getFullYear();
	const availableYears = Array.from({ length: currentYear - 2011 + 1 }, (_, i) => currentYear - i);

	$: if ($userProfile.data) {
		isPublic = $userProfile.data.isPublic || false;
		// Only sync from profile if we aren't currently editing
		if (!updatingStatus) {
			selectedPublicYearStr = $userProfile.data.publicYear?.toString() || '';
		}
	}

	// Helper to convert string to number | null for API
	const getYearForApi = (): number | null => {
		if (!selectedPublicYearStr || selectedPublicYearStr === '') {
			return null;
		}
		return parseInt(selectedPublicYearStr, 10);
	};

	const updatePublicSettings = async (newIsPublic: boolean) => {
		updatingStatus = true;
		const yearPayload = newIsPublic ? getYearForApi() : null;

		try {
			// Use store action
			await userProfile.updatePublicStatus(newIsPublic, yearPayload);
			showToast($t('common.success'), 'success');
		} catch (e) {
			logger.error('Failed to update public status', e, { context: 'PublicProfileSettings' });
			showToast($t('common.error'), 'error');
		} finally {
			updatingStatus = false;
		}
	};

	const togglePublicStatus = async () => {
		if (updatingStatus) return;
		await updatePublicSettings(!isPublic);
	};

	const handleYearChange = async (e: Event) => {
		if (updatingStatus) return;

		const target = e.target as HTMLSelectElement;
		const newYearStr = target.value;
		selectedPublicYearStr = newYearStr;

		const yearPayload = newYearStr === '' ? null : parseInt(newYearStr, 10);

		updatingStatus = true;
		try {
			// Use store action
			await userProfile.updatePublicStatus(true, yearPayload);
			showToast($t('common.success'), 'success');
		} catch (err) {
			logger.error('Failed to update public year', err, { context: 'PublicProfileSettings' });
			showToast($t('common.error'), 'error');
		} finally {
			updatingStatus = false;
		}
	};

	const copyPublicLink = () => {
		navigator.clipboard.writeText(`${window.location.origin}/u/${$userProfile.data?.username}`);
		showToast($t('settings.developer.copied'), 'success');
	};

	// Retry fetching profile data if it failed initially
	const retryGlobalProfileFetch = async () => {
		try {
			// Use store action
			await userProfile.load();
		} catch (e) {
			logger.error('Failed to retry profile fetch', e, { context: 'PublicProfileSettings' });
			showToast($t('profile.errorTitle'), 'error');
		}
	};
</script>

<div class="glass-panel p-6 rounded-3xl relative">
	<div class="flex items-center gap-3 mb-4">
		<div
			class="w-10 h-10 rounded-xl bg-purple-100 dark:bg-purple-900/20 flex items-center justify-center shadow-sm"
		>
			<Share2 class="w-5 h-5 text-purple-600 dark:text-purple-400" />
		</div>
		<div>
			<h3 class="text-lg font-bold text-gray-900 dark:text-gray-100">
				{$t('settings.publicProfile.title')}
			</h3>
			<p class="text-xs text-gray-500 dark:text-gray-400">
				{$t('settings.publicProfile.subtitle')}
			</p>
		</div>
	</div>

	{#if !$userProfile.data}
		{#if $isInitialDataLoaded && !$userProfile.loading}
			<!-- Error State if data is loaded but profile is missing -->
			<div class="mb-4">
				<ErrorState
					title={$t('settings.publicProfile.loadErrorTitle')}
					description={$t('settings.publicProfile.loadErrorDesc')}
					onRetry={retryGlobalProfileFetch}
				/>
			</div>
		{:else}
			<!-- Loading Skeleton -->
			<div
				class="bg-gray-50 dark:bg-gray-800/50 rounded-2xl p-4 border border-gray-100 dark:border-gray-700 mb-4 animate-pulse"
			>
				<div class="flex items-center justify-between">
					<div>
						<div class="h-4 w-40 bg-gray-200 dark:bg-gray-700 rounded mb-2" />
						<div class="h-3 w-64 bg-gray-200 dark:bg-gray-700 rounded" />
					</div>
					<div class="w-12 h-7 bg-gray-200 dark:bg-gray-700 rounded-full" />
				</div>
			</div>
		{/if}
	{:else}
		<div
			class="bg-gray-50 dark:bg-gray-800/50 rounded-2xl p-4 border border-gray-100 dark:border-gray-700 mb-4"
		>
			<div class="flex items-center justify-between">
				<div>
					<p class="text-sm font-bold text-gray-800 dark:text-gray-200">
						{$t('settings.publicProfile.enable')}
					</p>
					<p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
						{$t('settings.publicProfile.description')}
					</p>
				</div>
				<div class="flex items-center gap-3">
					{#if isPublic}
						<select
							value={selectedPublicYearStr}
							on:change={(e) => handleYearChange(e)}
							disabled={updatingStatus}
							class="p-1 px-2 text-xs font-bold bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 rounded-lg text-gray-700 dark:text-gray-300 focus:ring-2 focus:ring-purple-500 outline-none cursor-pointer"
						>
							<option value="">{$t('settings.publicProfile.allYears')}</option>
							<option value="-1">{$t('settings.publicProfile.thisYear')}</option>
							{#each availableYears as year}
								<option value={year.toString()}>{year}</option>
							{/each}
						</select>
					{/if}
					<button
						on:click={() => togglePublicStatus()}
						disabled={updatingStatus}
						class={`w-12 h-7 rounded-full transition-colors relative cursor-pointer ${
							isPublic ? 'bg-purple-500' : 'bg-gray-300 dark:bg-zinc-600'
						}`}
					>
						{#if updatingStatus}
							<div
								class="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-4 h-4 border-2 border-white/50 border-t-white rounded-full animate-spin"
							></div>
						{:else}
							<div
								class={`absolute top-1 w-5 h-5 bg-white rounded-full transition-transform shadow-sm ${
									isPublic ? 'left-6' : 'left-1'
								}`}
							></div>
						{/if}
					</button>
				</div>
			</div>

			{#if isPublic}
				<div class="mt-4 pt-4 border-t border-gray-100 dark:border-gray-700 animate-slide-down">
					<p class="text-xs font-bold text-gray-500 mb-2 uppercase tracking-wide">
						{$t('settings.publicProfile.yourLink')}
					</p>
					<div class="flex items-center gap-2">
						<code
							class="flex-1 bg-white dark:bg-zinc-900 py-2.5 px-3 rounded-lg border border-gray-200 dark:border-zinc-700 text-sm font-mono text-purple-600 dark:text-purple-400 truncate"
						>
							{typeof window !== 'undefined' ? window.location.origin : ''}/u/{$userProfile.data
								?.username}
						</code>
						<a
							href="/u/{$userProfile.data?.username}"
							target="_blank"
							rel="noopener noreferrer"
							class="p-2.5 bg-purple-100/50 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 rounded-lg hover:bg-purple-100 dark:hover:bg-purple-900/50 transition-colors cursor-pointer"
							title="Open Link"
						>
							<ExternalLink class="w-4 h-4" />
						</a>
						<button
							on:click={copyPublicLink}
							class="p-2.5 bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors cursor-pointer"
							title="Copy Link"
						>
							<Copy class="w-4 h-4" />
						</button>
					</div>
				</div>
			{/if}
		</div>
	{/if}
</div>
