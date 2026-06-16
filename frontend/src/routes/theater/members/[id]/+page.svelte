<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { membersStore } from '$lib/stores/theater.svelte';
	import { pageHeaderStore } from '$lib/stores';
	import { Users } from 'lucide-svelte';
	import MemberDetailPage from '$lib/components/theater/MemberDetailPage.svelte';
	import { MemberDetailSkeleton } from '$lib/components/skeletons';

	$effect(() => {
		pageHeaderStore.set({
			title: 'Member',
			icon: Users,
			theme: 'pink',
			showBackButton: true,
			handleBack: () => goto('/theater/members')
		});
		return () => pageHeaderStore.reset();
	});
</script>

{#if membersStore.list.length > 0}
	<MemberDetailPage
		memberId={$page.params.id}
		members={membersStore.list}
		basePath="/theater/members"
	/>
{:else}
	<MemberDetailSkeleton />
{/if}
