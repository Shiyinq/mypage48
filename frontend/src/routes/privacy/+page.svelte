<script lang="ts">
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import LandingPageThemeToggle from '$lib/components/landing-page/ThemeToggle.svelte';
	import LanguageToggle from '$lib/components/landing-page/LanguageToggle.svelte';
	import { Ticket, Github } from 'lucide-svelte';

	const { t } = useTranslation();
</script>

<SEO title={$t('privacy.title')} />

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
	</div>

	<!-- NAV -->
	<nav
		class="relative z-50 flex justify-between items-center max-w-7xl mx-auto p-6 mb-12 pointer-events-none"
	>
		<a href="/" class="flex items-center gap-3 group cursor-pointer pointer-events-auto">
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
					{$t('landing.nav.subtitle')}
				</span>
			</div>
		</a>
		<div class="flex items-center gap-4 pointer-events-auto">
			<LanguageToggle />
			<LandingPageThemeToggle />
		</div>
	</nav>

	<div class="max-w-3xl mx-auto space-y-12 relative z-10 px-6 pt-16">
		<!-- Header -->
		<div class="text-center space-y-4">
			<h1 class="text-4xl md:text-5xl font-black text-slate-900 dark:text-white tracking-tight">
				{$t('privacy.title')}
			</h1>
			<p class="text-slate-500 dark:text-slate-400 font-medium">
				{$t('privacy.lastUpdated', { date: '19/01/2026' })}
			</p>
		</div>

		<!-- Content -->
		<div
			class="bg-white dark:bg-zinc-900 rounded-[2.5rem] p-8 md:p-12 shadow-[0_30px_60px_-15px_rgba(0,0,0,0.08)] dark:shadow-none border border-slate-100 dark:border-zinc-800 space-y-8"
		>
			<p class="text-lg text-slate-600 dark:text-slate-300 leading-relaxed">
				{$t('privacy.intro')}
			</p>

			<section class="space-y-4">
				<h2 class="text-2xl font-bold text-slate-900 dark:text-white">
					{$t('privacy.sections.collection.title')}
				</h2>
				<p class="text-slate-600 dark:text-slate-400 leading-relaxed">
					{$t('privacy.sections.collection.content')}
				</p>
			</section>

			<section class="space-y-4">
				<h2 class="text-2xl font-bold text-slate-900 dark:text-white">
					{$t('privacy.sections.usage.title')}
				</h2>
				<p class="text-slate-600 dark:text-slate-400 leading-relaxed">
					{$t('privacy.sections.usage.content')}
				</p>
			</section>

			<section class="space-y-4">
				<h2 class="text-2xl font-bold text-slate-900 dark:text-white">
					{$t('privacy.sections.sharing.title')}
				</h2>
				<p class="text-slate-600 dark:text-slate-400 leading-relaxed">
					{$t('privacy.sections.sharing.content')}
				</p>
			</section>

			<section class="space-y-4">
				<h2 class="text-2xl font-bold text-slate-900 dark:text-white">
					{$t('privacy.sections.ai.title')}
				</h2>
				<p class="text-slate-600 dark:text-slate-400 leading-relaxed">
					{$t('privacy.sections.ai.content')}
				</p>
			</section>
		</div>
	</div>

	<!-- FOOTER -->
	<footer class="py-20 mt-32 relative z-10 pointer-events-none">
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

			<div class="flex items-center justify-center gap-6 flex-wrap px-6">
				<a
					href="/about"
					class="text-xs text-slate-500 dark:text-slate-400 hover:text-red-600 dark:hover:text-red-400 transition-colors"
				>
					{$t('landing.footer.about')}
				</a>
				<a
					href="/privacy"
					class="text-xs text-slate-500 dark:text-slate-400 hover:text-red-600 dark:hover:text-red-400 transition-colors"
				>
					{$t('landing.footer.privacy')}
				</a>
				<a
					href="/terms"
					class="text-xs text-slate-500 dark:text-slate-400 hover:text-red-600 dark:hover:text-red-400 transition-colors"
				>
					{$t('landing.footer.terms')}
				</a>
			</div>

			<p class="text-[9px] text-slate-300 max-w-md mx-auto px-6">
				{$t('landing.footer.disclaimer')}
			</p>
		</div>
	</footer>
</div>
