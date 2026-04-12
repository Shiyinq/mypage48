<script lang="ts">
	import { preventDefault } from 'svelte/legacy';

	import { X, Music, LoaderCircle, CircleCheck, Image as ImageIcon } from 'lucide-svelte';
	import type { Setlist } from '$lib/apis/setlists';
	import { fade } from 'svelte/transition';
	import { useTranslation } from '$lib/i18n/useTranslation';

	interface Props {
		show?: boolean;
		setlist?: Partial<Setlist>;
		isCreating?: boolean;
		isSubmitting?: boolean;
		onsubmit?: (data: Partial<Setlist>) => void;
	}

	let {
		show = $bindable(false),
		setlist = {},
		isCreating = false,
		isSubmitting = false,
		onsubmit
	}: Props = $props();

	const { t } = useTranslation();

	let formData = $state({
		title: '',
		titleJapanese: '',
		description: '',
		type: 'setlist',
		imageUrl: '',
		active: true,
		songs: [] as string[]
	});

	// Safe Form Reset Pattern
	let prevShow = $state(false);
	$effect(() => {
		if (show !== prevShow) {
			if (show) {
				// Modal opened - reset form
				formData = {
					title: setlist.title || '',
					titleJapanese: setlist.titleJapanese || '',
					description: setlist.description || '',
					type: setlist.type || 'setlist',
					imageUrl: setlist.imageUrl || '',
					active: setlist.active ?? true,
					songs: setlist.songs || []
				};
			}
			prevShow = show;
		}
	});

	// Realtime Validation
	let isTitleValid = $derived(formData.title.length > 0);
	let isFormValid = $derived(isTitleValid);

	function handleSubmit() {
		if (!isFormValid) return;
		onsubmit?.(formData);
	}

	function handleClose() {
		show = false;
	}
</script>

