<script lang="ts">
	import { fade } from 'svelte/transition';
	import {
		TvMinimalPlay,
		ShieldAlert,
		ExternalLink,
		ArrowLeft,
		Tv,
		LayoutGrid,
		RotateCcw,
		History,
		Image as ImageIcon
	} from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	const { t } = useTranslation();

	interface Props {
		backPath?: string;
	}

	let { backPath = '/' }: Props = $props();

	const features = $derived([
		{ key: 'featureLive' as const, icon: Tv, color: 'bg-red-400' },
		{ key: 'featureMultiview' as const, icon: LayoutGrid, color: 'bg-blue-400' },
		{ key: 'featureReplay' as const, icon: RotateCcw, color: 'bg-purple-400' },
		{ key: 'featureHistory' as const, icon: History, color: 'bg-amber-400' },
		{ key: 'featurePC' as const, icon: ImageIcon, color: 'bg-emerald-400' }
	]);
</script>

<div class="flex flex-col h-screen w-full relative overflow-hidden bg-slate-50 dark:bg-zinc-950">
	<!-- Header -->
	<div
		class="fixed top-0 left-0 right-0 w-full z-[10000] border-b border-black/5 dark:border-white/5 bg-white/85 dark:bg-zinc-950/60 backdrop-blur-xl"
	>
		<div
			class="max-w-7xl mx-auto w-full h-16 flex items-center justify-between px-4 sm:px-6 lg:px-8"
		>
			<a
				href={backPath}
				class="flex items-center gap-2 sm:gap-3 text-slate-900 dark:text-white hover:text-red-600 transition-colors cursor-pointer inline-flex group"
			>
				<div
					class="w-8 h-8 flex items-center justify-center rounded-full bg-white dark:bg-zinc-800 shadow-sm border border-gray-200 dark:border-zinc-700 group-hover:border-red-200 dark:group-hover:border-red-900 group-hover:shadow-md transition-all"
				>
					<ArrowLeft
						size={16}
						class="shrink-0 text-slate-500 dark:text-slate-400 group-hover:text-red-600 dark:group-hover:text-red-500"
					/>
				</div>
				<span class="font-extrabold tracking-tight text-lg whitespace-nowrap"
					>Oshi <span class="text-red-600 italic">Live</span></span
				>
			</a>
		</div>
	</div>

	<!-- Content -->
	<div class="flex-1 flex items-center justify-center px-4 pt-16 overflow-y-auto" in:fade>
		<div class="max-w-lg w-full text-center space-y-8 py-8">
			<!-- Icon -->
			<div class="flex justify-center">
				<div
					class="relative w-28 h-28 rounded-full bg-red-50 dark:bg-red-950/30 flex items-center justify-center"
				>
					<TvMinimalPlay size={52} class="text-red-400 dark:text-red-500" />
					<div
						class="absolute -bottom-1 -right-1 w-10 h-10 rounded-full bg-amber-50 dark:bg-amber-950/40 flex items-center justify-center border-4 border-slate-50 dark:border-zinc-950"
					>
						<ShieldAlert size={18} class="text-amber-500 dark:text-amber-400" />
					</div>
				</div>
			</div>

			<!-- Title -->
			<div class="space-y-3">
				<h1 class="text-2xl sm:text-3xl font-black text-slate-900 dark:text-white">
					{t('liveDisabled.title')}
				</h1>
				<p
					class="text-slate-500 dark:text-slate-400 text-sm sm:text-base leading-relaxed font-medium"
				>
					{t('liveDisabled.description')}
				</p>
			</div>

			<!-- Features Card -->
			<div
				class="bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 rounded-2xl p-5 text-left space-y-3 shadow-sm"
			>
				<p class="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
					{t('liveDisabled.featuresLabel')}
				</p>
				<ul class="space-y-2.5 text-sm text-slate-600 dark:text-slate-400">
					{#each features as feature}
						<li class="flex items-start gap-2.5">
							<span class="mt-1.5 w-1.5 h-1.5 rounded-full {feature.color} shrink-0"></span>
							<span>{t(`liveDisabled.${feature.key}`)}</span>
						</li>
					{/each}
				</ul>
			</div>

			<!-- Watch Official Note -->
			<p class="text-slate-500 dark:text-slate-400 text-sm font-medium leading-relaxed">
				{t('liveDisabled.infoWatchOfficial')}
				<a
					href="https://www.idn.app/"
					target="_blank"
					rel="noopener noreferrer"
					class="text-red-600 dark:text-red-400 font-bold hover:underline"
					>{t('liveDisabled.watchOfficialLink')}</a
				>.
			</p>

			<!-- CTA -->
			<div class="flex flex-col sm:flex-row gap-3 justify-center">
				<a
					href="https://www.idn.app/info/terms-of-services"
					target="_blank"
					rel="noopener noreferrer"
					class="inline-flex items-center justify-center gap-2 px-5 py-2.5 text-sm font-bold rounded-xl border border-slate-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-zinc-700 transition-all shadow-sm"
				>
					<ExternalLink size={14} />
					{t('liveDisabled.readTos')}
				</a>
				<a
					href={backPath}
					class="inline-flex items-center justify-center gap-2 px-5 py-2.5 text-sm font-bold rounded-xl bg-red-600 hover:bg-red-700 text-white transition-all shadow-sm"
				>
					<ArrowLeft size={14} />
					{t('liveDisabled.goBack')}
				</a>
			</div>
		</div>
	</div>
</div>
