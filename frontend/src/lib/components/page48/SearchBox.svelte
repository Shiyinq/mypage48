<script lang="ts">
	import { goto } from '$app/navigation';
	import { Search } from 'lucide-svelte';
	import { SEARCH_FIELD_CLASS, SEARCH_FIELD_ICON_CLASS } from '$lib/components/page48/searchField';
	import { isAuthenticated } from '$lib/stores/authStatus.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	interface Props {
		class?: string;
	}

	let { class: className = '' }: Props = $props();

	const { t } = useTranslation();

	let term = $state('');
	/** The suggestion list under the input; open as soon as something is typed. */
	let open = $state(false);

	let trimmed = $derived(term.trim());

	/** Clicking the suggestion, or pressing Enter, is what opens the results. */
	function run(event?: Event) {
		event?.preventDefault();
		if (!trimmed) return;
		open = false;
		void goto(`/page48/search?query=${encodeURIComponent(trimmed)}&tab=posts`);
	}
</script>

{#if isAuthenticated.value}
	<form onsubmit={run} class={`relative ${className}`} role="search">
		<Search size={16} class={SEARCH_FIELD_ICON_CLASS} />
		<input
			bind:value={term}
			type="text"
			enterkeyhint="search"
			placeholder={t('page48.search.placeholder')}
			aria-label={t('page48.search.placeholder')}
			class={SEARCH_FIELD_CLASS}
			oninput={() => (open = trimmed.length > 0)}
			onfocus={() => (open = trimmed.length > 0)}
			onblur={() => (open = false)}
			onkeydown={(event) => {
				if (event.key === 'Escape') open = false;
			}}
		/>

		{#if open && trimmed}
			<!-- The suggestion swallows mousedown so the input keeps focus until the click lands. -->
			<div
				class="absolute left-0 right-0 top-full z-[60] mt-1 overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-lg dark:border-zinc-800 dark:bg-zinc-900"
			>
				<button
					type="button"
					onmousedown={(event) => event.preventDefault()}
					onclick={run}
					class="flex w-full items-center gap-2 px-3 py-2.5 text-left text-[13px] font-medium text-gray-700 transition-colors hover:bg-gray-50 dark:text-gray-200 dark:hover:bg-white/5"
				>
					<Search size={15} class="shrink-0 text-gray-400" />
					<span class="min-w-0 flex-1 truncate">
						{t('page48.search.forTerm', { term: trimmed })}
					</span>
					<!-- Tells the reader that Enter does the same thing as this click. -->
					<kbd
						class="shrink-0 rounded border border-gray-200 px-1.5 py-0.5 text-[10px] font-medium text-gray-400 dark:border-zinc-700 dark:text-gray-500"
					>
						{t('page48.search.enterHint')}
					</kbd>
				</button>
			</div>
		{/if}
	</form>
{/if}
