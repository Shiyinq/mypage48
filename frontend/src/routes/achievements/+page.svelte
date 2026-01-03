<script lang="ts">
	import { isAuthenticated, achievementsData, showToast } from '$lib/stores';
	import { onMount } from 'svelte';
	import SEO from '$lib/components/SEO.svelte';
	import {
		Trophy,
		Heart,
		Star,
		Calendar,
		Crown,
		Zap,
		Wallet,
		Armchair,
		Award,
		Medal,
		Binoculars,
		Sparkles,
		History,
		Flame,
		Ticket as TicketIcon,
		Lock,
		Check
	} from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { PageHeader, ErrorState } from '$lib/components';
	import { AchievementSkeleton } from '$lib/components/skeletons';
	import { achievements } from '$lib/apis/achievements';
	import type { ComponentType } from 'svelte';

	const { t } = useTranslation();

	// Icon mapping from backend string names to Lucide components
	const iconMap: Record<string, ComponentType> = {
		heart: Heart,
		ticket: TicketIcon,
		award: Award,
		medal: Medal,
		zap: Zap,
		crown: Crown,
		sparkles: Sparkles,
		trophy: Trophy,
		star: Star,
		flame: Flame,
		calendar: Calendar,
		history: History,
		binoculars: Binoculars,
		armchair: Armchair,
		wallet: Wallet
	};

	let loading = true;
	let error: string | null = null;

	$: unlocked = $achievementsData?.achievements.filter((m) => m.isUnlocked) ?? [];
	$: locked = $achievementsData?.achievements.filter((m) => !m.isUnlocked) ?? [];

	async function loadAchievements() {
		if ($isAuthenticated) {
			loading = true;
			error = null;
			if ($achievementsData) {
				loading = false;
				return;
			}
			try {
				const data = await achievements.getAchievements();
				achievementsData.set(data);
			} catch (e) {
				console.error('Failed to fetch achievements:', e);
				error = 'Failed to load achievements';
				showToast($t('achievements.errorTitle') || 'Failed to load achievements', 'error');
			} finally {
				loading = false;
			}
		} else {
			loading = false;
		}
	}

	onMount(() => {
		loadAchievements();
	});

	function getIcon(iconName: string): ComponentType {
		return iconMap[iconName] || Trophy;
	}
</script>

<SEO title={$t('achievements.title')} path="/achievements" description={$t('seo.achievements')} />

<div class="max-w-6xl mx-auto p-4 pb-24 animate-fade-in">
	<div class="mb-8">
		<PageHeader
			icon={Trophy}
			title={$t('achievements.title')}
			subtitle={$t('achievements.subtitle')}
			theme="yellow"
		/>
	</div>

	<!-- Grid Layout -->
	<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
		{#if loading}
			<!-- eslint-disable-next-line @typescript-eslint/no-unused-vars -->
			{#each Array(9) as _unused}
				<AchievementSkeleton />
			{/each}
		{:else if error}
			<div class="col-span-full">
				<ErrorState
					title={$t('achievements.errorTitle') || 'Failed to load achievements'}
					description={$t('achievements.errorDesc') || error || ''}
					onRetry={loadAchievements}
				/>
			</div>
		{:else}
			{#each [...unlocked, ...locked] as m (m.id)}
				<div
					class={`relative border-2 rounded-3xl p-5 flex items-center gap-5 transition-all duration-300 h-full ${
						m.isUnlocked
							? 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-400 dark:border-yellow-500/50 shadow-sm hover:shadow-md hover:scale-[1.01]'
							: 'bg-gray-50 dark:bg-zinc-900 border-gray-200 dark:border-zinc-700 opacity-70 grayscale'
					}`}
				>
					<!-- Icon Box -->
					<div
						class={`w-14 h-14 rounded-2xl flex items-center justify-center flex-shrink-0 ${
							m.isUnlocked
								? 'bg-white dark:bg-zinc-800 shadow-sm text-yellow-600'
								: 'bg-gray-200 dark:bg-zinc-700 text-gray-400'
						}`}
					>
						{#if m.isUnlocked}
							<svelte:component this={getIcon(m.icon)} class="w-8 h-8 fill-current" />
						{:else}
							<Lock class="w-6 h-6" />
						{/if}
					</div>

					<div class="flex-1">
						<h3 class={`text-lg font-bold ${m.isUnlocked ? 'text-themed' : 'text-themed-muted'}`}>
							{m.title}
						</h3>
						<p class="text-xs text-themed-secondary font-medium">{m.description}</p>

						<!-- Progress Bar for Locked Items -->
						{#if !m.isUnlocked && m.progress}
							<div class="mt-2">
								<div class="text-[10px] font-bold text-gray-400 mb-1 text-right">{m.progress}</div>
								<div class="w-full h-1.5 bg-gray-200 rounded-full overflow-hidden">
									<div
										class="h-full bg-gray-400 rounded-full"
										style={`width: ${
											m.progress.includes('/')
												? (parseInt(m.progress.split('/')[0]) /
														parseInt(m.progress.split('/')[1].replace(/[^0-9]/g, ''))) *
													100
												: 0
										}%`}
									></div>
								</div>
							</div>
						{/if}
					</div>

					<!-- Status Badge -->
					{#if m.isUnlocked}
						<div
							class="absolute top-4 right-4 bg-yellow-400 text-yellow-900 text-[10px] font-bold px-3 py-1 rounded-full flex items-center gap-1 shadow-sm"
						>
							{$t('achievements.unlocked')}
							<Check class="w-3 h-3" />
						</div>
					{/if}
				</div>
			{/each}
		{/if}
	</div>
</div>
