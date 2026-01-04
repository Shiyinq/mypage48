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
		Ticket as TicketIcon
	} from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { PageHeader, ErrorState } from '$lib/components';
	import { AchievementSkeleton } from '$lib/components/skeletons';
	import { achievements } from '$lib/apis/achievements';
	import AchievementCard from '$lib/components/achievements/AchievementCard.svelte';
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
				<AchievementCard achievement={m} icon={getIcon(m.icon)} />
			{/each}
		{/if}
	</div>
</div>
