<script lang="ts">
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import LandingNavbar from '$lib/components/landing-page/LandingNavbar.svelte';
	import Footer from '$lib/components/landing-page/Footer.svelte';
	import AnimatedBackground from '$lib/components/common/AnimatedBackground.svelte';
	import { spring } from 'svelte/motion';

	import { isAuthenticated } from '$lib/stores';
	const { t } = useTranslation();

	let mouse = $state(spring({ x: 0, y: 0 }, { stiffness: 0.1, damping: 0.25 }));
	let scrollY = $state(0);
</script>

<SEO title={t('cookies.title')} path="/cookies" description={t('seo.cookies')} />

<div
	class="min-h-screen bg-gradient-to-b from-pink-50/50 via-white to-white dark:from-zinc-950 dark:via-zinc-950 dark:to-zinc-900 relative overflow-hidden font-sans selection:bg-red-500/20"
>
	<!-- Background Elements -->
	<AnimatedBackground interactive={true} bind:mouse bind:scrollY />

	<!-- NAV -->
	{#if !isAuthenticated.value}
		<LandingNavbar showLogin={true} />
	{/if}

	<div class="max-w-3xl mx-auto pb-12 relative z-10 px-6 pt-4 md:pt-6">
		<!-- Header -->
		<div class="space-y-4 text-center mb-8">
			<h1
				class="text-3xl md:text-5xl font-black text-slate-900 dark:text-white tracking-tighter uppercase mb-3"
			>
				{t('cookies.title')}
			</h1>
			<p
				class="text-base md:text-lg text-slate-500 dark:text-slate-400 font-medium max-w-2xl mx-auto uppercase tracking-widest leading-relaxed"
			>
				{t('cookies.subtitle')}
			</p>
		</div>

		<!-- Content -->
		<div class="prose prose-slate dark:prose-invert max-w-none">
			<div
				class="bg-white dark:bg-zinc-900 rounded-[2.5rem] p-8 md:p-10 shadow-[0_30px_60px_-15px_rgba(0,0,0,0.08)] dark:shadow-none border border-slate-100 dark:border-zinc-800 space-y-8"
			>
				<section>
					<h2 class="text-2xl font-bold text-slate-900 dark:text-white mb-4">
						{t('cookies.whatAreCookies.title')}
					</h2>
					<p class="text-slate-600 dark:text-slate-400 leading-relaxed">
						{t('cookies.whatAreCookies.content')}
					</p>
				</section>

				<section>
					<h2 class="text-2xl font-bold text-slate-900 dark:text-white mb-4">
						{t('cookies.howWeUse.title')}
					</h2>
					<p class="text-slate-600 dark:text-slate-400 leading-relaxed mb-4">
						{t('cookies.howWeUse.content')}
					</p>
					<ul
						class="space-y-3 marker:text-red-500 list-disc pl-5 text-slate-600 dark:text-slate-400"
					>
						<li>{t('cookies.howWeUse.items.essential')}</li>
						<li>{t('cookies.howWeUse.items.analytics')}</li>
						<li>{t('cookies.howWeUse.items.preferences')}</li>
					</ul>
				</section>

				<section>
					<h2 class="text-2xl font-bold text-slate-900 dark:text-white mb-4">
						{t('cookies.managing.title')}
					</h2>
					<p class="text-slate-600 dark:text-slate-400 leading-relaxed">
						{t('cookies.managing.content')}
					</p>
				</section>
			</div>
		</div>
	</div>

	<!-- FOOTER -->
	{#if !isAuthenticated.value}
		<Footer />
	{/if}
</div>
