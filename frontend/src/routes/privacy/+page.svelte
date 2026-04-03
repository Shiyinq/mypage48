<script lang="ts">
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import LandingNavbar from '$lib/components/landing-page/LandingNavbar.svelte';
	import Footer from '$lib/components/landing-page/Footer.svelte';
	import AnimatedBackground from '$lib/components/common/AnimatedBackground.svelte';
	import { spring } from 'svelte/motion';

	const { t } = useTranslation();

	let mouse = spring({ x: 0, y: 0 }, { stiffness: 0.1, damping: 0.25 });
	let scrollY = 0;
</script>

<SEO title={$t('privacy.title')} />

<svelte:window bind:scrollY />


<div
	class="min-h-screen bg-gradient-to-b from-pink-50/50 via-white to-white dark:from-zinc-950 dark:via-zinc-950 dark:to-zinc-900 relative overflow-hidden font-sans selection:bg-red-500/20"
>
	<!-- Background Elements -->
	<AnimatedBackground interactive={true} bind:mouse bind:scrollY />



	<!-- NAV -->
	<LandingNavbar showLogin={false} />

	<div class="max-w-3xl mx-auto pb-12 relative z-10 px-6 pt-4 md:pt-6">
		<!-- Header -->
		<div class="text-center space-y-4 mb-8">
			<h1 class="text-3xl md:text-5xl font-black text-slate-900 dark:text-white tracking-tighter uppercase mb-3">
				{$t('privacy.title')}
			</h1>
			<p class="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-[0.2em]">
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
