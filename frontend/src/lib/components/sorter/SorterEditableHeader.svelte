<script lang="ts">
	import { Pencil, Check, X, Calendar } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	const { t } = useTranslation();

	interface Props {
		title: string;
		description: string;
		tempTitle?: string;
		tempDescription?: string;
		isEditingTitle?: boolean;
		isEditingDescription?: boolean;
		isSaving?: boolean;
		date?: string;
		filters?: string[];
		titleLimit?: number;
		descriptionLimit?: number;
		placeholderDescription?: string;
		onstartEditTitle?: () => void;
		oncancelEditTitle?: () => void;
		onsaveTitle?: () => void;
		onstartEditDescription?: () => void;
		oncancelEditDescription?: () => void;
		onsaveDescription?: () => void;
		onTitleChange?: (v: string) => void;
		onDescriptionChange?: (v: string) => void;
		hideEdit?: boolean;
	}

	let {
		title,
		description,
		tempTitle = '',
		tempDescription = '',
		isEditingTitle = false,
		isEditingDescription = false,
		isSaving = false,
		date,
		filters = [],
		titleLimit = 50,
		descriptionLimit = 100,
		placeholderDescription,
		onstartEditTitle,
		oncancelEditTitle,
		onsaveTitle,
		onstartEditDescription,
		oncancelEditDescription,
		onsaveDescription,
		onTitleChange,
		onDescriptionChange,
		hideEdit = false
	}: Props = $props();

	function autofocus(node: HTMLInputElement | HTMLTextAreaElement) {
		node.focus();
		if (node instanceof HTMLInputElement) node.select();
	}
</script>

