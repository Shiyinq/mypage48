<script lang="ts">
	import { Ticket } from 'lucide-svelte';
</script>

<div class="min-h-screen flex flex-col items-center justify-center animate-fade-in">
	<div
		class="w-20 h-20 rounded-full idol-gradient flex items-center justify-center text-white shadow-xl mb-6 ring-4 ring-white/50 dark:ring-white/10 animate-pulse"
	>
		<Ticket class="w-10 h-10" />
	</div>
	<h1 class="text-2xl font-black text-gray-900 dark:text-white tracking-tight">
		MyPage<span class="text-red-600">48</span>
	</h1>
</div>
