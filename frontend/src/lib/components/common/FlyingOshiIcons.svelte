<script lang="ts">
	import { Heart, Flame, Star } from 'lucide-svelte';
	import { getTeamColors } from '$lib/constants/teamColors';
	import { untrack } from 'svelte';

	interface Props {
		active?: boolean;
		memberType?: string;
		oshis?: { memberType?: string }[];
	}

	let { active = false, memberType, oshis = [] }: Props = $props();

	let flyingParticles: { id: number; style: string; iconSize: number; type: string }[] = $state([]);
	let nextParticleId = 0;

	export function burst(count: number = 3) {
		for (let i = 0; i < count; i++) {
			spawnParticle();
		}
	}

	function spawnParticle() {
		const angle = Math.random() * Math.PI * 2;
		const distance = 60 + Math.random() * 60;
		const tx = Math.cos(angle) * distance;
		const ty = Math.sin(angle) * distance - 30;
		const iconSize = 12 + Math.random() * 16;

		let particleType = 'LOVE';
		let typeToUse = memberType;

		if (oshis && oshis.length > 0) {
			const randomOshi = oshis[Math.floor(Math.random() * oshis.length)];
			typeToUse = randomOshi.memberType;
		}

		let particleColor = getTeamColors('LOVE').ring;
		if (typeToUse) {
			const type = typeToUse.toUpperCase();
			if (['LOVE', 'PASSION', 'DREAM'].includes(type)) {
				particleType = type;
				particleColor = getTeamColors(type).ring;
			}
		}

		const style = `--tx: ${tx}px; --ty: ${ty}px; left: ${40 + Math.random() * 20}%; top: ${40 + Math.random() * 20}%; color: ${particleColor};`;

		const id = nextParticleId++;
		flyingParticles.push({ id, style, iconSize, type: particleType });

		setTimeout(() => {
			flyingParticles = flyingParticles.filter((p) => p.id !== id);
		}, 1000);
	}

	$effect(() => {
		if (active) {
			untrack(() => spawnParticle());
			const interval = setInterval(() => {
				spawnParticle();
			}, 150);

			return () => clearInterval(interval);
		}
	});
</script>

<div class="absolute inset-0 pointer-events-none z-30">
	{#each flyingParticles as particle (particle.id)}
		<div class="flying-heart absolute drop-shadow-sm" style={particle.style}>
			{#if particle.type === 'PASSION'}
				<Flame
					class="fill-current"
					style="width: {particle.iconSize}px; height: {particle.iconSize}px;"
				/>
			{:else if particle.type === 'DREAM'}
				<Star
					class="fill-current"
					style="width: {particle.iconSize}px; height: {particle.iconSize}px;"
				/>
			{:else}
				<Heart
					class="fill-current"
					style="width: {particle.iconSize}px; height: {particle.iconSize}px;"
				/>
			{/if}
		</div>
	{/each}
</div>

<style>
	.flying-heart {
		animation: flyUp 1s ease-out forwards;
		transform: translate(0, 0) scale(0);
		opacity: 1;
	}

	@keyframes flyUp {
		0% {
			transform: translate(0, 0) scale(0.5);
			opacity: 0;
		}
		20% {
			transform: translate(calc(var(--tx) * 0.2), calc(var(--ty) * 0.2)) scale(1.2);
			opacity: 1;
		}
		80% {
			opacity: 0.8;
		}
		100% {
			transform: translate(var(--tx), var(--ty)) scale(1);
			opacity: 0;
		}
	}
</style>