<div class="space-y-4">
	<!-- Date if available -->
	{#if date}
		<div
			class="flex items-center justify-start gap-1.5 text-[10px] font-bold text-zinc-400 dark:text-zinc-500 uppercase tracking-wider mb-2"
		>
			<Calendar size={12} class="text-rose-500" />
			<span>{date}</span>
		</div>
	{/if}

	<!-- TITLE -->
	<div class="flex items-center gap-2">
		{#if isEditingTitle}
			<div
				class="flex-1 max-w-2xl bg-zinc-50 dark:bg-zinc-800/50 rounded-xl sm:rounded-2xl p-2 sm:p-3 border border-zinc-200 dark:border-zinc-700/50 flex flex-col sm:flex-row items-stretch sm:items-center gap-2 sm:gap-3 transition-colors shadow-sm"
			>
				<div
					class="flex-1 relative flex items-center bg-white dark:bg-zinc-900 rounded-lg sm:rounded-xl border border-zinc-200 dark:border-zinc-700 focus-within:border-rose-500 dark:focus-within:border-rose-500 focus-within:ring-2 focus-within:ring-rose-500/20 transition-all overflow-hidden group"
				>
					<input
						type="text"
						value={tempTitle}
						oninput={(e) => onTitleChange?.(e.currentTarget.value)}
						use:autofocus
						placeholder="Judul"
						maxlength={titleLimit}
						class="w-full bg-transparent px-3 sm:px-4 py-2 sm:py-2.5 text-sm sm:text-base font-black text-themed outline-none placeholder:text-zinc-400 dark:placeholder:text-zinc-600"
						onkeydown={(e) => {
							if (e.key === 'Enter') onsaveTitle?.();
							if (e.key === 'Escape') oncancelEditTitle?.();
						}}
						disabled={isSaving}
					/>
					<div
						class="absolute right-3 top-1/2 -translate-y-1/2 flex items-center pointer-events-none select-none"
					>
						<span
							class="text-[10px] sm:text-xs font-bold text-zinc-400 dark:text-zinc-500 group-focus-within:text-rose-500 transition-colors"
						>
							{tempTitle.length}/{titleLimit}
						</span>
					</div>
				</div>
				<div class="flex items-center justify-end sm:justify-start gap-1.5 shrink-0">
					<button
						onclick={onsaveTitle}
						disabled={isSaving}
						class="flex items-center justify-center w-8 h-8 sm:w-10 sm:h-10 rounded-lg sm:rounded-xl bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 disabled:hover:bg-emerald-500 text-white transition-all shadow-md shadow-emerald-500/20 cursor-pointer"
						title={t('common.save') || 'Save'}
					>
						{#if isSaving}
							<div
								class="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"
							></div>
						{:else}
							<Check size={16} />
						{/if}
					</button>
					<button
						onclick={oncancelEditTitle}
						disabled={isSaving}
						class="flex items-center justify-center w-8 h-8 sm:w-10 sm:h-10 rounded-lg sm:rounded-xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 text-zinc-500 hover:text-red-500 hover:bg-red-50 hover:border-red-200 dark:hover:bg-red-500/10 dark:hover:border-red-500/30 transition-all cursor-pointer"
						title={t('common.cancel') || 'Cancel'}
					>
						<X size={16} />
					</button>
				</div>
			</div>
		{:else}
			<div class="flex items-center gap-2 w-full min-w-0">
				<h1
					class="text-2xl sm:text-4xl md:text-5xl font-black tracking-tighter uppercase leading-tight break-words min-w-0 text-themed"
				>
					{title}
				</h1>
				{#if !hideEdit}
					<button
						onclick={onstartEditTitle}
						class="p-1.5 rounded-full text-zinc-400 hover:text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-500/10 transition-all cursor-pointer shrink-0"
						title={t('common.edit') || 'Edit'}
					>
						<Pencil size={18} />
					</button>
				{/if}
			</div>
		{/if}
	</div>

	<!-- DESCRIPTION -->
	<div class="flex items-start gap-2">
		{#if isEditingDescription}
			<div
				class="w-full max-w-2xl bg-zinc-50 dark:bg-zinc-800/50 rounded-xl p-2 sm:p-3 border border-zinc-200 dark:border-zinc-700/50 flex flex-col sm:flex-row items-end sm:items-start gap-2 sm:gap-3 transition-colors shadow-sm"
			>
				<div
					class="flex-1 w-full relative flex items-start bg-white dark:bg-zinc-900 rounded-lg sm:rounded-xl border border-zinc-200 dark:border-zinc-700 focus-within:border-rose-500 dark:focus-within:border-rose-500 focus-within:ring-2 focus-within:ring-rose-500/20 transition-all overflow-hidden group"
				>
					<textarea
						value={tempDescription}
						oninput={(e) => onDescriptionChange?.(e.currentTarget.value)}
						use:autofocus
						placeholder={placeholderDescription ||
							t('theater.sorter.descriptionPlaceholder') ||
							'Deskripsi (opsional)'}
						maxlength={descriptionLimit}
						rows="2"
						class="w-full bg-transparent px-3 sm:px-4 py-2 sm:py-2.5 text-xs sm:text-sm font-semibold text-themed outline-none resize-none placeholder:text-zinc-400 dark:placeholder:text-zinc-600"
						onkeydown={(e) => {
							if (e.key === 'Escape') oncancelEditDescription?.();
						}}
						disabled={isSaving}
					></textarea>
					<div
						class="absolute right-2 bottom-1.5 flex items-center pointer-events-none select-none bg-white/80 dark:bg-zinc-900/80 px-1 rounded backdrop-blur-sm"
					>
						<span
							class="text-[9px] sm:text-[10px] font-bold text-zinc-400 dark:text-zinc-500 group-focus-within:text-rose-500 transition-colors"
						>
							{tempDescription.length}/{descriptionLimit}
						</span>
					</div>
				</div>
				<div class="flex sm:flex-col items-center justify-end gap-1.5 shrink-0 w-full sm:w-auto">
					<button
						onclick={onsaveDescription}
						disabled={isSaving}
						class="flex items-center justify-center w-8 h-8 rounded-lg bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 disabled:hover:bg-emerald-500 text-white transition-all shadow-md shadow-emerald-500/20 cursor-pointer"
						title={t('common.save') || 'Save'}
					>
						{#if isSaving}
							<div
								class="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"
							></div>
						{:else}
							<Check size={14} />
						{/if}
					</button>
					<button
						onclick={oncancelEditDescription}
						disabled={isSaving}
						class="flex items-center justify-center w-8 h-8 rounded-lg bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 text-zinc-500 hover:text-red-500 hover:bg-red-50 hover:border-red-200 dark:hover:bg-red-500/10 dark:hover:border-red-500/30 transition-all cursor-pointer"
						title={t('common.cancel') || 'Cancel'}
					>
						<X size={14} />
					</button>
				</div>
			</div>
		{:else}
			<div class="flex items-start gap-1.5 max-w-2xl min-w-0">
				<p
					class="text-xs sm:text-sm font-semibold text-themed-secondary break-words min-w-0 leading-relaxed max-w-[90%]"
				>
					{description ||
						placeholderDescription ||
						t('theater.sorter.descriptionPlaceholder') ||
						'Deskripsi (opsional)'}
				</p>
				{#if !hideEdit}
					<button
						onclick={onstartEditDescription}
						class="p-1 rounded-full text-zinc-400 hover:text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-500/10 transition-all cursor-pointer shrink-0 mt-0.5"
						title={t('common.edit') || 'Edit'}
					>
						<Pencil size={14} />
					</button>
				{/if}
			</div>
		{/if}
	</div>

	<!-- FILTERS (Generations) -->
	{#if filters && filters.length > 0}
		<div class="flex flex-wrap gap-1.5 pt-2">
			{#each filters as gen}
				<span
					class="px-2.5 py-0.5 rounded-full text-[9px] font-black tracking-wider uppercase border transition-all hover:scale-105 select-none bg-rose-50/50 dark:bg-rose-950/20 border-rose-100 dark:border-rose-900/30 text-rose-500 dark:text-rose-400"
				>
					{t('theater.sorter.genLabel', { gen })}
				</span>
			{/each}
		</div>
	{/if}
</div>
