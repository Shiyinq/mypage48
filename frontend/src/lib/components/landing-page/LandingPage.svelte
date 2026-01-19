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
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import LandingPageThemeToggle from './ThemeToggle.svelte';

	const { t } = useTranslation();

	const features = [
		{
			title: 'THEATER',
			description:
				"Track every JKT48 theater show you attend. Monitor your spending, seat history, and watch your fan level grow. See which setlists you've mastered.",
			icon: Ticket,
			color: 'text-red-500',
			iconBg: 'bg-red-50',
			type: 'theater'
		},
		{
			title: '2-SHOT',
			description:
				"Keep a digital collection of your 2-shot polaroids. Analyze your collection by member and see who's really your oshi with visual breakdown stats.",
			icon: Camera,
			color: 'text-pink-500',
			iconBg: 'bg-pink-50',
			type: 'twoshot'
		},
		{
			title: 'MEMORIES',
			description:
				'A beautiful digital scrapbook for your fan journey. Store photos, tickets, and special moments in one place. Relive the excitement of every event.',
			icon: Users,
			color: 'text-blue-500',
			iconBg: 'bg-blue-50',
			type: 'memories'
		},
		{
			title: 'ACHIEVEMENTS',
			description:
				'Unlock badges and milestones as you support JKT48. From "First Show" to "Legendary Fan", track your progress and show off your loyalty.',
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

		<!-- Decor Elements -->
		<div class="absolute top-20 left-10 text-pink-200 animate-pulse delay-700">
			<Sparkles size={48} />
		</div>
		<div class="absolute top-40 right-10 text-red-200 animate-pulse delay-300">
			<Star size={32} />
		</div>
	</div>

	<!-- NAV -->
	<nav class="relative z-50 flex justify-between items-center p-6 max-w-7xl mx-auto">
		<div class="flex items-center gap-3 group cursor-default">
			<div
				class="w-10 h-10 rounded-full bg-red-600 flex items-center justify-center text-white shadow-xl shadow-red-500/20 ring-4 ring-white dark:ring-zinc-800 transition-transform group-hover:scale-105 duration-300"
			>
				<Ticket class="w-5 h-5" />
			</div>
			<div class="flex flex-col">
				<h1 class="text-xl font-black tracking-tighter text-slate-900 dark:text-white leading-none">
					MyPage<span class="text-red-600">48</span>
				</h1>
				<span
					class="text-[9px] font-bold text-slate-400 dark:text-slate-500 tracking-[0.2em] uppercase mt-0.5"
				>
					JKT48 Theater Tracker
				</span>
			</div>
		</div>
		<div class="flex items-center gap-4">
			<LandingPageThemeToggle />
			<a
				href="/login"
				class="px-6 py-2 rounded-full bg-red-600 text-white font-bold text-sm shadow-xl shadow-red-500/30 hover:shadow-red-500/50 hover:-translate-y-0.5 transition-all flex items-center gap-2 group"
			>
				Login <ArrowRight size={14} class="group-hover:translate-x-1 transition-transform" />
			</a>
		</div>
	</nav>

	<!-- HERO -->
	<header class="relative z-10 pt-16 pb-32 px-6 text-center max-w-5xl mx-auto">
		<!-- Pill -->
		<div
			class="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white dark:bg-zinc-900 border border-red-100 dark:border-red-900/30 shadow-sm dark:shadow-none mb-12 opacity-0 animate-appear"
		>
			<span class="relative flex h-2 w-2">
				<span
					class="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"
				></span>
				<span class="relative inline-flex rounded-full h-2 w-2 bg-red-600"></span>
			</span>
			<span
				class="text-[10px] font-bold text-slate-400 dark:text-slate-400 tracking-[0.2em] uppercase"
				>Fan Made Project</span
			>
		</div>

		<h1
			class="text-6xl md:text-8xl font-black tracking-tighter text-slate-900 dark:text-white mb-8 leading-[0.9] opacity-0 animate-appear"
			style="animation-delay: 100ms;"
		>
			Your Ultimate <br />
			<span class="text-transparent bg-clip-text bg-gradient-to-r from-red-600 to-pink-500">
				JKT48 Companion
			</span>
		</h1>

		<p
			class="text-lg md:text-xl text-slate-500 dark:text-slate-400 mb-12 max-w-2xl mx-auto font-medium leading-relaxed opacity-0 animate-appear"
			style="animation-delay: 200ms;"
		>
			Track shows, collect 2-shots, and celebrate your fandom journey with <span
				class="text-slate-800 dark:text-slate-200 font-bold decoration-red-200 decoration-2 underline-offset-4"
				>premium analytics</span
			>
			and a beautiful personal dashboard.
		</p>

		<div
			class="flex flex-col items-center justify-center opacity-0 animate-appear"
			style="animation-delay: 300ms;"
		>
			<a
				href="/register"
				class="group relative inline-flex items-center justify-center gap-3 px-8 py-4 rounded-xl bg-red-600 text-white font-bold text-base shadow-xl shadow-red-500/30 hover:shadow-red-500/50 hover:-translate-y-1 transition-all duration-300"
			>
				Get Started <Rocket size={20} class="group-hover:rotate-12 transition-transform" />
			</a>
			<p class="mt-6 text-[10px] font-bold text-slate-300 uppercase tracking-[0.3em]">
				Open Source • No Ads • Fan Made
			</p>
		</div>
	</header>

	<!-- FEATURES SECTION -->
	<section class="relative z-10 px-6 pb-40">
		<div class="max-w-6xl mx-auto space-y-40">
			{#each features as feature, i}
				<div
					class="flex flex-col md:flex-row gap-12 lg:gap-24 items-center {i % 2 === 1
						? 'md:flex-row-reverse'
						: ''}"
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
						>
							<svelte:component this={feature.icon} size={24} />
						</div>
						<h2
							class="text-4xl md:text-5xl font-black text-slate-900 dark:text-white uppercase tracking-tighter"
						>
							{feature.title}
						</h2>
						<p
							class="text-lg text-slate-500 dark:text-slate-400 leading-relaxed font-medium max-w-lg mx-auto md:mx-0"
						>
							{feature.description}
						</p>
					</div>
				</div>
			{/each}
		</div>
	</section>

	<!-- FOOTER -->
	<footer class="py-20 relative z-10">
		<div class="text-center space-y-8">
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
				<span
					>&copy; {new Date().getFullYear()} Crafted with <span class="text-red-500">❤️</span> for the
					JKT48 Family</span
				>
			</div>

			<a
				href="https://github.com/shiyinq/mypage48"
				target="_blank"
				class="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-slate-100 dark:bg-zinc-800 text-slate-600 dark:text-slate-300 text-xs font-bold hover:bg-slate-200 dark:hover:bg-zinc-700 transition-colors"
			>
				<Github size={14} />
				OPEN SOURCE PROJECT
			</a>

			<p class="text-[9px] text-slate-300 max-w-md mx-auto px-6">
				This is a fan-made project and is not affiliated with or endorsed by official JKT48
				management company.
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
</style>
