<script lang="ts">
	import { X, Flag } from 'lucide-svelte';
	import { portal } from '$lib/actions/portal';
	import { page48Api, type ReportReason, type ReportTargetType } from '$lib/api/page48';
	import { showToast } from '$lib/stores/toast.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { fade } from 'svelte/transition';

	interface Props {
		targetType: ReportTargetType;
		targetId: string;
		onClose: () => void;
	}

	let { targetType, targetId, onClose }: Props = $props();

	const { t } = useTranslation();

	const reasons: ReportReason[] = ['spam', 'harassment', 'inappropriate', 'other'];

	let reason = $state<ReportReason>('spam');
	let note = $state('');
	let submitting = $state(false);

	async function submit() {
		if (submitting) return;
		submitting = true;
		try {
			await page48Api.createReport({
				targetType,
				targetId,
				reason,
				note: note.trim() ? note.trim() : null
			});
			showToast(t('page48.report.success'), 'success');
			onClose();
		} catch (err: unknown) {
			const e = err as { detail?: string; message?: string };
			showToast(e?.detail || e?.message || t('page48.report.error'), 'error');
		} finally {
			submitting = false;
		}
	}
</script>

<div
	use:portal
	class="fixed inset-0 z-[10060] flex items-center justify-center p-4"
	transition:fade={{ duration: 150 }}
	role="dialog"
	aria-modal="true"
>
	<div
		class="absolute inset-0 bg-black/60 backdrop-blur-sm"
		onclick={onClose}
		role="presentation"
	></div>

	<div
		class="relative w-full max-w-md rounded-2xl bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 p-5 shadow-2xl"
	>
		<div class="flex items-start justify-between gap-3">
			<div class="flex items-center gap-2">
				<Flag size={18} class="text-red-500" />
				<h3 class="text-base font-bold text-gray-900 dark:text-gray-100">
					{targetType === 'post' ? t('page48.report.titlePost') : t('page48.report.titleUser')}
				</h3>
			</div>
			<button
				class="p-1 rounded-full text-gray-400 hover:bg-gray-100 dark:hover:bg-zinc-800 cursor-pointer"
				onclick={onClose}
				aria-label={t('page48.aria.close')}
			>
				<X size={16} />
			</button>
		</div>

		<div class="mt-4">
			<p class="text-[13px] font-semibold text-gray-700 dark:text-gray-300 mb-2">
				{t('page48.report.reasonLabel')}
			</p>
			<div class="flex flex-col gap-1">
				{#each reasons as item (item)}
					<label
						class="flex items-center gap-3 px-3 py-2 rounded-xl hover:bg-gray-50 dark:hover:bg-white/5 cursor-pointer"
					>
						<input
							type="radio"
							name="report-reason"
							value={item}
							bind:group={reason}
							class="accent-red-600"
						/>
						<span class="text-[14px] text-gray-800 dark:text-gray-200">
							{t(`page48.report.reason.${item}`)}
						</span>
					</label>
				{/each}
			</div>
		</div>

		<div class="mt-4">
			<label
				for="report-note"
				class="text-[13px] font-semibold text-gray-700 dark:text-gray-300 mb-2 block"
			>
				{t('page48.report.noteLabel')}
			</label>
			<textarea
				id="report-note"
				bind:value={note}
				rows="3"
				maxlength="500"
				class="w-full rounded-xl bg-gray-50 dark:bg-zinc-800/60 border border-gray-200 dark:border-zinc-800 p-3 text-[14px] text-gray-900 dark:text-gray-100 outline-none resize-none focus:border-red-300 dark:focus:border-red-900"
			></textarea>
		</div>

		<div class="flex justify-end gap-2 mt-5">
			<button
				class="px-4 py-2 rounded-full border border-gray-200 dark:border-zinc-800 text-[13px] font-semibold text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
				onclick={onClose}
			>
				{t('common.cancel')}
			</button>
			<button
				class="px-4 py-2 rounded-full bg-red-600 hover:bg-red-700 text-white text-[13px] font-semibold transition-colors cursor-pointer disabled:opacity-50"
				onclick={submit}
				disabled={submitting}
			>
				{t('page48.report.submit')}
			</button>
		</div>
	</div>
</div>
