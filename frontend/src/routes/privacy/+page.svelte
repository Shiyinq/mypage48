<script lang="ts">
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import LandingNavbar from '$lib/components/landing-page/LandingNavbar.svelte';
	import Footer from '$lib/components/landing-page/Footer.svelte';

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
	<LandingNavbar showLogin={false} />

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
	<Footer />
</div>
