<script lang="ts">
    import type { PageData } from './$types';
    import { useTranslation } from '$lib/i18n/useTranslation';
    import SEO from '$lib/components/SEO.svelte';
    import { Calendar, ChevronRight, ExternalLink } from 'lucide-svelte';
    import { formatDate } from '$lib/i18n';
    import { getExternalMediaUrl } from '$lib/utils/media';
    
    export let data: PageData;
    
    $: item = data.item;
    $: recentNews = data.recentNews.filter(n => n.link !== item.link).slice(0, 10);
    
    const { t, locale } = useTranslation();
</script>

<SEO
    title={item.title}
    path={`/theater/news/${item.link}`}
    description={item.short_description || item.title}
    image={item.background_image ? getExternalMediaUrl(item.background_image) : undefined}
/>

<div class="space-y-6 animate-fade-in pb-12">
    <!-- Breadcrumbs & Header -->
    <div class="mb-8">
        <h1 class="text-3xl md:text-4xl font-extrabold text-red-500 mb-4 leading-tight">
            {item.title}
        </h1>
        <div class="flex flex-wrap items-center gap-2 text-sm text-gray-500 dark:text-gray-400 font-medium">
            <a href="/theater" class="hover:text-red-500 transition-colors">Home</a>
            <span class="w-1 h-1 rounded-full bg-gray-300 dark:bg-zinc-600"></span>
            <a href="/theater/news" class="hover:text-red-500 transition-colors">News</a>
            <span class="w-1 h-1 rounded-full bg-gray-300 dark:bg-zinc-600"></span>
            <span class="text-gray-900 dark:text-gray-200 line-clamp-1 break-all">{item.title}</span>
        </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
        <!-- Main Content (Left) -->
        <main class="lg:col-span-2 space-y-6 bg-white dark:bg-zinc-900 rounded-3xl p-4 md:p-8 shadow-sm border border-gray-100 dark:border-white/5">
            {#if item.background_image}
                <div class="w-full rounded-2xl overflow-hidden bg-gray-100 dark:bg-zinc-800 shadow-inner">
                    <img 
                        src={getExternalMediaUrl(item.background_image)} 
                        alt={item.title}
                        class="w-full h-auto object-cover max-h-[500px]"
                    />
                </div>
            {/if}

            <div class="flex items-center gap-3 py-2 border-b border-gray-100 dark:border-zinc-800">
                <span class="inline-flex items-center px-2.5 py-1 rounded-md text-[10px] md:text-xs font-bold uppercase {item.category.toLowerCase() === 'event' ? 'bg-red-100 dark:bg-red-500/20 text-red-600 dark:text-red-400' : item.category.toLowerCase() === 'theater' ? 'bg-cyan-100 dark:bg-cyan-500/20 text-cyan-600 dark:text-cyan-400' : 'bg-orange-100 dark:bg-orange-500/20 text-orange-600 dark:text-orange-400'}">
                    {item.category}
                </span>
                <span class="flex items-center gap-1.5 text-xs md:text-sm font-semibold text-gray-500 dark:text-gray-400">
                    <Calendar class="w-4 h-4" />
                    {$formatDate(item.date, { day: 'numeric', month: 'long', year: 'numeric' })}
                </span>
            </div>

            <!-- HTML Content -->
            <div class="prose prose-red dark:prose-invert max-w-none prose-img:rounded-xl prose-a:text-red-500 hover:prose-a:text-red-600 space-y-4 text-gray-800 dark:text-gray-300 leading-relaxed text-sm md:text-base">
                {@html item.content_body}
            </div>

            <div class="pt-8 mt-8 border-t border-gray-100 dark:border-zinc-800 flex justify-center">
                <a 
                    href={`https://jkt48.com/news/${item.link}?lang=${$locale === 'id' ? 'id' : 'jp'}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    class="inline-flex items-center gap-2 px-6 py-3 bg-red-500 hover:bg-red-600 text-white rounded-full font-bold shadow-md hover:shadow-lg transition-all"
                >
                    {$t('theater.news.readOriginal')} <ExternalLink class="w-4 h-4" />
                </a>
            </div>
        </main>

        <!-- Sidebar (Right) -->
        <aside class="lg:col-span-1 space-y-6">
            <div class="bg-white dark:bg-zinc-900 rounded-3xl p-6 shadow-sm border border-gray-100 dark:border-white/5 sticky top-24">
                <div class="flex items-center justify-between mb-6 pb-4 border-b border-gray-100 dark:border-zinc-800">
                    <h3 class="text-lg font-bold text-gray-900 dark:text-white">{$t('theater.news.otherNews')}</h3>
                    <a href="/theater/news" class="text-xs font-semibold text-red-500 hover:text-red-600 flex items-center gap-0.5">
                        {$t('theater.news.seeAll')} <ChevronRight class="w-3 h-3" />
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
                                <span class="inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-bold uppercase {recent.category.toLowerCase() === 'event' ? 'bg-red-100 dark:bg-red-500/20 text-red-600 dark:text-red-400' : recent.category.toLowerCase() === 'theater' ? 'bg-cyan-100 dark:bg-cyan-500/20 text-cyan-600 dark:text-cyan-400' : 'bg-orange-100 dark:bg-orange-500/20 text-orange-600 dark:text-orange-400'}">
                                    {recent.category}
                                </span>
                                <span class="text-gray-300 dark:text-zinc-600">|</span>
                                <span class="text-[11px] font-medium text-gray-500 dark:text-gray-400">
                                    {$formatDate(recent.date, { day: 'numeric', month: 'short', year: 'numeric' })}
                                </span>
                            </div>
                            <h4 class="text-sm font-bold text-gray-800 dark:text-gray-200 leading-snug group-hover:text-red-500 transition-colors line-clamp-2">
                                {recent.title}
                            </h4>
                        </a>
                    {/each}
                </div>
            </div>
        </aside>
    </div>
</div>
