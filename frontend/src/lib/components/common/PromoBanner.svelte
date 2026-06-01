<script lang="ts">
	import { Info, X } from 'lucide-svelte';
	import { onMount, type Snippet } from 'svelte';

	interface Props {
		title: string;
		desc: string;
		actionText?: string;
		href?: string;
		class?: string;
		// eslint-disable-next-line @typescript-eslint/no-explicit-any
		icon?: any;
		storageKey?: string;
		onClose?: () => void;
		actions?: Snippet;
	}

	let {
		title,
		desc,
		actionText,
		href = '/register',
		class: className = '',
		icon: IconComponent = Info,
		storageKey,
		onClose,
		actions
	}: Props = $props();

	let isVisible = $state(true);

	onMount(() => {
		if (storageKey) {
			isVisible = localStorage.getItem(storageKey) !== 'true';
		}
	});

	function handleClose() {
		isVisible = false;
		if (storageKey) {
			localStorage.setItem(storageKey, 'true');
		}
		if (onClose) {
			onClose();
		}
	}
</script>

{#if isVisible}
	<div
		class="relative overflow-hidden bg-gradient-to-r from-red-500/10 via-rose-500/5 to-white dark:to-zinc-950 backdrop-blur-md border border-red-500/15 dark:border-red-500/10 rounded-3xl p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-lg shadow-slate-100/50 dark:shadow-none text-left {className}"
	>
		<!-- Blur decoration -->
		<div
			class="absolute -right-12 -bottom-12 w-32 h-32 bg-red-500/15 rounded-full blur-2xl pointer-events-none"
		></div>
		<div
			class="absolute -left-12 -top-12 w-32 h-32 bg-rose-500/10 rounded-full blur-2xl pointer-events-none"
		></div>

		<button
			class="absolute top-3 right-3 p-1 text-slate-400 hover:text-slate-600 dark:text-zinc-500 dark:hover:text-zinc-300 rounded-full hover:bg-slate-100 dark:hover:bg-zinc-900 transition-all cursor-pointer z-20"
			onclick={handleClose}
			aria-label="Close banner"
		>
			<X size={15} />
		</button>

		<div
			class="flex flex-col sm:flex-row items-center sm:items-start gap-3 text-center sm:text-left z-10 flex-1 w-full"
		>
			<div
				class="w-10 h-10 rounded-xl bg-red-600/10 dark:bg-red-500/10 flex items-center justify-center text-red-600 dark:text-red-400 flex-shrink-0 animate-pulse"
			>
				<IconComponent size={18} />
			</div>
			<div class="flex-1 min-w-0 pr-4 sm:pr-0">
				<h3
					class="text-sm font-black tracking-tight text-slate-900 dark:text-white mb-0.5 uppercase tracking-wider"
				>
					{title}
				</h3>
				<p
					class="text-xs font-semibold text-slate-500 dark:text-slate-400 leading-relaxed max-w-2xl"
				>
					{desc}
				</p>
			</div>
		</div>

		{#if actions}
			{@render actions()}
		{:else if actionText}
			<div class="w-full sm:w-auto z-10 shrink-0 mt-1 sm:mt-0 flex sm:items-center">
				<a
					{href}
					class="w-full sm:w-auto py-2 px-5 bg-red-600 hover:bg-red-700 active:scale-95 text-white font-black uppercase tracking-widest text-[9px] rounded-2xl transition-all shadow-md shadow-red-500/20 cursor-pointer text-center"
				>
					{actionText}
				</a>
			</div>
		{/if}
	</div>
{/if}
