<script lang="ts">
	import { isAuthenticated } from '$lib/stores';
	import LandingPage from '$lib/components/landing-page/LandingPage.svelte';
	import DashboardView from '$lib/components/dashboard/DashboardView.svelte';
	import { onMount } from 'svelte';
	import SplashScreen from '$lib/components/SplashScreen.svelte';
	import type { PageData } from './$types';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	let mounted = $state(false);

	onMount(() => {
		mounted = true;
	});
</script>

{#if isAuthenticated.value}
	<DashboardView />
{:else if data.hasSession && !mounted}
	<!-- Prevent flash of landing page if likely authenticated but not yet hydrated -->
	<SplashScreen />
{:else}
	<LandingPage />
{/if}
