<script lang="ts">
	import type { PageData } from './$types';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import { Calendar, ChevronRight, ExternalLink, Share2, Copy, MoveLeft } from 'lucide-svelte';
	import { formatDate } from '$lib/i18n';
	import { getExternalMediaUrl, proxyExternalImageUrls } from '$lib/utils/media';
	import ImageLightbox from '$lib/components/common/ImageLightbox.svelte';
	import { showToast } from '$lib/stores';
	import { browser } from '$app/environment';

	export let data: PageData;

	$: item = data.item;
	$: recentNews = data.recentNews.filter((n) => n.link !== item.link).slice(0, 5);

	const { t, locale } = useTranslation();

	$: shareUrl = browser ? window.location.href : '';
	$: shareTitle = item?.title || '';

	$: shareLinks = {
		x: `https://twitter.com/intent/tweet?text=${encodeURIComponent(shareTitle)}&url=${encodeURIComponent(shareUrl)}`,
		facebook: `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl)}`,
		whatsapp: `https://api.whatsapp.com/send?text=${encodeURIComponent(shareTitle + ' ' + shareUrl)}`
	};

	let showLightbox = false;
	let selectedImgSrc = '';
	let selectedImgAlt = '';

	function openLightbox(src: string, alt: string) {
		selectedImgSrc = src;
		selectedImgAlt = alt;
		showLightbox = true;
	}

	function handleContentClick(e: MouseEvent) {
		const target = e.target as HTMLElement;
		if (target.tagName === 'IMG') {
			const img = target as HTMLImageElement;
			openLightbox(img.src, img.alt);
		}
	}

	$: processedContent = proxyExternalImageUrls(item.content_body);

	function copyLink() {
		if (!browser) return;
		navigator.clipboard.writeText(shareUrl);
		showToast($t('common.copied'), 'success');
	}
</script>

<SEO
	title={item.title}
	path={`/jkt48/news/${item.link}`}
	description={item.short_description || item.title}
	image={item.background_image ? getExternalMediaUrl(item.background_image) : undefined}
	keywords={`${item.title}, JKT48 News, ${item.category}, MyPage48, JKT48 Theater`}
/>

