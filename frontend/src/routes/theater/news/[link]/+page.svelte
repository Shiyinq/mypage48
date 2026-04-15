<script lang="ts">
	import type { PageData } from './$types';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import { Calendar, ChevronRight, ExternalLink, Share2, Copy } from 'lucide-svelte';
	import { formatDate } from '$lib/i18n';
	import { getExternalMediaUrl, proxyExternalImageUrls } from '$lib/utils/media';
	import ImageLightbox from '$lib/components/common/ImageLightbox.svelte';
	import { showToast } from '$lib/stores';
	import { browser } from '$app/environment';
	import DOMPurify from 'isomorphic-dompurify';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	let item = $derived(data.item);
	let recentNews = $derived(data.recentNews.filter((n) => n.link !== item.link).slice(0, 10));

	const { t, locale } = useTranslation();

	let shareUrl = $derived(browser ? window.location.href : '');
	let shareTitle = $derived(item?.title || '');

	let shareLinks = $derived({
		x: `https://twitter.com/intent/tweet?text=${encodeURIComponent(shareTitle)}&url=${encodeURIComponent(shareUrl)}`,
		facebook: `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl)}`,
		whatsapp: `https://api.whatsapp.com/send?text=${encodeURIComponent(shareTitle + ' ' + shareUrl)}`
	});

	let showLightbox = $state(false);
	let selectedImgSrc = $state('');
	let selectedImgAlt = $state('');

	function openLightbox(src: string, alt: string) {
		selectedImgSrc = src;
		selectedImgAlt = alt;
		showLightbox = true;
	}

	function handleContentClick(e: MouseEvent | KeyboardEvent) {
		if (e instanceof KeyboardEvent && e.key !== 'Enter' && e.key !== ' ') return;
		const target = e.target as HTMLElement;
		if (target.tagName === 'IMG') {
			const img = target as HTMLImageElement;
			openLightbox(img.src, img.alt);
		}
	}

	let processedContent = $derived(DOMPurify.sanitize(proxyExternalImageUrls(item.content_body)));

	function copyLink() {
		if (!browser) return;
		navigator.clipboard.writeText(shareUrl);
		showToast(t('common.copied'), 'success');
	}
</script>

<SEO
	title={item.title}
	path={`/theater/news/${item.link}`}
	description={item.short_description || item.title}
	image={item.background_image ? getExternalMediaUrl(item.background_image) : undefined}
/>

