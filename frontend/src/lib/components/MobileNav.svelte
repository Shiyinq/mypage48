<script lang="ts">
	import { page } from '$app/stores';
	import { LayoutDashboard, AudioLines, Plus, Image as ImageIcon, History, BookOpen, Trophy } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	const { t } = useTranslation();
</script>

<nav
	class="md:hidden fixed bottom-0 left-0 right-0 bg-white/95 dark:bg-zinc-950/95 backdrop-blur-xl border-t border-gray-200 dark:border-zinc-800 z-40 pb-safe shadow-[0_-4px_20px_rgba(0,0,0,0.05)] dark:shadow-none"
>
	<div class="flex h-16 items-center justify-between max-w-md mx-auto px-2">
		<a
			href="/"
			class="flex flex-col items-center justify-center gap-1 text-gray-400 hover:text-red-600 dark:hover:text-red-400 group flex-1 min-w-0"
		>
			<LayoutDashboard
				class={`w-5 h-5 transition-all ${$page.url.pathname === '/' ? 'text-red-600 dark:text-red-400 scale-110' : ''}`}
			/>
			<span
				class={`text-[9px] font-medium transition-all truncate w-full text-center ${$page.url.pathname === '/' ? 'text-red-600 dark:text-red-400' : ''}`}
				>{$t('nav.home')}</span
			>
		</a>

		<a
			href="/theater/events"
			class="flex flex-col items-center justify-center gap-1 text-gray-400 hover:text-purple-600 dark:hover:text-purple-400 group flex-1 min-w-0"
		>
			<AudioLines
				class={`w-5 h-5 transition-all ${$page.url.pathname.startsWith('/theater') ? 'text-purple-600 dark:text-purple-400 scale-110' : ''}`}
			/>
			<span
				class={`text-[9px] font-medium transition-all truncate w-full text-center ${$page.url.pathname.startsWith('/theater') ? 'text-purple-600 dark:text-purple-400' : ''}`}
				>{$t('nav.theater')}</span
			>
		</a>

		<a
			href="/achievements"
			class="flex flex-col items-center justify-center gap-1 text-gray-400 hover:text-amber-600 dark:hover:text-amber-400 group flex-1 min-w-0"
		>
			<Trophy
				class={`w-5 h-5 transition-all ${$page.url.pathname === '/achievements' ? 'text-amber-600 dark:text-amber-400 scale-110' : ''}`}
			/>
			<span
				class={`text-[9px] font-medium transition-all truncate w-full text-center ${$page.url.pathname === '/achievements' ? 'text-amber-600 dark:text-amber-400' : ''}`}
				>{$t('nav.achievements')}</span
			>
		</a>

		<!-- Floating Action Button (FAB) -->
		<div class="relative -top-5 flex justify-center px-1">
			<a
				href="/upload"
				class="flex justify-center w-12 h-12 rounded-full idol-gradient text-white shadow-lg shadow-red-300 dark:shadow-red-900/50 border-4 border-gray-50 dark:border-zinc-950 items-center transform transition-transform active:scale-90 hover:scale-105"
			>
				<Plus class="w-7 h-7" />
			</a>
		</div>

		<a
			href="/journal"
			class="flex flex-col items-center justify-center gap-1 text-gray-400 hover:text-green-600 dark:hover:text-green-400 group flex-1 min-w-0"
		>
			<BookOpen
				class={`w-5 h-5 transition-all ${$page.url.pathname === '/journal' ? 'text-green-600 dark:text-green-400 scale-110' : ''}`}
			/>
			<span
				class={`text-[9px] font-medium transition-all truncate w-full text-center ${$page.url.pathname === '/journal' ? 'text-green-600 dark:text-green-400' : ''}`}
				>{$t('nav.journal')}</span
			>
		</a>

		<a
			href="/memories"
			class="flex flex-col items-center justify-center gap-1 text-gray-400 hover:text-pink-600 dark:hover:text-pink-400 group flex-1 min-w-0"
		>
			<ImageIcon
				class={`w-5 h-5 transition-all ${$page.url.pathname === '/memories' ? 'text-pink-600 dark:text-pink-400 scale-110' : ''}`}
			/>
			<span
				class={`text-[9px] font-medium transition-all truncate w-full text-center ${$page.url.pathname === '/memories' ? 'text-pink-600 dark:text-pink-400' : ''}`}
				>{$t('nav.memories')}</span
			>
		</a>

		<a
			href="/history"
			class="flex flex-col items-center justify-center gap-1 text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 group flex-1 min-w-0"
		>
			<History
				class={`w-5 h-5 transition-all ${$page.url.pathname === '/history' ? 'text-blue-600 dark:text-blue-400 scale-110' : ''}`}
			/>
			<span
				class={`text-[9px] font-medium transition-all truncate w-full text-center ${$page.url.pathname === '/history' ? 'text-blue-600 dark:text-blue-400' : ''}`}
				>{$t('nav.history')}</span
			>
		</a>
	</div>
</nav>
