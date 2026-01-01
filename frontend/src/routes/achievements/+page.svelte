<script lang="ts">
	import { tickets, isAuthenticated, isInitialDataLoaded } from '$lib/stores';
	import { onMount } from 'svelte';
	import SEO from '$lib/components/SEO.svelte';
	import { Trophy } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { PageHeader } from '$lib/components';
	import { AchievementCard } from '$lib/components/achievements';
	import { AchievementSkeleton } from '$lib/components/skeletons';
	import { calculateMilestones } from '$lib/utils/achievements';

	const { t } = useTranslation();

	$: milestones = calculateMilestones($tickets);
	$: unlocked = milestones.filter((m) => m.isUnlocked);
	$: locked = milestones.filter((m) => !m.isUnlocked);

	/* Loading State */
	let mounted = false;

	onMount(() => {
		mounted = true;
	});

	$: isLoading = !mounted || ($isAuthenticated && !$isInitialDataLoaded);
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
		{#if isLoading}
			<!-- eslint-disable-next-line @typescript-eslint/no-unused-vars -->
			{#each Array(9) as _unused}
				<AchievementSkeleton />
			{/each}
		{:else}
			{#each [...unlocked, ...locked] as m (m.id)}
				<AchievementCard milestone={m} />
			{/each}
		{/if}
	</div>
</div>
