<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { membersStore } from '$lib/stores/theater.svelte';
	import { pageHeaderStore } from '$lib/stores';
	import { LoaderCircle, Users } from 'lucide-svelte';
	import MemberDetailPage from '$lib/components/theater/MemberDetailPage.svelte';

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
	<div
		class="h-[calc(100vh-64px)] flex flex-col items-center justify-center space-y-4 bg-slate-50/50 dark:bg-zinc-900/40"
	>
		<LoaderCircle class="w-10 h-10 animate-spin text-red-500" />
	</div>
{/if}
