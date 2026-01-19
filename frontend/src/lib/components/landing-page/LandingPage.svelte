<script lang="ts">
	import {
		ArrowRight,
		Ticket,
		Camera,
		Users,
		Trophy,
		Sparkles,
		Star,
		Rocket,
		Github
	} from 'lucide-svelte';
	import { onMount } from 'svelte';
	import { fade } from 'svelte/transition';
	import { spring } from 'svelte/motion';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import LandingPageThemeToggle from './ThemeToggle.svelte';
	import LanguageToggle from './LanguageToggle.svelte';

	const { t } = useTranslation();

	let decorations: Array<{
		x: number;
		y: number;
		scale: number;
		delay: number;
		duration: number;
		depth: number;
		type: 'star' | 'sparkle';
	}> = [];

	let mouse = spring({ x: 0, y: 0 }, { stiffness: 0.1, damping: 0.25 });

	function handleMouseMove(event: MouseEvent) {
		const { clientX, clientY, currentTarget } = event;
		const { clientWidth, clientHeight } = currentTarget as HTMLElement;
		// Calculate center-relative coordinates (-0.5 to 0.5)
		const x = clientX / clientWidth - 0.5;
		const y = clientY / clientHeight - 0.5;
		mouse.set({ x, y });
	}

	onMount(() => {
		decorations = Array.from({ length: 25 }, () => ({
			x: Math.random() * 100,
			y: Math.random() * 100,
			scale: 0.5 + Math.random() * 1.5,
			delay: Math.random() * 5,
			duration: 3 + Math.random() * 4,
			depth: (Math.random() - 0.5) * 150, // Parallax depth factor (Increased 3x)
			type: Math.random() > 0.5 ? 'star' : 'sparkle'
		}));
	});

	// Make features reactive to language changes
	$: features = [
		{
			title: $t('landing.features.theater.title'),
			description: $t('landing.features.theater.description'),
			icon: Ticket,
			color: 'text-red-500',
			iconBg: 'bg-red-50',
			type: 'theater'
		},
		{
			title: $t('landing.features.twoShot.title'),
			description: $t('landing.features.twoShot.description'),
			icon: Camera,
			color: 'text-pink-500',
			iconBg: 'bg-pink-50',
			type: 'twoshot'
		},
		{
			title: $t('landing.features.memories.title'),
			description: $t('landing.features.memories.description'),
			icon: Users,
			color: 'text-blue-500',
			iconBg: 'bg-blue-50',
			type: 'memories'
		},
		{
			title: $t('landing.features.achievements.title'),
			description: $t('landing.features.achievements.description'),
			icon: Trophy,
			color: 'text-yellow-500',
			iconBg: 'bg-yellow-50',
			type: 'achievements'
		}
	];
</script>

<SEO title="Home" />

<div
	class="min-h-screen bg-gradient-to-b from-pink-50/50 via-white to-white dark:from-zinc-950 dark:via-zinc-950 dark:to-zinc-900 relative overflow-hidden font-sans selection:bg-red-500/20"
	on:mousemove={handleMouseMove}
