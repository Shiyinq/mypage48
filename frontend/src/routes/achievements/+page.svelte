<script lang="ts">
	import { isAuthenticated, showToast } from '$lib/stores';
	import { logger } from '$lib/utils/logger';
	import { achievementsStore, isAchievementsLoading } from '$lib/stores/achievements';
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
		Ticket as TicketIcon
	} from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { PageHeader, ErrorState } from '$lib/components';
	import { AchievementSkeleton } from '$lib/components/skeletons';
	import AchievementCard from '$lib/components/achievements/AchievementCard.svelte';
	import type { ComponentType } from 'svelte';
	interface Props {
		params?: Record<string, string> | undefined;
	}

	let { params = undefined }: Props = $props();

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

	// Subscribe to store
	let state = $derived($achievementsStore);
	let data = $derived(state.data);
	let error = $derived(state.error);

	let unlocked = $derived(data?.achievements.filter((m) => m.isUnlocked) ?? []);
	let locked = $derived(data?.achievements.filter((m) => !m.isUnlocked) ?? []);

	async function loadAchievements() {
		if (!$isAuthenticated) {
			return;
		}

		try {
			await achievementsStore.load();
		} catch {
			// Error logged and handled by store
			showToast($t('achievements.errorLoad'), 'error');
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

<div class="max-w-7xl mx-auto px-4 sm:px-6 pt-4 sm:pt-6 animate-fade-in pb-32">
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
		{#if $isAchievementsLoading}
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
				<AchievementCard achievement={m} icon={getIcon(m.icon)} />
			{/each}
		{/if}
	</div>
</div>
