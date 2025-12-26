<script lang="ts">
	import { page } from '$app/stores';
	import { LayoutDashboard, Mic2, Plus, Image as ImageIcon, History } from 'lucide-svelte';
</script>

<nav
	class="md:hidden fixed bottom-0 left-0 right-0 bg-white/90 backdrop-blur-lg border-t border-gray-200 z-40 pb-safe shadow-[0_-4px_20px_rgba(0,0,0,0.05)]"
>
	<div class="grid grid-cols-5 h-16 items-center max-w-md mx-auto px-2">
		<a
			href="/"
			class="flex flex-col items-center justify-center gap-1 text-gray-400 hover:text-red-600 group"
		>
			<LayoutDashboard
				class={`w-6 h-6 transition-all ${$page.url.pathname === '/' ? 'text-red-600 scale-110' : ''}`}
			/>
			<span
				class={`text-[10px] font-medium transition-all ${$page.url.pathname === '/' ? 'text-red-600' : ''}`}
				>Home</span
			>
		</a>

		<a
			href="/shows"
			class="flex flex-col items-center justify-center gap-1 text-gray-400 hover:text-purple-600 group"
		>
			<Mic2
				class={`w-6 h-6 transition-all ${$page.url.pathname === '/shows' ? 'text-purple-600 scale-110' : ''}`}
			/>
			<span
				class={`text-[10px] font-medium transition-all ${$page.url.pathname === '/shows' ? 'text-purple-600' : ''}`}
				>Setlists</span
			>
		</a>

		<!-- Center Floating Action Button (FAB) -->
		<div class="relative -top-5 flex justify-center w-full">
			<a
				href="/upload"
				class="flex justify-center w-14 h-14 rounded-full idol-gradient text-white shadow-lg shadow-red-300 border-4 border-gray-50 items-center transform transition-transform active:scale-90 hover:scale-105 hover:shadow-red-400"
			>
				<Plus class="w-8 h-8" />
			</a>
		</div>

		<a
			href="/memories"
			class="flex flex-col items-center justify-center gap-1 text-gray-400 hover:text-pink-600 group"
		>
			<ImageIcon
				class={`w-6 h-6 transition-all ${$page.url.pathname === '/memories' ? 'text-pink-600 scale-110' : ''}`}
			/>
			<span
				class={`text-[10px] font-medium transition-all ${$page.url.pathname === '/memories' ? 'text-pink-600' : ''}`}
				>Memories</span
			>
		</a>

		<a
			href="/history"
			class="flex flex-col items-center justify-center gap-1 text-gray-400 hover:text-blue-600 group"
		>
			<History
				class={`w-6 h-6 transition-all ${$page.url.pathname === '/history' ? 'text-blue-600 scale-110' : ''}`}
			/>
			<span
				class={`text-[10px] font-medium transition-all ${$page.url.pathname === '/history' ? 'text-blue-600' : ''}`}
				>History</span
			>
		</a>
	</div>
</nav>
