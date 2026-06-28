<script lang="ts">
	import type { PageData } from './$types';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import {
		Calendar,
		ExternalLink,
		Share2,
		Copy,
		PanelLeft,
		PanelLeftClose,
		ZoomIn
	} from 'lucide-svelte';
	import { fade } from 'svelte/transition';
	import { navigating } from '$app/stores';
	import { formatDate } from '$lib/i18n';
	import { getExternalMediaUrl, proxyExternalImageUrls } from '$lib/utils/media';
	import { OptimizedImage } from '$lib/components/common';
	import ImageLightbox from '$lib/components/common/ImageLightbox.svelte';
	import { showToast } from '$lib/stores';
	import { browser } from '$app/environment';
	import { goto } from '$app/navigation';
	import { pageHeaderStore } from '$lib/stores';
	import DOMPurify from 'isomorphic-dompurify';
	import { onMount } from 'svelte';
	import { newsStore, newsList } from '$lib/stores/news.svelte';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	let item = $derived(data.item);

	let innerWidth = $state(0);
	let isSidebarVisible = $state(browser ? window.innerWidth >= 768 : true);
	let mainContentEl = $state<HTMLElement | null>(null);

	// Mobile behavior
	$effect(() => {
		if (innerWidth < 768) {
			isSidebarVisible = false;
		} else {
			isSidebarVisible = true;
		}
	});

	function toggleSidebar() {
		isSidebarVisible = !isSidebarVisible;
	}

	onMount(() => {
		if (newsList.value.length === 0) {
			newsStore.load(1);
		}
	});

	$effect(() => {
		if (item) {
			pageHeaderStore.set({
				title: item.title,
				theme: 'red',
				showBackButton: true,
				handleBack: () => goto('/theater/news')
			});
		} else {
			pageHeaderStore.set({
				title: t('theater.news.title') || 'News',
				theme: 'red',
				showBackButton: true,
				handleBack: () => goto('/theater/news')
			});
		}
		return () => pageHeaderStore.reset();
	});

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

<svelte:window bind:innerWidth />

<div
	class="h-[calc(100vh-64px)] flex flex-col bg-slate-50/50 dark:bg-zinc-900/40 overflow-hidden relative"