<div class="max-w-4xl mx-auto space-y-8 animate-fade-in pb-20">
	<!-- Header / Back -->
	<div class="space-y-6">
		<a
			href="/jkt48/news"
			class="inline-flex items-center gap-2 text-sm font-bold text-slate-400 hover:text-red-500 transition-colors group"
		>
			<MoveLeft class="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
			{$t('common.back') || 'Back'}
		</a>

		<h1
			class="text-3xl md:text-5xl font-black text-slate-900 dark:text-white leading-tight uppercase tracking-tight"
		>
			{item.title}
		</h1>

		<div
			class="flex flex-wrap items-center gap-3 md:gap-4 py-4 border-y border-slate-100 dark:border-white/5"
		>
			<span
				class="inline-flex items-center px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest shadow-sm {item.category.toLowerCase() ===
				'event'
					? 'bg-red-600 text-white'
					: item.category.toLowerCase() === 'theater'
						? 'bg-cyan-600 text-white'
						: 'bg-orange-600 text-white'} whitespace-nowrap"
			>
				{item.category}
			</span>
			<span
				class="flex items-center gap-1.5 text-xs font-bold text-slate-400 uppercase tracking-wider"
			>
				<Calendar class="w-4 h-4" />
				{$formatDate(item.valid_date_from, { day: 'numeric', month: 'long', year: 'numeric' })}
			</span>
		</div>
	</div>

	<!-- Content Area -->
	<main class="space-y-8">
		{#if item.background_image}
			<!-- svelte-ignore a11y-click-events-have-key-events -->
			<button
				on:click={() => openLightbox(getExternalMediaUrl(item.background_image), item.title)}
				class="w-full rounded-2xl md:rounded-[2.5rem] overflow-hidden bg-gray-100 dark:bg-zinc-800 shadow-2xl group/img cursor-pointer transition-transform hover:scale-[1.012] active:scale-[0.99] duration-500"
			>
				<img
					src={getExternalMediaUrl(item.background_image)}
					alt={item.title}
					class="w-full h-auto object-cover max-h-[400px] md:max-h-[600px] transition-all duration-1000 group-hover/img:scale-110"
				/>
			</button>
		{/if}

		<!-- svelte-ignore a11y-click-events-have-key-events -->
		<div
			class="prose prose-red dark:prose-invert prose-responsive-colors max-w-none prose-img:rounded-2xl md:prose-img:rounded-3xl prose-img:cursor-zoom-in prose-img:shadow-xl hover:prose-img:scale-[1.02] prose-img:transition-all prose-img:duration-500 prose-a:text-red-500 hover:prose-a:text-red-600 space-y-4 md:space-y-6 text-slate-800 dark:text-slate-300 leading-relaxed text-sm md:text-base md:text-lg font-medium bg-white dark:bg-zinc-900/50 p-5 md:p-10 rounded-2xl md:rounded-[2.5rem] border border-gray-100 dark:border-white/5"
			on:click={handleContentClick}
			role="presentation"
		>
			{@html processedContent}
		</div>

		<!-- Share Actions -->
		<div
			class="flex flex-col items-center gap-6 py-12 border-t border-slate-100 dark:border-white/10 mt-12"
		>
			<div class="flex flex-col items-center gap-2">
				<span class="text-[10px] font-black uppercase tracking-widest text-slate-400">
					{$t('theater.news.share')}
				</span>
			</div>

			<div class="flex items-center gap-4">
				<a
					href={shareLinks.x}
					target="_blank"
					rel="noopener noreferrer"
					class="w-12 h-12 flex items-center justify-center rounded-full bg-slate-900 text-white hover:scale-110 transition-transform shadow-lg"
					title="Share on X"
				>
					<svg class="w-5 h-5 fill-current" viewBox="0 0 24 24">
						<path
							d="M18.901 1.153h3.68l-8.04 9.19L24 22.846h-7.406l-5.8-7.584-6.638 7.584H.474l8.6-9.83L0 1.154h7.594l5.243 6.932L18.901 1.153ZM17.61 20.644h2.039L6.486 3.24H4.298L17.61 20.644Z"
						/>
					</svg>
				</a>

				<a
					href={shareLinks.facebook}
					target="_blank"
					rel="noopener noreferrer"
					class="w-12 h-12 flex items-center justify-center rounded-full bg-[#1877F2] text-white hover:scale-110 transition-transform shadow-lg"
					title="Share on Facebook"
				>
					<svg class="w-6 h-6 fill-current" viewBox="0 0 24 24">
						<path
							d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.469h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"
						/>
					</svg>
				</a>

				<a
					href={shareLinks.whatsapp}
					target="_blank"
					rel="noopener noreferrer"
					class="w-12 h-12 flex items-center justify-center rounded-full bg-[#25D366] text-white hover:scale-110 transition-transform shadow-lg"
					title="Share on WhatsApp"
				>
					<svg class="w-7 h-7 fill-current" viewBox="0 0 24 24">
						<path
							d="M19.077 4.928C17.191 3.041 14.683 2 12.001 2c-5.406 0-9.803 4.397-9.803 9.802 0 1.728.451 3.414 1.304 4.9l-1.387 5.064 5.181-1.358c1.446.787 3.078 1.203 4.704 1.203h.004c5.405 0 9.802-4.397 9.802-9.803 0-2.617-1.02-5.078-2.928-6.98zM12.001 19.818c-1.464 0-2.895-.393-4.14-1.137l-.297-.176-3.078.807.82-2.997-.194-.309c-.819-1.302-1.251-2.816-1.251-4.376 0-4.475 3.64-8.115 8.117-8.115 2.167 0 4.204.844 5.736 2.377 1.531 1.532 2.375 3.569 2.375 5.739 0 4.476-3.64 8.115-8.116 8.115zM16.452 13.911c-.244-.122-1.44-.711-1.663-.792-.222-.081-.384-.122-.544.122-.16.244-.619.792-.759.953-.14.162-.28.182-.524.061-.244-.122-1.03-.38-1.961-1.211-.725-.647-1.214-1.446-1.356-1.691-.143-.244-.015-.376.107-.497.11-.11.244-.284.365-.426.122-.143.162-.244.244-.407.081-.162.04-.305-.02-.426-.061-.122-.544-1.31-.745-1.796-.197-.472-.397-.407-.544-.415-.14-.007-.301-.008-.461-.008-.16 0-.421.061-.641.305-.221.244-.843.824-.843 2.011 0 1.187.863 2.333.984 2.496.122.162 1.698 2.592 4.114 3.633.575.247 1.023.395 1.373.506.577.183 1.102.157 1.517.095.463-.069 1.44-.588 1.643-1.157.202-.569.202-1.056.141-1.157-.061-.1-.223-.162-.466-.284z"
						/>
					</svg>
				</a>

				<button
					on:click={copyLink}
					class="w-12 h-12 flex items-center justify-center rounded-full bg-slate-100 dark:bg-zinc-800 text-slate-600 dark:text-slate-300 hover:scale-110 transition-transform shadow-md border border-slate-200 dark:border-zinc-700 cursor-pointer"
					title={$t('common.copyLink')}
				>
					<Copy class="w-5 h-5" />
				</button>
			</div>
		</div>

		<!-- Read Original -->
		<div class="flex justify-center pb-20">
			<a
				href={`https://jkt48.com/news/${item.link}?lang=${$locale === 'id' ? 'id' : 'jp'}`}
				target="_blank"
				rel="noopener noreferrer"
				class="inline-flex items-center gap-3 px-10 py-4 bg-red-600 hover:bg-red-700 text-white rounded-full font-black shadow-xl hover:shadow-2xl transition-all uppercase tracking-widest text-sm"
			>
				{$t('theater.news.readOriginal')}
				<ExternalLink class="w-5 h-5" />
			</a>
		</div>
	</main>

	<!-- Other News -->
	{#if recentNews.length > 0}
		<section class="space-y-8 pt-12 border-t border-slate-100 dark:border-white/10">
			<div class="flex items-center justify-between">
				<h3 class="text-2xl font-black text-slate-900 dark:text-white uppercase tracking-tight">
					{$t('theater.news.otherNews')}
				</h3>
				<a
					href="/jkt48/news"
					class="text-sm font-bold text-red-500 hover:text-red-600 flex items-center gap-1"
				>
					{$t('theater.news.seeAll')}
					<ChevronRight class="w-4 h-4" />
				</a>
			</div>

			<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
				{#each recentNews as recent}
					<a
						href={`/jkt48/news/${recent.link}`}
						class="group bg-white dark:bg-zinc-900/50 p-6 rounded-[2rem] border border-gray-100 dark:border-white/5 hover:shadow-xl transition-all"
						data-sveltekit-reload
					>
						<div class="flex items-center gap-3 mb-4">
							<span
								class="inline-flex items-center px-2 py-0.5 rounded-full text-[9px] font-black uppercase tracking-widest shadow-sm {recent.category.toLowerCase() ===
								'event'
									? 'bg-red-600 text-white'
									: recent.category.toLowerCase() === 'theater'
										? 'bg-cyan-600 text-white'
										: 'bg-orange-600 text-white'}"
							>
								{recent.category}
							</span>
							<span class="text-[11px] font-bold text-slate-400">
								{$formatDate(recent.valid_date_from, {
									day: 'numeric',
									month: 'short',
									year: 'numeric'
								})}
							</span>
						</div>
						<h4
							class="text-base font-black text-slate-900 dark:text-slate-100 leading-tight group-hover:text-red-500 transition-colors line-clamp-2 uppercase"
						>
							{recent.title}
						</h4>
					</a>
				{/each}
			</div>
		</section>
	{/if}
</div>

<ImageLightbox
	src={selectedImgSrc}
	alt={selectedImgAlt}
	isOpen={showLightbox}
	onClose={() => (showLightbox = false)}
/>

<style>
	:global(.animate-fade-in) {
		animation: fadeIn 0.8s ease-out forwards;
	}

	@keyframes fadeIn {
		from {
			opacity: 0;
			transform: translateY(20px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}
</style>
