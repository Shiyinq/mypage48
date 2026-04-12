<script lang="ts">
	import { run } from 'svelte/legacy';

	import { showToast } from '$lib/stores';
	import { logger } from '$lib/utils/logger';
	import { userProfile, isInitialDataLoaded, isUserProfileLoading } from '$lib/stores';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { Share2, Copy, ExternalLink } from 'lucide-svelte';
	import { ErrorState } from '$lib/components';

	const { t } = useTranslation();

	let isPublic = $state($userProfile.data?.isPublic || false);
	let selectedPublicYearStr: string = $state($userProfile.data?.publicYear?.toString() || '');
	let updatingStatus = $state(false);

	// Generate available years (from 2011 to current year)
	const currentYear = new Date().getFullYear();
	const availableYears = Array.from({ length: currentYear - 2011 + 1 }, (_, i) => currentYear - i);

	run(() => {
		if ($userProfile.data) {
			isPublic = $userProfile.data.isPublic || false;
			// Only sync from profile if we aren't currently editing
			if (!updatingStatus) {
				selectedPublicYearStr = $userProfile.data.publicYear?.toString() || '';
			}
		}
	});

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
		{#if $isInitialDataLoaded && !$isUserProfileLoading}
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
						<div class="h-4 w-40 bg-gray-200 dark:bg-gray-700 rounded mb-2"></div>
						<div class="h-3 w-64 bg-gray-200 dark:bg-gray-700 rounded"></div>
					</div>
					<div class="w-12 h-7 bg-gray-200 dark:bg-gray-700 rounded-full"></div>
				</div>
			</div>
		{/if}
	{:else}
		<div
			class="bg-gray-50 dark:bg-gray-800/50 rounded-2xl p-4 border border-gray-100 dark:border-gray-700 mb-4"
		>
			<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
				<div class="flex-1">
					<p class="text-sm font-bold text-gray-800 dark:text-gray-200">
						{$t('settings.publicProfile.enable')}
					</p>
					<p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
						{$t('settings.publicProfile.description')}
					</p>
				</div>
				<div class="flex items-center justify-end gap-3 w-full sm:w-auto">
					{#if isPublic}
						<select
							value={selectedPublicYearStr}
							onchange={(e) => handleYearChange(e)}
							disabled={updatingStatus}
							class="p-2 text-xs font-bold bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 rounded-xl text-gray-700 dark:text-gray-300 focus:ring-2 focus:ring-purple-500 outline-none cursor-pointer flex-1 sm:flex-none"
						>
							<option value="">{$t('settings.publicProfile.allYears')}</option>
							<option value="-1">{$t('settings.publicProfile.thisYear')}</option>
							{#each availableYears as year}
								<option value={year.toString()}>{year}</option>
							{/each}
						</select>
					{/if}
					<button
						onclick={() => togglePublicStatus()}
						disabled={updatingStatus}
						class={`w-12 h-7 rounded-full transition-colors relative cursor-pointer flex-shrink-0 ${
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
					<p class="text-[10px] font-black text-gray-400 mb-2 uppercase tracking-widest pl-1">
						{$t('settings.publicProfile.yourLink')}
					</p>
					<div class="flex items-center gap-2">
						<div
							class="flex-1 bg-white dark:bg-zinc-900 py-2.5 px-3 rounded-xl border border-gray-200 dark:border-zinc-700 min-w-0"
						>
							<code class="text-xs font-mono text-purple-600 dark:text-purple-400 block truncate">
								{typeof window !== 'undefined' ? window.location.origin : ''}/u/{$userProfile.data
									?.username}
							</code>
						</div>
						<div class="flex items-center gap-1.5 flex-shrink-0">
							<a
								href="/u/{$userProfile.data?.username}"
								target="_blank"
								rel="noopener noreferrer"
								class="p-2.5 bg-purple-50 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 rounded-xl hover:bg-purple-100 transition-colors cursor-pointer border border-purple-100/50 dark:border-purple-800/30"
								title="Open Link"
							>
								<ExternalLink class="w-4 h-4" />
							</a>
							<button
								onclick={copyPublicLink}
								class="p-2.5 bg-gray-100 dark:bg-zinc-800 text-gray-600 dark:text-gray-300 rounded-xl hover:bg-gray-200 transition-colors cursor-pointer border border-gray-200/50 dark:border-zinc-700"
								title="Copy Link"
							>
								<Copy class="w-4 h-4" />
							</button>
						</div>
					</div>
				</div>
			{/if}
		</div>
	{/if}
</div>