<div class="max-w-5xl mx-auto space-y-6 animate-fade-in pb-12">
	<!-- Breadcrumbs & Header -->
	<div class="mb-8">
		<h1 class="text-3xl md:text-4xl font-extrabold text-red-500 mb-4 leading-tight">
			{item.title}
		</h1>
		<div
			class="flex flex-wrap items-center gap-2 text-sm text-gray-500 dark:text-gray-400 font-medium"
		>
			<a href="/theater" class="hover:text-red-500 transition-colors">Home</a>
			<span class="w-1 h-1 rounded-full bg-gray-300 dark:bg-zinc-600"></span>
			<a href="/theater/news" class="hover:text-red-500 transition-colors">News</a>
			<span class="w-1 h-1 rounded-full bg-gray-300 dark:bg-zinc-600"></span>
			<span class="text-gray-900 dark:text-gray-200 line-clamp-1 break-all">{item.title}</span>
		</div>
	</div>

	<div class="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
		<!-- Main Content (Left) -->
		<main
			class="lg:col-span-2 space-y-6 bg-white dark:bg-zinc-900 rounded-3xl p-4 md:p-10 shadow-sm border border-gray-100 dark:border-white/5"
		>
			{#if item.background_image}
				<button
					onclick={() => openLightbox(getExternalMediaUrl(item.background_image), item.title)}
					class="w-full rounded-2xl overflow-hidden bg-gray-100 dark:bg-zinc-800 shadow-inner group/img cursor-pointer transition-transform hover:scale-[1.01] active:scale-[0.99] duration-500"
				>
					<img
						src={getExternalMediaUrl(item.background_image)}
						alt={item.title}
						class="w-full h-auto object-cover max-h-[500px] transition-all duration-1000 group-hover/img:scale-110"
					/>
				</button>
			{/if}

			<div
				class="flex flex-wrap items-center gap-3 md:gap-4 py-2 border-b border-gray-100 dark:border-zinc-800"
			>
				<span
					class="inline-flex items-center px-2.5 py-1 rounded-md text-[10px] md:text-xs font-bold uppercase {item.category.toLowerCase() ===
					'event'
						? 'bg-red-100 dark:bg-red-500/20 text-red-600 dark:text-red-400'
						: item.category.toLowerCase() === 'theater'
							? 'bg-cyan-100 dark:bg-cyan-500/20 text-cyan-600 dark:text-cyan-400'
							: 'bg-orange-100 dark:bg-orange-500/20 text-orange-600 dark:text-orange-400'} whitespace-nowrap"
				>
					{item.category}
				</span>
				<span
					class="flex items-center gap-1.5 text-xs md:text-sm font-semibold text-gray-500 dark:text-gray-400"
				>
					<Calendar class="w-4 h-4" />
					{formatDate(item.valid_date_from, { day: 'numeric', month: 'long', year: 'numeric' })}
				</span>
			</div>

			<!-- HTML Content -->

			<div
				class="prose prose-red dark:prose-invert prose-responsive-colors max-w-none prose-img:rounded-xl prose-img:cursor-zoom-in hover:prose-img:scale-[1.01] prose-img:transition-transform prose-img:duration-300 prose-a:text-red-500 hover:prose-a:text-red-600 space-y-4 text-gray-800 dark:text-gray-300 leading-relaxed text-sm md:text-base md:p-0 rounded-2xl md:bg-transparent"
				onclick={handleContentClick}
				onkeydown={handleContentClick}
				role="presentation"
			>
				<!-- eslint-disable-next-line svelte/no-at-html-tags -->
				{@html processedContent}
			</div>

			<div
				class="pt-8 mt-8 border-t border-gray-100 dark:border-zinc-800 flex flex-col items-center gap-6"
			>
				<a
					href={`https://jkt48.com/news/${item.link}?lang=${locale.value === 'id' ? 'id' : 'jp'}`}
					target="_blank"
					rel="noopener noreferrer"
					class="inline-flex items-center gap-2 px-8 py-3 bg-red-500 hover:bg-red-600 text-white rounded-full font-bold shadow-md hover:shadow-lg transition-all"
				>
					{t('theater.news.readOriginal')}
					<ExternalLink class="w-4 h-4" />
				</a>

				<div class="flex flex-col items-center gap-3">
					<div class="flex items-center gap-2 text-gray-400">
						<Share2 class="w-3.5 h-3.5" />
						<span class="text-[10px] font-bold uppercase tracking-widest text-gray-400">
							{t('theater.news.share')}
						</span>
					</div>

					<div class="flex items-center gap-3">
						<!-- X (Twitter) -->
						<a
							href={shareLinks.x}
							target="_blank"
							rel="noopener noreferrer"
							class="w-10 h-10 flex items-center justify-center rounded-full bg-zinc-900 text-white hover:scale-110 transition-transform shadow-sm"
							title="Share on X"
						>
							<svg class="w-4 h-4 fill-current" viewBox="0 0 24 24">
								<path
									d="M18.901 1.153h3.68l-8.04 9.19L24 22.846h-7.406l-5.8-7.584-6.638 7.584H.474l8.6-9.83L0 1.154h7.594l5.243 6.932L18.901 1.153ZM17.61 20.644h2.039L6.486 3.24H4.298L17.61 20.644Z"
								/>
							</svg>
						</a>

						<!-- Facebook -->
						<a
							href={shareLinks.facebook}
							target="_blank"
							rel="noopener noreferrer"
							class="w-10 h-10 flex items-center justify-center rounded-full bg-[#1877F2] text-white hover:scale-110 transition-transform shadow-sm"
							title="Share on Facebook"
						>
							<svg class="w-5 h-5 fill-current" viewBox="0 0 24 24">
								<path
									d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.469h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"
								/>
							</svg>
						</a>

						<!-- WhatsApp -->
						<a
							href={shareLinks.whatsapp}
							target="_blank"
							rel="noopener noreferrer"
							class="w-10 h-10 flex items-center justify-center rounded-full bg-[#25D366] text-white hover:scale-110 transition-transform shadow-sm"
							title="Share on WhatsApp"
						>
							<svg class="w-6 h-6 fill-current" viewBox="0 0 24 24">
								<path
									d="M19.077 4.928C17.191 3.041 14.683 2 12.001 2c-5.406 0-9.803 4.397-9.803 9.802 0 1.728.451 3.414 1.304 4.9l-1.387 5.064 5.181-1.358c1.446.787 3.078 1.203 4.704 1.203h.004c5.405 0 9.802-4.397 9.802-9.803 0-2.617-1.02-5.078-2.928-6.98zM12.001 19.818c-1.464 0-2.895-.393-4.14-1.137l-.297-.176-3.078.807.82-2.997-.194-.309c-.819-1.302-1.251-2.816-1.251-4.376 0-4.475 3.64-8.115 8.117-8.115 2.167 0 4.204.844 5.736 2.377 1.531 1.532 2.375 3.569 2.375 5.739 0 4.476-3.64 8.115-8.116 8.115zM16.452 13.911c-.244-.122-1.44-.711-1.663-.792-.222-.081-.384-.122-.544.122-.16.244-.619.792-.759.953-.14.162-.28.182-.524.061-.244-.122-1.03-.38-1.961-1.211-.725-.647-1.214-1.446-1.356-1.691-.143-.244-.015-.376.107-.497.11-.11.244-.284.365-.426.122-.143.162-.244.244-.407.081-.162.04-.305-.02-.426-.061-.122-.544-1.31-.745-1.796-.197-.472-.397-.407-.544-.415-.14-.007-.301-.008-.461-.008-.16 0-.421.061-.641.305-.221.244-.843.824-.843 2.011 0 1.187.863 2.333.984 2.496.122.162 1.698 2.592 4.114 3.633.575.247 1.023.395 1.373.506.577.183 1.102.157 1.517.095.463-.069 1.44-.588 1.643-1.157.202-.569.202-1.056.141-1.157-.061-.1-.223-.162-.466-.284z"
								/>
							</svg>
						</a>

						<!-- Copy Link -->
						<button
							onclick={copyLink}
							class="w-10 h-10 flex items-center justify-center rounded-full bg-gray-100 dark:bg-zinc-800 text-gray-600 dark:text-gray-300 hover:scale-110 transition-transform shadow-sm border border-gray-200 dark:border-zinc-700 cursor-pointer"
							title={t('common.copyLink')}
						>
							<Copy class="w-4 h-4" />
						</button>
					</div>
				</div>
			</div>
		</main>

		<!-- Sidebar (Right) -->
		<aside class="lg:col-span-1 space-y-6">
			<div
				class="bg-white dark:bg-zinc-900 rounded-3xl p-6 shadow-sm border border-gray-100 dark:border-white/5 sticky top-24"
			>
				<div
					class="flex items-center justify-between mb-6 pb-4 border-b border-gray-100 dark:border-zinc-800"
				>
					<h3 class="text-lg font-bold text-gray-900 dark:text-white">
						{t('theater.news.otherNews')}
					</h3>
					<a
						href="/theater/news"
						class="text-xs font-semibold text-red-500 hover:text-red-600 flex items-center gap-0.5"
					>
						{t('theater.news.seeAll')}
						<ChevronRight class="w-3 h-3" />
					</a>
				</div>

				<div class="flex flex-col gap-5">
					{#each recentNews as recent}
						<a
							href={`/theater/news/${recent.link}`}
							class="group flex flex-col gap-1.5 pb-5 border-b border-gray-50 dark:border-zinc-800/50 last:border-0 last:pb-0"
							data-sveltekit-reload
						>
							<div class="flex items-center gap-2 mb-1">
								<span
									class="inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-bold uppercase {recent.category.toLowerCase() ===
									'event'
										? 'bg-red-100 dark:bg-red-500/20 text-red-600 dark:text-red-400'
										: recent.category.toLowerCase() === 'theater'
											? 'bg-cyan-100 dark:bg-cyan-500/20 text-cyan-600 dark:text-cyan-400'
											: 'bg-orange-100 dark:bg-orange-500/20 text-orange-600 dark:text-orange-400'}"
								>
									{recent.category}
								</span>
								<span class="text-gray-300 dark:text-zinc-600">|</span>
								<span class="text-[11px] font-medium text-gray-500 dark:text-gray-400">
									{formatDate(recent.valid_date_from, {
										day: 'numeric',
										month: 'short',
										year: 'numeric'
									})}
								</span>
							</div>
							<h4
								class="text-sm font-bold text-gray-800 dark:text-gray-200 leading-snug group-hover:text-red-500 transition-colors line-clamp-2"
							>
								{recent.title}
							</h4>
						</a>
					{/each}
				</div>
			</div>
		</aside>
	</div>
</div>

<ImageLightbox
	src={selectedImgSrc}
	alt={selectedImgAlt}
	isOpen={showLightbox}
	onClose={() => (showLightbox = false)}
/>