>
	<div class="flex-1 flex flex-col md:flex-row overflow-hidden relative">
		<!-- Mobile Sidebar Backdrop -->
		{#if isSidebarVisible && innerWidth < 768}
			<button
				onclick={toggleSidebar}
				class="fixed inset-0 bg-black/40 backdrop-blur-sm z-[55] md:hidden transition-opacity"
				aria-label="Close Sidebar"
				transition:fade={{ duration: 200 }}
			></button>
		{/if}

		<!-- Desktop Content Spacer -->
		{#if innerWidth >= 768}
			<div
				class="hidden md:block transition-all duration-300 ease-in-out shrink-0 overflow-hidden"
				style="width: {isSidebarVisible ? '256px' : '0px'}; opacity: {isSidebarVisible
					? '1'
					: '0'};"
			></div>
		{/if}

		<!-- Sidebar (Left) -->
		<aside
			class="fixed md:absolute top-0 bottom-0 left-0 z-[60] md:z-10 bg-white md:bg-white/80 dark:bg-zinc-900 md:dark:bg-zinc-900/80 backdrop-blur-md border-r border-gray-100 dark:border-white/5 shadow-2xl md:shadow-none w-full md:w-64 transition-transform duration-300 ease-in-out flex flex-col"
			class:-translate-x-full={!isSidebarVisible}
			class:translate-x-0={isSidebarVisible}
		>
			<!-- Sidebar Header -->
			<div
				class="relative p-4 border-b border-gray-100 dark:border-zinc-800/50 shrink-0 bg-white/95 dark:bg-zinc-900/95 backdrop-blur z-10"
			>
				<div class="flex items-center justify-between">
					<h2 class="font-bold text-gray-900 dark:text-white flex items-center gap-2">
						<div class="w-1.5 h-4 bg-red-500 rounded-full"></div>
						{t('theater.news.otherNews') || 'Berita Lainnya'}
					</h2>
					<button
						onclick={toggleSidebar}
						class="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-zinc-300 rounded-lg hover:bg-gray-100 dark:hover:bg-zinc-800 cursor-pointer"
						title={t('theater.closeSidebar') || 'Close sidebar'}
					>
						<PanelLeftClose class="w-4 h-4" />
					</button>
				</div>
			</div>

			<div
				class="flex-1 overflow-y-auto custom-scrollbar p-3 pt-2 pb-28"
				style="overscroll-behavior: contain;"
			>
				{#if newsStore.isLoading && newsList.value.length === 0}
					<div class="space-y-3">
						{#each Array(5)}
							<div class="w-full h-16 rounded-xl bg-gray-100 dark:bg-zinc-800 animate-pulse"></div>
						{/each}
					</div>
				{:else}
					<div class="space-y-2">
						{#each newsList.value as recent}
							{@const isActive = recent.link === item?.link}
							<a
								href={`/theater/news/${recent.link}`}
								class="w-full cursor-pointer group flex flex-col gap-1.5 p-3 md:p-4 rounded-xl transition-all duration-200 border {isActive
									? 'bg-red-50 dark:bg-red-500/10 border-red-200 dark:border-red-500/30 shadow-sm'
									: 'border-transparent hover:bg-gray-50 dark:hover:bg-zinc-800/50 hover:border-gray-200 dark:hover:border-zinc-700/50'}"
								onclick={() => {
									if (innerWidth < 768) isSidebarVisible = false;
								}}
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
									class="text-sm font-bold {isActive
										? 'text-red-600 dark:text-red-400'
										: 'text-gray-800 dark:text-gray-200'} leading-snug group-hover:text-red-500 transition-colors line-clamp-2"
								>
									{recent.title}
								</h4>
							</a>
						{/each}
					</div>
				{/if}
			</div>
		</aside>

		<!-- Floating Toggle Sidebar Button -->
		{#if !isSidebarVisible}
			<div
				class="absolute top-3 left-0 z-30 transition-all duration-300"
				transition:fade={{ duration: 200 }}
			>
				<button
					onclick={toggleSidebar}
					class="flex items-center justify-center w-8 h-10 bg-white/90 dark:bg-zinc-900/90 backdrop-blur-md shadow-lg border-y border-r border-gray-200 dark:border-white/10 rounded-r-xl text-gray-400 hover:text-red-500 transition-all hover:w-10 active:scale-95 cursor-pointer"
					title={t('common.openSidebar') || 'Open sidebar'}
				>
					<PanelLeft class="w-4 h-4 ml-1" />
				</button>
			</div>
		{/if}

		<!-- Main Content Area -->
		<main
			bind:this={mainContentEl}
			class="flex-1 overflow-y-auto relative h-full custom-scrollbar bg-white dark:bg-zinc-900"
			style="overscroll-behavior: contain;"
		>
			<div class="pb-28 md:pb-12 max-w-none w-full mx-auto">
				{#if $navigating || !item}
					<div class="bg-white dark:bg-zinc-900 overflow-hidden animate-pulse">
						<div
							class="relative w-full min-h-[280px] sm:min-h-[350px] flex flex-col justify-end bg-gray-200 dark:bg-zinc-800"
						>
							<div
								class="relative z-20 px-6 sm:px-10 pt-[150px] sm:pt-[200px] pb-6 sm:pb-10 flex flex-col justify-end w-full"
							>
								<div class="pointer-events-auto w-full max-w-5xl mx-auto">
									<div class="flex flex-wrap gap-2 mb-3">
										<div class="h-6 w-20 bg-gray-300 dark:bg-zinc-700 rounded-lg"></div>
									</div>
									<div
										class="h-10 sm:h-12 w-3/4 bg-gray-300 dark:bg-zinc-700 rounded-xl mb-4"
									></div>
									<div class="flex flex-row gap-2 sm:gap-4">
										<div class="h-10 w-32 bg-gray-300 dark:bg-zinc-700 rounded-xl"></div>
									</div>
								</div>
							</div>
						</div>
						<div class="p-6 sm:p-8 lg:p-10 max-w-5xl mx-auto w-full">
							<div class="space-y-12">
								<div class="space-y-4 pt-4">
									<div class="h-4 bg-gray-200 dark:bg-zinc-800 rounded w-full"></div>
									<div class="h-4 bg-gray-200 dark:bg-zinc-800 rounded w-full"></div>
									<div class="h-4 bg-gray-200 dark:bg-zinc-800 rounded w-full"></div>
									<div class="h-4 bg-gray-200 dark:bg-zinc-800 rounded w-5/6"></div>
								</div>
							</div>
						</div>
					</div>
				{:else}
					<div class="bg-white dark:bg-zinc-900 overflow-hidden">
						{#snippet heroContent({ isDarkText = false }: { isDarkText?: boolean })}
							<div class="flex flex-wrap gap-2 mb-3">
								<span
									class="px-3 py-1.5 text-[11px] font-black rounded-lg uppercase tracking-widest flex items-center gap-1.5 shadow-sm {item.category.toLowerCase() ===
									'event'
										? 'bg-red-100 dark:bg-red-500/20 text-red-600 dark:text-red-400 border border-red-200 dark:border-red-500/30'
										: item.category.toLowerCase() === 'theater'
											? 'bg-cyan-100 dark:bg-cyan-500/20 text-cyan-600 dark:text-cyan-400 border border-cyan-200 dark:border-cyan-500/30'
											: 'bg-orange-100 dark:bg-orange-500/20 text-orange-600 dark:text-orange-400 border border-orange-200 dark:border-orange-500/30'}"
								>
									{item.category}
								</span>
							</div>
							<h1
								class="text-2xl sm:text-4xl md:text-5xl font-black leading-tight mb-4 {isDarkText
									? 'text-gray-900 dark:text-white'
									: 'text-white drop-shadow-md'}"
							>
								{item.title}
							</h1>
							<div
								class="flex flex-row flex-wrap gap-2 sm:gap-4 font-medium text-xs sm:text-sm md:text-base {isDarkText
									? 'text-gray-600 dark:text-gray-300'
									: 'text-white'}"
							>
								<div
									class="inline-flex items-center justify-center sm:justify-start gap-1.5 sm:gap-2 px-3 sm:px-4 py-2 rounded-xl border {isDarkText
										? 'bg-gray-50 dark:bg-zinc-800/80 border-gray-100 dark:border-zinc-700/50'
										: 'bg-black/40 backdrop-blur-md border-white/20 shadow-sm'} overflow-hidden"
								>
									<Calendar
										class="w-3.5 h-3.5 sm:w-4 sm:h-4 shrink-0 {isDarkText
											? 'text-red-500 dark:text-red-400'
											: 'text-red-400'}"
									/>
									<span class="whitespace-nowrap"
										>{formatDate(item.valid_date_from, {
											day: 'numeric',
											month: 'long',
											year: 'numeric'
										})}</span
									>
								</div>
							</div>
						{/snippet}

						<!-- Hero Section -->
						<div class="relative w-full flex flex-col">
							{#if item.background_image}
								<div
									class="relative w-full min-h-[280px] sm:min-h-[350px] flex flex-col justify-end"
								>
									<button
										onclick={() =>
											openLightbox(getExternalMediaUrl(item.background_image), item.title)}
										class="absolute inset-0 w-full h-full overflow-hidden bg-gray-100 dark:bg-zinc-800 group cursor-pointer outline-none focus-visible:ring-2 focus-visible:ring-red-500"
										aria-label="View full image"
									>
										<OptimizedImage
											src={getExternalMediaUrl(item.background_image)}
											alt={item.title}
											class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
										/>
										<div
											class="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors duration-300 z-10 hidden md:flex items-center justify-center pb-24 sm:pb-32"
										>
											<ZoomIn
												class="w-16 h-16 text-white opacity-0 group-hover:opacity-100 transition-opacity duration-300 drop-shadow-lg"
											/>
										</div>
									</button>

									<!-- Hero Content Overlay with seamless fade to background color -->
									<div
										class="relative z-20 px-6 sm:px-10 pt-[150px] sm:pt-[200px] pb-6 sm:pb-10 flex flex-col justify-end w-full bg-gradient-to-t from-white via-white/95 to-transparent dark:from-zinc-900 dark:via-zinc-900/95 pointer-events-none"
									>
										<div class="pointer-events-auto w-full max-w-5xl mx-auto">
											{@render heroContent({ isDarkText: true })}
										</div>
									</div>
								</div>
							{:else}
								<div
									class="relative w-full min-h-[280px] sm:min-h-[350px] flex flex-col justify-end"
								>
									<div
										class="absolute inset-0 bg-gradient-to-br from-red-500/10 to-rose-700/10 dark:from-red-500/5 dark:to-rose-700/5 overflow-hidden pointer-events-none"
									></div>
									<div
										class="relative z-10 px-6 sm:px-10 pt-[150px] sm:pt-[200px] pb-6 sm:pb-10 flex flex-col justify-end w-full bg-gradient-to-t from-white via-white/95 to-transparent dark:from-zinc-900 dark:via-zinc-900/95 pointer-events-none"
									>
										<div class="pointer-events-auto w-full max-w-5xl mx-auto">
											{@render heroContent({ isDarkText: true })}
										</div>
									</div>
								</div>
							{/if}
						</div>

						<!-- Content Layout inside unified card -->
						<div class="p-6 sm:p-8 lg:p-10 max-w-5xl mx-auto w-full">
							<!-- Main Content -->
							<div class="space-y-12">
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
										class="flex md:inline-flex items-center justify-center gap-2 w-full md:w-auto px-4 md:px-8 py-3 md:py-3 bg-red-500 hover:bg-red-600 text-white rounded-full font-bold shadow-md hover:shadow-lg transition-all uppercase tracking-wide md:tracking-normal text-[11px] md:text-base"
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
							</div>
						</div>
					</div>
				{/if}
			</div>
		</main>
	</div>
</div>

<ImageLightbox
	src={selectedImgSrc}
	alt={selectedImgAlt}
	isOpen={showLightbox}
	onClose={() => (showLightbox = false)}
/>
