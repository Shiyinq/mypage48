<script lang="ts">
	import { spring, type Spring } from 'svelte/motion';
	import AnimatedBackground from './AnimatedBackground.svelte';
	import AnimatedTeamBackground from './AnimatedTeamBackground.svelte';

	interface Props {
		interactive?: boolean;
		hideDecorationsOnMobile?: boolean;
		mouse?: Spring<{ x: number; y: number }>;
		scrollY?: number;
	}

	let {
		interactive = false,
		hideDecorationsOnMobile = false,
		mouse = $bindable(spring({ x: 0, y: 0 }, { stiffness: 0.1, damping: 0.25 })),
		scrollY = $bindable(0)
	}: Props = $props();

	// Hardcoded to 'team' for now. In the future, this could be driven by a store, settings, or themes.
	let backgroundType: 'default' | 'team' = 'team';
</script>

{#if backgroundType === 'team'}
	<AnimatedTeamBackground {interactive} {hideDecorationsOnMobile} bind:mouse bind:scrollY />
{:else}
	<AnimatedBackground {interactive} {hideDecorationsOnMobile} bind:mouse bind:scrollY />
{/if}
