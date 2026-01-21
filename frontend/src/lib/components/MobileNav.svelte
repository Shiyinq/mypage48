<script lang="ts">
	import { page } from '$app/stores';
	import { LayoutDashboard, AudioLines, Plus, Image as ImageIcon, History } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	const { t } = useTranslation();
</script>

<nav
	class="md:hidden fixed bottom-0 left-0 right-0 bg-white/95 dark:bg-zinc-950/95 backdrop-blur-xl border-t border-gray-200 dark:border-zinc-800 z-40 pb-safe shadow-[0_-4px_20px_rgba(0,0,0,0.05)] dark:shadow-none"
>
	<div class="grid grid-cols-5 h-16 items-center max-w-md mx-auto px-2">
		<a
			href="/"
			class="flex flex-col items-center justify-center gap-1 text-gray-400 hover:text-red-600 dark:hover:text-red-400 group"
		>
			<LayoutDashboard
				class={`w-6 h-6 transition-all ${$page.url.pathname === '/' ? 'text-red-600 dark:text-red-400 scale-110' : ''}`}
			/>
			<span
				class={`text-[10px] font-medium transition-all ${$page.url.pathname === '/' ? 'text-red-600 dark:text-red-400' : ''}`}
				>{$t('nav.home')}</span
			>
		</a>

		<a
			href="/theater/events"
			class="flex flex-col items-center justify-center gap-1 text-gray-400 hover:text-purple-600 dark:hover:text-purple-400 group"
		>
			<AudioLines
				class={`w-6 h-6 transition-all ${$page.url.pathname.startsWith('/theater') ? 'text-purple-600 dark:text-purple-400 scale-110' : ''}`}
			/>
			<span
				class={`text-[10px] font-medium transition-all ${$page.url.pathname.startsWith('/theater') ? 'text-purple-600 dark:text-purple-400' : ''}`}
				>{$t('nav.theater')}</span
			>
		</a>

		<!-- Center Floating Action Button (FAB) -->
		<div class="relative -top-5 flex justify-center w-full">
			<a
				href="/upload"
				class="flex justify-center w-14 h-14 rounded-full idol-gradient text-white shadow-lg shadow-red-300 dark:shadow-red-900/50 border-4 border-gray-50 dark:border-gray-800 items-center transform transition-transform active:scale-90 hover:scale-105 hover:shadow-red-400 dark:hover:shadow-red-800/50"
			>
				<Plus class="w-8 h-8" />
			</a>
		</div>

		<a
			href="/memories"
			class="flex flex-col items-center justify-center gap-1 text-gray-400 hover:text-pink-600 dark:hover:text-pink-400 group"
		>
			<ImageIcon
				class={`w-6 h-6 transition-all ${$page.url.pathname === '/memories' ? 'text-pink-600 dark:text-pink-400 scale-110' : ''}`}
			/>
			<span
				class={`text-[10px] font-medium transition-all ${$page.url.pathname === '/memories' ? 'text-pink-600 dark:text-pink-400' : ''}`}
				>{$t('nav.memories')}</span
			>
		</a>

		<a
			href="/history"
			class="flex flex-col items-center justify-center gap-1 text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 group"
		>
			<History
				class={`w-6 h-6 transition-all ${$page.url.pathname === '/history' ? 'text-blue-600 dark:text-blue-400 scale-110' : ''}`}
			/>
			<span
				class={`text-[10px] font-medium transition-all ${$page.url.pathname === '/history' ? 'text-blue-600 dark:text-blue-400' : ''}`}
				>{$t('nav.history')}</span
			>
		</a>
	</div>
</nav>
