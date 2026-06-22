<script lang="ts">
	import { X, LoaderCircle, CircleCheck, MessageSquare, ChevronDown } from 'lucide-svelte';
	import type { FeedbackMessage } from '$lib/types/feedback';
	import { fade } from 'svelte/transition';
	import { useTranslation } from '$lib/i18n/useTranslation';

	interface Props {
		show?: boolean;
		feedback?: FeedbackMessage | null;
		isSubmitting?: boolean;
		onsubmit?: (data: { status: string; admin_notes: string }) => Promise<void> | void;
		onclose?: () => void;
	}

	let {
		show = $bindable(false),
		feedback = null,
		isSubmitting = false,
		onsubmit,
		onclose
	}: Props = $props();

	const { t } = useTranslation();

	let formData = $state({
		status: 'pending',
		admin_notes: ''
	});

	// Reset form when modal opens
	let prevShow = $state(false);
	$effect(() => {
		if (show !== prevShow) {
			if (show && feedback) {
				formData = {
					status: feedback.status || 'pending',
					admin_notes: feedback.admin_notes || ''
				};
			}
			prevShow = show;
		}
	});

	async function handleSubmit() {
		if (isSubmitting) return;
		await onsubmit?.({
			status: formData.status,
			admin_notes: formData.admin_notes
		});
	}

	function handleClose() {
		show = false;
		onclose?.();
	}
</script>

{#if show && feedback}
	<div class="fixed inset-0 z-[9999] flex items-center justify-center p-3 sm:p-6">
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
			class="bg-white/95 dark:bg-zinc-900/95 backdrop-blur-xl w-full max-w-lg max-h-[90vh] rounded-3xl shadow-2xl overflow-y-auto custom-scrollbar relative z-50 pointer-events-auto flex flex-col"
			transition:fade={{ duration: 200 }}
		>
			<div class="p-5 sm:p-6 md:p-8">
				<!-- Header -->
				<div class="flex items-center justify-between mb-6 sm:mb-8">
					<div class="flex items-center gap-3">
						<div
							class="p-2 sm:p-3 rounded-2xl bg-cyan-50 dark:bg-cyan-900/30 text-cyan-600 dark:text-cyan-400 shadow-lg shadow-cyan-100 dark:shadow-cyan-900/20 border-2 border-white dark:border-zinc-700 transform -rotate-6"
						>
							<MessageSquare class="w-5 h-5 sm:w-6 sm:h-6" />
						</div>
						<div>
							<h2
								class="text-lg sm:text-xl font-bold text-gray-900 dark:text-white leading-tight relative w-fit"
							>
								{t('admin.feedback.modal.title')}
							</h2>
						</div>
					</div>

					<button
						onclick={handleClose}
						class="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-full transition-all cursor-pointer"
					>
						<X class="w-5 h-5 sm:w-6 sm:h-6" />
					</button>
				</div>

				<form
					onsubmit={(e) => {
						e.preventDefault();
						handleSubmit();
					}}
					class="space-y-5 sm:space-y-6"
				>
					<div class="space-y-2">
						<label for="status" class="text-sm font-bold text-gray-700 dark:text-gray-300 ml-1">
							{t('admin.feedback.modal.statusLabel')}
						</label>
						<div class="relative">
							<select
								id="status"
								name="status"
								bind:value={formData.status}
								class="w-full px-4 pr-10 py-3 bg-gray-50 dark:bg-zinc-800/50 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-2 focus:ring-cyan-500 focus:border-transparent outline-none transition-all cursor-pointer appearance-none font-medium"
							>
								<option value="pending">{t('feedback.status.pending')}</option>
								<option value="noted">{t('feedback.status.noted')}</option>
								<option value="in_progress">{t('feedback.status.in_progress')}</option>
								<option value="implemented">{t('feedback.status.implemented')}</option>
								<option value="rejected">{t('feedback.status.rejected')}</option>
								<option value="spam">{t('feedback.status.spam')}</option>
							</select>
							<ChevronDown
								class="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 pointer-events-none"
							/>
						</div>
					</div>

					<div class="space-y-2">
						<div class="flex items-center justify-between ml-1 mb-1">
							<div class="flex items-center gap-2">
								<label for="admin_notes" class="text-sm font-bold text-gray-700 dark:text-gray-300">
									{t('admin.feedback.modal.notesLabel')}
								</label>
								<span
									class="px-2 py-0.5 rounded-full bg-slate-100 dark:bg-zinc-800 text-[10px] font-bold text-slate-500 uppercase tracking-wider"
								>
									{t('forms.optional')}
								</span>
							</div>
							<span
								class="text-xs font-bold {formData.admin_notes.length >= 1000
									? 'text-red-500'
									: 'text-slate-400'}"
							>
								{formData.admin_notes.length}/1000
							</span>
						</div>
						<textarea
							id="admin_notes"
							name="admin_notes"
							bind:value={formData.admin_notes}
							rows="4"
							maxlength="1000"
							placeholder={t('admin.feedback.modal.notesPlaceholder')}
							class="w-full px-4 py-3 bg-gray-50 dark:bg-zinc-800/50 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-2 focus:ring-cyan-500 focus:border-transparent outline-none transition-all resize-y min-h-[100px] max-h-[300px] text-sm font-medium"
						></textarea>
						<p class="text-xs text-slate-500 dark:text-slate-400 ml-1 leading-relaxed">
							{t('admin.feedback.modal.notesInfo')}
						</p>
					</div>

					<div class="pt-4 sm:pt-6 flex gap-2 sm:gap-3">
						<button
							type="button"
							onclick={handleClose}
							class="flex-1 px-3 sm:px-4 py-3 rounded-xl text-sm sm:text-base font-bold text-gray-600 dark:text-gray-300 bg-gray-100 dark:bg-zinc-800 hover:bg-gray-200 dark:hover:bg-zinc-700 transition-colors cursor-pointer"
						>
							{t('common.cancel')}
						</button>
						<button
							type="submit"
							disabled={isSubmitting}
							class="flex-[2] px-3 sm:px-4 py-3 rounded-xl text-sm sm:text-base font-bold text-white bg-gradient-to-r from-cyan-600 to-cyan-500 hover:from-cyan-500 hover:to-cyan-400 shadow-lg shadow-cyan-500/30 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-all cursor-pointer"
						>
							{#if isSubmitting}
								<LoaderCircle class="w-4 h-4 sm:w-5 sm:h-5 animate-spin" />
								{t('admin.feedback.modal.saving')}
							{:else}
								<CircleCheck class="w-4 h-4 sm:w-5 sm:h-5" />
								{t('admin.feedback.modal.saveChanges')}
							{/if}
						</button>
					</div>
				</form>
			</div>
		</div>
	</div>
{/if}