{#if show}
	<div class="fixed inset-0 z-[9999] flex items-center justify-center p-4 sm:p-6">
		<!-- Backdrop -->
		<!-- svelte-ignore a11y_click_events_have_key_events -->
		<!-- svelte-ignore a11y_no_static_element_interactions -->
		<div
			class="absolute inset-0 bg-black/80 backdrop-blur-sm transition-opacity duration-300"
			onclick={handleClose}
			transition:fade
		></div>

		<!-- Modal Content -->
		<div
			class="bg-white/95 dark:bg-zinc-900/95 backdrop-blur-xl w-full max-w-2xl max-h-[90vh] rounded-3xl shadow-2xl overflow-y-auto custom-scrollbar relative z-50 pointer-events-auto"
			transition:fade={{ duration: 200 }}
		>
			<div class="p-6 md:p-8">
				<!-- Header -->
				<div class="flex items-center justify-between mb-8">
					<div class="flex items-center gap-3">
						<div
							class="p-3 rounded-2xl bg-purple-50 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 shadow-lg shadow-purple-100 dark:shadow-purple-900/20 border-2 border-white dark:border-zinc-700 transform -rotate-6"
						>
							<Music class="w-6 h-6" />
						</div>
						<div>
							<h2
								class="text-2xl font-bold text-gray-900 dark:text-white leading-none relative w-fit"
							>
								{isCreating
									? $t('admin.setlists.modal.addTitle')
									: $t('admin.setlists.modal.editTitle')}
								<span
									class="absolute -bottom-1 left-0 w-full h-2 bg-purple-200/60 dark:bg-purple-500/30 -z-10 transform -skew-x-12 rounded-sm"
								></span>
							</h2>
						</div>
					</div>

					<button
						onclick={handleClose}
						class="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-full transition-all cursor-pointer"
					>
						<X class="w-6 h-6" />
					</button>
				</div>

				<form onsubmit={preventDefault(handleSubmit)} class="space-y-6">
					<!-- Basic Info -->
					<div class="space-y-4">
						<div class="space-y-2">
							<label
								for="setlist-title"
								class="text-sm font-bold text-gray-700 dark:text-gray-300 ml-1"
								>{$t('admin.setlists.modal.title')}</label
							>
							<input
								id="setlist-title"
								type="text"
								bind:value={formData.title}
								placeholder="e.g. Ramune no Nomikata"
								class="w-full px-4 py-3 bg-gray-50 dark:bg-zinc-800/50 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none transition-all"
							/>
							{#if !isTitleValid && formData.title.length > 0}
								<p class="text-xs text-red-500 ml-1">
									{$t('admin.setlists.modal.titleRequired')}
								</p>
							{/if}
						</div>

						<div class="space-y-2">
							<label
								for="setlist-title-jp"
								class="text-sm font-bold text-gray-700 dark:text-gray-300 ml-1"
								>{$t('admin.setlists.modal.japaneseTitle')}</label
							>
							<input
								id="setlist-title-jp"
								type="text"
								bind:value={formData.titleJapanese}
								placeholder="e.g. ラムネの飲み方"
								class="w-full px-4 py-3 bg-gray-50 dark:bg-zinc-800/50 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none transition-all"
							/>
						</div>

						<div class="space-y-2">
							<span class="text-sm font-bold text-gray-700 dark:text-gray-300 ml-1"
								>{$t('admin.setlists.modal.type')}</span
							>
							<div class="flex gap-4">
								<label class="flex items-center gap-2 cursor-pointer">
									<input
										type="radio"
										bind:group={formData.type}
										value="setlist"
										class="w-5 h-5 text-purple-600 focus:ring-purple-500 border-gray-300"
									/>
									<span class="text-sm font-medium text-gray-800 dark:text-gray-200"
										>{$t('admin.setlists.table.theaterSetlist')}</span
									>
								</label>
								<label class="flex items-center gap-2 cursor-pointer">
									<input
										type="radio"
										bind:group={formData.type}
										value="event"
										class="w-5 h-5 text-purple-600 focus:ring-purple-500 border-gray-300"
									/>
									<span class="text-sm font-medium text-gray-800 dark:text-gray-200"
										>{$t('admin.setlists.table.specialEvent')}</span
									>
								</label>
							</div>
						</div>
					</div>

					<!-- Description -->
					<div class="space-y-2">
						<label
							for="setlist-desc"
							class="text-sm font-bold text-gray-700 dark:text-gray-300 ml-1"
							>{$t('admin.setlists.modal.description')}</label
						>
						<textarea
							id="setlist-desc"
							bind:value={formData.description}
							placeholder="Brief description of the setlist or event..."
							class="w-full px-4 py-3 bg-gray-50 dark:bg-zinc-800/50 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-2 focus:ring-purple-500 outline-none transition-all min-h-[100px] text-sm"
						></textarea>
					</div>

					<!-- Images -->
					<div class="space-y-2">
						<label
							for="setlist-image"
							class="text-sm font-bold text-gray-700 dark:text-gray-300 ml-1 flex items-center gap-2"
						>
							<ImageIcon class="w-4 h-4" />
							{$t('admin.setlists.modal.posterUrl')}
						</label>
						<input
							id="setlist-image"
							type="text"
							bind:value={formData.imageUrl}
							placeholder="https://..."
							class="w-full px-4 py-3 bg-gray-50 dark:bg-zinc-800/50 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none transition-all"
						/>
					</div>

					<!-- Active Status -->
					<div class="flex items-center gap-3 pt-2">
						<button
							type="button"
							aria-label="Toggle active status"
							class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 {formData.active
								? 'bg-green-500'
								: 'bg-gray-200 dark:bg-zinc-700'}"
							onclick={() => (formData.active = !formData.active)}
						>
							<span
								class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform {formData.active
									? 'translate-x-6'
									: 'translate-x-1'}"
							></span>
						</button>
						<span class="text-sm font-medium text-gray-700 dark:text-gray-300">
							{$t('admin.setlists.modal.setlistStatus')}: {formData.active
								? $t('admin.setlists.table.active')
								: $t('admin.setlists.table.inactive')}
						</span>
					</div>

					<!-- Actions -->
					<div class="pt-6 flex gap-3">
						<button
							type="button"
							onclick={handleClose}
							class="flex-1 px-4 py-3 rounded-xl font-bold text-gray-600 dark:text-gray-300 bg-gray-100 dark:bg-zinc-800 hover:bg-gray-200 dark:hover:bg-zinc-700 transition-colors cursor-pointer"
						>
							{$t('common.cancel')}
						</button>
						<button
							type="submit"
							disabled={!isFormValid || isSubmitting}
							class="flex-[2] px-4 py-3 rounded-xl font-bold text-white bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 shadow-lg shadow-purple-500/30 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-all cursor-pointer"
						>
							{#if isSubmitting}
								<LoaderCircle class="w-5 h-5 animate-spin" />
								{$t('admin.setlists.modal.saving')}
							{:else}
								<CircleCheck class="w-5 h-5" />
								{isCreating ? $t('admin.setlists.modal.create') : $t('admin.setlists.modal.save')}
							{/if}
						</button>
					</div>
				</form>
			</div>
		</div>
	</div>
{/if}