>
	<!-- Background Elements -->
	<div class="fixed inset-0 pointer-events-none z-0">
		<div
			class="absolute inset-0 opacity-[0.4]"
			style="background-image: radial-gradient(#fb7185 1px, transparent 1px); background-size: 32px 32px;"
		></div>

		<!-- Soft Glows -->
		<div
			class="absolute top-0 right-0 w-[800px] h-[800px] bg-red-100/30 rounded-full blur-[120px] -translate-y-1/2 translate-x-1/2"
		></div>
		<div
			class="absolute bottom-0 left-0 w-[600px] h-[600px] bg-pink-100/30 rounded-full blur-[100px] translate-y-1/2 -translate-x-1/2"
		></div>

		<!-- Static Decor Elements (Restored) -->
		<div
			class="absolute top-20 left-10 text-pink-200 animate-pulse delay-700 hover:scale-125 hover:text-pink-400 cursor-pointer transition-all duration-300 pointer-events-auto"
		>
			<Sparkles size={48} />
		</div>
		<div
			class="absolute top-40 right-10 text-red-200 animate-pulse delay-300 hover:scale-125 hover:rotate-12 hover:text-red-400 cursor-pointer transition-all duration-300 pointer-events-auto"
			style="transform: translate({$mouse.x * 60}px, {$mouse.y * 60}px)"
		>
			<Star size={32} />
		</div>

		<!-- Dynamic Decor Elements -->
		<!-- Decor Elements -->
		{#each decorations as d}
			<div
				in:fade={{ duration: 2000 }}
				class="absolute cursor-pointer hover:z-10 group pointer-events-auto"
				style="
                left: {d.x}%;
                top: {d.y}%;
                transform: scale({d.scale}) translate({$mouse.x * d.depth}px, {$mouse.y *
					d.depth}px);
            "
			>
				<!-- Floating Wrapper -->
				<div
					class="animate-float"
					style="
                    animation-delay: {d.delay}s;
                    animation-duration: {d.duration}s;
                "
				>
					<!-- Interaction Wrapper -->
					<div
						class="transition-all duration-500 ease-out group-hover:scale-150 group-hover:rotate-12 {d.type ===
						'star'
							? 'text-red-300 dark:text-red-500/30 group-hover:text-red-500 dark:group-hover:text-red-400'
							: 'text-pink-300 dark:text-pink-500/30 group-hover:text-pink-500 dark:group-hover:text-pink-400'}"
					>
						<div class="animate-pulse" style="animation-duration: {d.duration / 1.5}s">
							{#if d.type === 'star'}
								<Star size={28} strokeWidth={2} fill="currentColor" class="opacity-60" />
							{:else}
								<Sparkles size={32} strokeWidth={2} class="opacity-80" />
							{/if}
						</div>
					</div>
				</div>
			</div>
		{/each}
	</div>

	<!-- NAV -->
	<nav
		class="relative z-50 flex justify-between items-center p-6 max-w-7xl mx-auto pointer-events-none"
	>
		<div class="flex items-center gap-3 group cursor-default pointer-events-auto">
			<div
				class="w-10 h-10 rounded-full bg-red-600 flex items-center justify-center text-white shadow-xl shadow-red-500/20 ring-4 ring-white dark:ring-zinc-800 transition-transform group-hover:scale-105 duration-300"
			>
				<Ticket class="w-5 h-5" />
			</div>
			<div class="flex flex-col relative">
				<div
					class="absolute inset-0"
					style="transform: translate({$mouse.x * 10}px, {$mouse.y * 10}px)"
				></div>
				<h1
					class="text-xl font-black tracking-tighter text-slate-900 dark:text-white leading-none relative z-10"
					style="transform: translate({$mouse.x * 5}px, {$mouse.y * 5}px)"
				>
					MyPage<span class="text-red-600">48</span>
				</h1>
				<span
					class="text-[9px] font-bold text-slate-400 dark:text-slate-500 tracking-[0.2em] uppercase mt-0.5"
					style="transform: translate({$mouse.x * 8}px, {$mouse.y * 8}px)"
				>
					{$t('landing.nav.subtitle')}
				</span>
			</div>
		</div>
		<div class="flex items-center gap-4 pointer-events-auto">
			<LanguageToggle />
			<LandingPageThemeToggle />
			<a
				href="/login"
				class="px-6 py-2 rounded-full bg-red-600 text-white font-bold text-sm shadow-xl shadow-red-500/30 hover:shadow-red-500/50 hover:-translate-y-0.5 transition-all flex items-center gap-2 group"
			>
				{$t('auth.login.signIn')}
				<ArrowRight size={14} class="group-hover:translate-x-1 transition-transform" />
			</a>
		</div>
	</nav>

	<!-- HERO -->
	<header class="relative z-10 pt-16 pb-32 px-6 text-center max-w-5xl mx-auto pointer-events-none">
		<!-- Pill -->
		<div
			class="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white dark:bg-zinc-900 border border-red-100 dark:border-red-900/30 shadow-sm dark:shadow-none mb-12 opacity-0 animate-appear pointer-events-auto"
		>
			<span class="relative flex h-2 w-2">
				<span
					class="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"
				></span>
				<span class="relative inline-flex rounded-full h-2 w-2 bg-red-600"></span>
			</span>
			<span
				class="text-[10px] font-bold text-slate-400 dark:text-slate-400 tracking-[0.2em] uppercase"
				>{$t('landing.hero.badge')}</span
			>
		</div>

		<!-- Parallax Wrapper for Title -->
		<div class="opacity-0 animate-appear mb-8" style="animation-delay: 100ms;">
			<h1
				class="text-6xl md:text-8xl font-black tracking-tighter text-slate-900 dark:text-white leading-[0.9] pointer-events-auto"
				style="transform: translate({$mouse.x * 30}px, {$mouse.y * 30}px)"
			>
				{$t('landing.hero.titlePrefix')} <br />
				<span class="text-transparent bg-clip-text bg-gradient-to-r from-red-600 to-pink-500">
					{$t('landing.hero.titleSuffix')}
				</span>
			</h1>
		</div>

		<!-- Parallax Wrapper for Description -->
		<div class="opacity-0 animate-appear pointer-events-auto mb-12" style="animation-delay: 200ms;">
			<div style="transform: translate({$mouse.x * 15}px, {$mouse.y * 15}px)">
				<p
					class="text-lg md:text-xl text-slate-500 dark:text-slate-400 max-w-2xl mx-auto font-medium leading-relaxed"
				>
					{@html $t('landing.hero.description', {
						highlight: `<span class="text-slate-800 dark:text-slate-200 font-bold decoration-red-200 decoration-2 underline-offset-4">${$t('landing.hero.highlight')}</span>`
					})}
				</p>
			</div>
		</div>

		<div
			class="flex flex-col items-center justify-center opacity-0 animate-appear pointer-events-auto"
			style="animation-delay: 300ms;"
		>
			<a
				href="/register"
				class="group relative inline-flex items-center justify-center gap-3 px-8 py-4 rounded-xl bg-red-600 text-white font-bold text-base shadow-xl shadow-red-500/30 hover:shadow-red-500/50 hover:-translate-y-1 transition-all duration-300"
			>
				{$t('landing.hero.getStarted')}
				<Rocket size={20} class="group-hover:rotate-12 transition-transform" />
			</a>
			<p class="mt-6 text-[10px] font-bold text-slate-300 uppercase tracking-[0.3em]">
				{$t('landing.hero.openSource')}
			</p>
		</div>
	</header>

	<!-- FEATURES SECTION -->
	<section class="relative z-10 px-6 pb-40 pointer-events-none">
		<div class="max-w-6xl mx-auto space-y-40">
			{#each features as feature, i}
				<div
					class="flex flex-col md:flex-row gap-12 lg:gap-24 items-center {i % 2 === 1
						? 'md:flex-row-reverse'
						: ''} pointer-events-auto"
				>
					<!-- Mockup Side -->
					<div class="flex-1 w-full relative group">
						<!-- Mockup Container -->
						<div class="relative z-10 p-8">
							<!-- THEATER MOCKUP -->
							{#if feature.type === 'theater'}
								<div
									class="bg-white dark:bg-zinc-900 rounded-[2.5rem] p-8 shadow-[0_30px_60px_-15px_rgba(0,0,0,0.08)] dark:shadow-none border border-slate-100 dark:border-zinc-800 transform transition-transform duration-500 group-hover:-translate-y-2"
								>
									<!-- Browser Dots -->
									<div class="flex gap-2 mb-6">
										<div class="w-2.5 h-2.5 rounded-full bg-yellow-400/50"></div>
										<div class="w-2.5 h-2.5 rounded-full bg-green-400/50"></div>
										<div class="w-2.5 h-2.5 rounded-full bg-red-400/50"></div>
									</div>
									<!-- Calendar Grid -->
									<div class="grid grid-cols-7 gap-3">
										{#each Array(14) as _, idx}
											<div
												class="aspect-square rounded-xl {idx === 5
													? 'bg-red-600 shadow-lg shadow-red-500/40'
													: idx % 3 === 0
														? 'bg-red-50 dark:bg-red-900/20'
														: 'bg-slate-50 dark:bg-zinc-800'}"
											></div>
										{/each}
									</div>
									<div class="mt-6 flex gap-3">
										<div class="h-2 w-1/3 bg-slate-100 dark:bg-zinc-800 rounded-full"></div>
										<div class="h-2 w-1/2 bg-slate-100 dark:bg-zinc-800 rounded-full"></div>
									</div>
								</div>
							{/if}

							<!-- 2-SHOT MOCKUP -->
							{#if feature.type === 'twoshot'}
								<div class="relative h-[320px] w-[300px] mx-auto">
									<div
										class="absolute inset-0 bg-white dark:bg-zinc-900 p-4 pb-12 shadow-xl dark:shadow-none dark:border dark:border-zinc-800 rounded-lg rotate-[-6deg] translate-y-4 transition-transform group-hover:rotate-[-12deg] group-hover:-translate-x-4"
									>
										<div class="w-full h-full bg-pink-50 dark:bg-pink-900/10 rounded-sm"></div>
									</div>
									<div
										class="absolute inset-0 bg-white dark:bg-zinc-900 p-4 pb-12 shadow-2xl dark:shadow-none dark:border dark:border-zinc-800 rounded-lg rotate-3 transition-transform group-hover:rotate-6 group-hover:translate-x-4 z-10"
									>
										<div
											class="w-full h-full bg-pink-100 dark:bg-pink-900/20 flex items-center justify-center rounded-sm"
										>
											<Camera class="text-pink-300 dark:text-pink-500/50 w-12 h-12 opacity-50" />
										</div>
										<div
											class="absolute bottom-4 left-0 right-0 text-center font-handwriting text-slate-400 dark:text-slate-500 text-xs"
										>
											24.08.12
										</div>
									</div>
								</div>
							{/if}

							<!-- MEMORIES MOCKUP -->
							{#if feature.type === 'memories'}
								<div
									class="grid grid-cols-2 gap-4 w-[320px] mx-auto transform rotate-3 transition-transform group-hover:rotate-0"
								>
									<div
										class="aspect-[4/3] bg-blue-50 dark:bg-blue-900/10 rounded-2xl shadow-sm"
									></div>
									<div
										class="aspect-square bg-red-50 dark:bg-red-900/10 rounded-2xl shadow-sm translate-y-8"
									></div>
									<div
										class="aspect-square bg-white dark:bg-zinc-900 border border-slate-100 dark:border-zinc-800 rounded-2xl shadow-lg dark:shadow-none -translate-y-8 flex items-center justify-center"
									>
										<Ticket class="text-slate-200 dark:text-zinc-700" />
									</div>
									<div
										class="aspect-[4/3] bg-slate-50 dark:bg-zinc-800 rounded-2xl shadow-sm"
									></div>
								</div>
							{/if}

							<!-- ACHIEVEMENTS MOCKUP -->
							{#if feature.type === 'achievements'}
								<div
									class="relative w-[300px] aspect-square mx-auto flex items-center justify-center"
								>
									<div
										class="absolute inset-0 bg-yellow-100/50 rounded-full blur-3xl animate-pulse"
									></div>
									<div
										class="relative bg-white dark:bg-zinc-900 rounded-[2rem] p-8 shadow-[0_20px_40px_-10px_rgba(0,0,0,0.1)] dark:shadow-none border border-yellow-100 dark:border-yellow-900/20 text-center group-hover:scale-105 transition-transform"
									>
										<div
											class="w-20 h-20 bg-yellow-400 dark:bg-yellow-500 rounded-2xl mx-auto flex items-center justify-center shadow-lg shadow-yellow-500/20 mb-4 text-white"
										>
											<Trophy size={32} />
										</div>
										<div
											class="h-2 w-24 bg-slate-100 dark:bg-zinc-800 rounded-full mx-auto mb-2"
										></div>
										<div class="h-2 w-16 bg-slate-100 dark:bg-zinc-800 rounded-full mx-auto"></div>
										<!-- Star Badge -->
										<div
											class="absolute -top-4 -right-4 w-10 h-10 bg-red-500 text-white rounded-full flex items-center justify-center shadow-lg ring-4 ring-white"
										>
											<Star size={16} fill="white" />
										</div>
									</div>
								</div>
							{/if}
						</div>

						<!-- Hover Background Blob -->
						<div
							class="absolute inset-0 bg-gradient-to-tr from-white/0 to-white/0 group-hover:from-{feature.type ===
							'theater'
								? 'red'
								: feature.type === 'twoshot'
									? 'pink'
									: feature.type === 'memories'
										? 'blue'
										: 'yellow'}-50/50 rounded-[3rem] -z-10 transition-colors duration-500"
						></div>
					</div>

					<!-- Content Side -->
					<div class="flex-1 text-center md:text-left space-y-6">
						<div
							class="inline-flex p-3 rounded-full {feature.iconBg} {feature.color} ring-4 ring-white shadow-lg mb-2"
							style="transform: translate({$mouse.x * 40}px, {$mouse.y * 40}px)"
						>
							<svelte:component this={feature.icon} size={24} />
						</div>
						<h2
							class="text-4xl md:text-5xl font-black text-slate-900 dark:text-white uppercase tracking-tighter"
							style="transform: translate({$mouse.x * 30}px, {$mouse.y * 30}px)"
						>
							{feature.title}
						</h2>
						<p
							class="text-lg text-slate-500 dark:text-slate-400 leading-relaxed font-medium max-w-lg mx-auto md:mx-0"
							style="transform: translate({$mouse.x * 20}px, {$mouse.y * 20}px)"
						>
							{feature.description}
						</p>
					</div>
				</div>
			{/each}
		</div>
	</section>

	<!-- FOOTER -->
	<footer class="py-20 relative z-10 pointer-events-none">
		<div class="text-center space-y-8 pointer-events-auto">
			<div class="flex items-center justify-center gap-3">
				<div
					class="w-10 h-10 rounded-full bg-red-600 flex items-center justify-center text-white shadow-xl shadow-red-500/20 ring-4 ring-white dark:ring-zinc-800"
				>
					<Ticket class="w-5 h-5" />
				</div>
				<span class="font-black text-2xl tracking-tighter text-slate-900 dark:text-white">
					MyPage<span class="text-red-600">48</span>
				</span>
			</div>

			<div
				class="flex items-center justify-center gap-2 text-[10px] sm:text-xs text-slate-400 dark:text-slate-500 uppercase tracking-widest font-bold"
			>
				<span>{$t('landing.footer.copyright', { heart: '❤️' })}</span>
			</div>

			<a
				href="https://github.com/shiyinq/mypage48"
				target="_blank"
				class="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-slate-100 dark:bg-zinc-800 text-slate-600 dark:text-slate-300 text-xs font-bold hover:bg-slate-200 dark:hover:bg-zinc-700 transition-colors"
			>
				<Github size={14} />
				{$t('landing.footer.openSource')}
			</a>

			<p class="text-[9px] text-slate-300 max-w-md mx-auto px-6">
				{$t('landing.footer.disclaimer')}
			</p>
		</div>
	</footer>
</div>

<style>
	@keyframes fadeInUp {
		from {
			opacity: 0;
			transform: translateY(20px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}
	.animate-appear {
		animation: fadeInUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
	}

	/* Font Handwriting for Polaroid */
	.font-handwriting {
		font-family: 'Courier New', Courier, monospace; /* Fallback for now */
	}

	@keyframes float {
		0%,
		100% {
			transform: translateY(0) scale(1);
			opacity: 0.4;
		}
		50% {
			transform: translateY(-20px) scale(1.1);
			opacity: 0.8;
		}
	}
	.animate-float {
		animation-name: float;
		animation-timing-function: ease-in-out;
		animation-iteration-count: infinite;
	}
</style>
