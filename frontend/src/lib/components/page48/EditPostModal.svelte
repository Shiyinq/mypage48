<script lang="ts">
	import { X, EyeOff } from 'lucide-svelte';
	import { portal } from '$lib/actions/portal';
	import { page48Api, type Page48Post } from '$lib/api/page48';
	import { showToast } from '$lib/stores/toast.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { fade } from 'svelte/transition';

	interface Props {
		post: Page48Post;
		onClose: () => void;
		onSaved?: (post: Page48Post) => void;
	}

	let { post, onClose, onSaved }: Props = $props();

	const { t } = useTranslation();

	// svelte-ignore state_referenced_locally
	let content = $state(post.content ?? '');
	// svelte-ignore state_referenced_locally
	let spoilerOn = $state(post.isSpoiler ?? false);
	let submitting = $state(false);

	let canSave = $derived(
		content.trim().length > 0 && (content !== post.content || spoilerOn !== post.isSpoiler)
	);

	async function save() {
		if (submitting || !canSave) return;
		submitting = true;
		try {
			const updated = await page48Api.editPost(post.postId, content.trim(), spoilerOn);
			onSaved?.(updated);
			showToast(t('page48.edit.success'), 'success');
			onClose();
		} catch (err: unknown) {
			const e = err as { detail?: string; message?: string };
			showToast(e?.detail || e?.message || t('page48.edit.error'), 'error');
		} finally {
			submitting = false;
		}
	}

	function handleKeydown(e: KeyboardEvent) {
		if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
			e.preventDefault();
			void save();
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
			<h3 class="text-base font-bold text-gray-900 dark:text-gray-100">
				{t('page48.edit.title')}
			</h3>
			<button
				class="p-1 rounded-full text-gray-400 hover:bg-gray-100 dark:hover:bg-zinc-800 cursor-pointer"
				onclick={onClose}
				aria-label={t('page48.aria.close')}
			>
				<X size={16} />
			</button>
		</div>

		<textarea
			bind:value={content}
			onkeydown={handleKeydown}
			rows="4"
			maxlength="500"
			placeholder={t('page48.edit.placeholder')}
			class="mt-4 w-full rounded-xl bg-gray-50 dark:bg-zinc-800/60 border border-gray-200 dark:border-zinc-800 p-3 text-[14px] text-gray-900 dark:text-gray-100 outline-none resize-none focus:border-red-300 dark:focus:border-red-900"
		></textarea>

		<button
			type="button"
			class="mt-3 flex w-full items-center justify-between gap-3 rounded-xl border border-gray-200 px-3 py-2.5 text-left transition-colors cursor-pointer hover:bg-gray-50 dark:border-zinc-800 dark:hover:bg-zinc-800"
			onclick={() => (spoilerOn = !spoilerOn)}
			aria-pressed={spoilerOn}
		>
			<span
				class="flex items-center gap-2 text-[13px] font-semibold text-gray-800 dark:text-gray-200"
			>
				<EyeOff size={16} class={spoilerOn ? 'text-amber-500' : 'text-gray-400'} />
				{t('page48.spoiler.label')}
			</span>
			<span
				class={`relative inline-flex h-5 w-9 shrink-0 items-center rounded-full transition-colors ${
					spoilerOn ? 'bg-red-500' : 'bg-gray-300 dark:bg-zinc-700'
				}`}
			>
				<span
					class={`inline-block h-3.5 w-3.5 rounded-full bg-white shadow transition-transform ${
						spoilerOn ? 'translate-x-5' : 'translate-x-1'
					}`}
				></span>
			</span>
		</button>

		<div class="flex justify-end gap-2 mt-5">
			<button
				class="px-4 py-2 rounded-full border border-gray-200 dark:border-zinc-800 text-[13px] font-semibold text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
				onclick={onClose}
				disabled={submitting}
			>
				{t('common.cancel')}
			</button>
			<button
				class="px-4 py-2 rounded-full bg-black dark:bg-white text-white dark:text-black text-[13px] font-semibold transition-colors cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
				onclick={save}
				disabled={submitting || !canSave}
			>
				{t('page48.edit.save')}
			</button>
		</div>
	</div>
</div>
