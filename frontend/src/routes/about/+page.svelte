<script lang="ts">
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import { Heart, Users, Github } from 'lucide-svelte';
	import LandingNavbar from '$lib/components/landing-page/LandingNavbar.svelte';
	import Footer from '$lib/components/landing-page/Footer.svelte';

	const { t } = useTranslation();
</script>

<SEO title={$t('about.title')} />

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
				{$t('about.title')}
			</h1>
		</div>

		<!-- Content -->
		<div class="grid gap-8">
			<!-- Mission -->
			<div
				class="bg-white dark:bg-zinc-900 rounded-[2.5rem] p-8 md:p-10 shadow-[0_30px_60px_-15px_rgba(0,0,0,0.08)] dark:shadow-none border border-slate-100 dark:border-zinc-800 flex items-start gap-6 group hover:-translate-y-1 transition-transform duration-300"
			>
				<div
					class="p-4 bg-red-50 dark:bg-red-900/20 rounded-2xl text-red-600 dark:text-red-400 shrink-0 ring-4 ring-white dark:ring-zinc-800 shadow-xl shadow-red-500/10 group-hover:bg-red-600 group-hover:text-white transition-colors duration-300"
				>
					<Heart size={32} />
				</div>
				<div class="space-y-3">
					<h2 class="text-2xl font-bold text-slate-900 dark:text-white">
						{$t('about.mission.title')}
					</h2>
					<p class="text-slate-600 dark:text-slate-400 leading-relaxed">
						{$t('about.mission.content')}
					</p>
				</div>
			</div>

			<!-- Team -->
			<div
				class="bg-white dark:bg-zinc-900 rounded-[2.5rem] p-8 md:p-10 shadow-[0_30px_60px_-15px_rgba(0,0,0,0.08)] dark:shadow-none border border-slate-100 dark:border-zinc-800 flex items-start gap-6 group hover:-translate-y-1 transition-transform duration-300"
			>
				<div
					class="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-2xl text-blue-600 dark:text-blue-400 shrink-0 ring-4 ring-white dark:ring-zinc-800 shadow-xl shadow-blue-500/10 group-hover:bg-blue-600 group-hover:text-white transition-colors duration-300"
				>
					<Users size={32} />
				</div>
				<div class="space-y-3">
					<h2 class="text-2xl font-bold text-slate-900 dark:text-white">
						{$t('about.team.title')}
					</h2>
					<p class="text-slate-600 dark:text-slate-400 leading-relaxed">
						{$t('about.team.content')}
					</p>
				</div>
			</div>
			<!-- Open Source -->
			<div
				class="bg-white dark:bg-zinc-900 rounded-[2.5rem] p-8 md:p-10 shadow-[0_30px_60px_-15_rgba(0,0,0,0.08)] dark:shadow-none border border-slate-100 dark:border-zinc-800 flex items-start gap-6 group hover:-translate-y-1 transition-transform duration-300"
			>
				<div
					class="p-4 bg-slate-50 dark:bg-slate-800/50 rounded-2xl text-slate-600 dark:text-slate-400 shrink-0 ring-4 ring-white dark:ring-zinc-800 shadow-xl shadow-slate-500/10 group-hover:bg-slate-900 dark:group-hover:bg-white group-hover:text-white dark:group-hover:text-zinc-900 transition-colors duration-300"
				>
					<Github size={32} />
				</div>
				<div class="space-y-3">
					<h2 class="text-2xl font-bold text-slate-900 dark:text-white">
						{$t('about.openSource.title')}
					</h2>
					<p class="text-slate-600 dark:text-slate-400 leading-relaxed">
						{@html $t('about.openSource.content', {
							githubLink:
								'<a href="https://github.com/shiyinq/mypage48" target="_blank" class="text-red-600 font-bold hover:underline">GitHub</a>'
						})}
					</p>
				</div>
			</div>
		</div>
	</div>

	<!-- FOOTER -->
	<Footer />
</div>
