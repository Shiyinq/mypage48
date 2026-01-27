<script lang="ts">
	import { Ticket, ArrowRight } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import LanguageToggle from './LanguageToggle.svelte';
	import LandingPageThemeToggle from './ThemeToggle.svelte';
	import { isAuthenticated } from '$lib/stores';

	export let showLogin = true;
	export let mouse = { x: 0, y: 0 };

	const { t } = useTranslation();
</script>

<nav
	class="relative z-50 flex justify-between items-center p-6 max-w-7xl mx-auto pointer-events-none mb-12"
>
	<a
		href="/"
		class="flex items-center gap-3 group {showLogin
			? 'cursor-default'
			: 'cursor-pointer'} pointer-events-auto"
	>
		<div
			class="w-10 h-10 rounded-full bg-red-600 flex items-center justify-center text-white shadow-xl shadow-red-500/20 ring-4 ring-white dark:ring-zinc-800 transition-transform group-hover:scale-105 duration-300"
		>
			<Ticket class="w-5 h-5" />
		</div>
		<div class="flex flex-col relative">
			<div
				class="absolute inset-0"
				style="transform: translate({mouse.x * 10}px, {mouse.y * 10}px)"
			></div>
			<h1
				class="text-xl font-black tracking-tighter text-slate-900 dark:text-white leading-none relative z-10"
				style="transform: translate({mouse.x * 5}px, {mouse.y * 5}px)"
			>
				MyPage<span class="text-red-600">48</span>
			</h1>
			<span
				class="text-[9px] font-bold text-slate-400 dark:text-slate-500 tracking-[0.2em] uppercase mt-0.5"
				style="transform: translate({mouse.x * 8}px, {mouse.y * 8}px)"
			>
				{$t('landing.nav.subtitle')}
			</span>
		</div>
	</a>
	<div class="flex items-center gap-4 pointer-events-auto">
		<LanguageToggle />
		<LandingPageThemeToggle />
		{#if $isAuthenticated}
			<a
				href="/"
				class="px-6 py-2 rounded-full bg-slate-100 dark:bg-zinc-800 text-slate-900 dark:text-white font-bold text-sm hover:bg-slate-200 dark:hover:bg-zinc-700 transition-all flex items-center gap-2 group"
			>
				{$t('nav.dashboard')}
				<ArrowRight size={14} class="group-hover:translate-x-1 transition-transform" />
			</a>
		{:else if showLogin}
			<a
				href="/login"
				class="px-6 py-2 rounded-full bg-red-600 text-white font-bold text-sm shadow-xl shadow-red-500/30 hover:shadow-red-500/50 hover:-translate-y-0.5 transition-all flex items-center gap-2 group"
			>
				{$t('auth.login.signIn')}
				<ArrowRight size={14} class="group-hover:translate-x-1 transition-transform" />
			</a>
		{/if}
	</div>
</nav>
