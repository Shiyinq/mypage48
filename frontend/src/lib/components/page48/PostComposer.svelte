<script lang="ts">
	import { Image as ImageIcon, X, Loader2 } from 'lucide-svelte';
	import { fade } from 'svelte/transition';
	import { userProfile } from '$lib/stores/profile.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	const { t } = useTranslation();

	interface Props {
		onPost: (content: string, images: File[]) => Promise<void>;
		isReply?: boolean;
		placeholder?: string;
	}

	let { onPost, isReply = false, placeholder }: Props = $props();

	let resolvedPlaceholder = $derived(placeholder ?? t('page48.composer.placeholder'));

	let content = $state('');
	let images = $state<File[]>([]);
	let imagePreviews = $state<string[]>([]);
	let isSubmitting = $state(false);
	let fileInput: HTMLInputElement;

	function handleFileSelect(e: Event) {
		const target = e.target as HTMLInputElement;
		if (!target.files) return;

		const newFiles = Array.from(target.files);
		if (images.length + newFiles.length > 4) {
			alert(t('page48.composer.maxPhotos'));
			return;
		}

		for (const file of newFiles) {
			if (!file.type.startsWith('image/')) continue;
			if (file.size > 3 * 1024 * 1024) {
				alert(t('page48.composer.maxSize'));
				continue;
			}
			images = [...images, file];
			imagePreviews = [...imagePreviews, URL.createObjectURL(file)];
		}

		// Reset input
		target.value = '';
	}

	function removeImage(index: number) {
		URL.revokeObjectURL(imagePreviews[index]);
		images = images.filter((_, i) => i !== index);
		imagePreviews = imagePreviews.filter((_, i) => i !== index);
	}

	async function handleSubmit() {
		if (!content.trim() && images.length === 0) return;
		if (isSubmitting) return;

		try {
			isSubmitting = true;
			await onPost(content, images);
			content = '';
			images = [];
			imagePreviews.forEach(URL.revokeObjectURL);
			imagePreviews = [];
		} catch (error) {
			console.error(error);
		} finally {
			isSubmitting = false;
		}
	}

	let userAvatar = $derived(
		userProfile.data?.profilePicture_small ||
			(userProfile.data
				? `https://ui-avatars.com/api/?name=${encodeURIComponent(userProfile.data.name || '')}&background=fca5a5&color=fff`
				: null)
	);
</script>

<div
	class="flex gap-4 py-5 px-5 sm:px-6 border-b border-gray-100 dark:border-white/10 bg-white/60 dark:bg-zinc-950/60 backdrop-blur-xl transition-all"
>
	<!-- Avatar -->
	<div class="shrink-0 pt-1">
		<div
			class="w-11 h-11 rounded-full overflow-hidden bg-gray-100 dark:bg-zinc-800 ring-2 ring-white dark:ring-zinc-900 shadow-sm"
		>
			{#if userAvatar}
				<img
					src={userAvatar}
					alt={t('page48.aria.profile')}
					class="w-full h-full object-cover"
					onerror={(e) => {
						(e.target as HTMLImageElement).src =
							`https://ui-avatars.com/api/?name=${encodeURIComponent(userProfile.data?.name || '')}&background=fca5a5&color=fff`;
					}}
				/>
			{:else}
				<div
					class="w-full h-full bg-red-100 flex items-center justify-center text-red-500 font-bold"
				>
					?
				</div>
			{/if}
		</div>
	</div>

	<!-- Composer Content -->
	<div class="flex-1 min-w-0 flex flex-col pt-1.5">
		<!-- Active Username -->
		{#if userProfile.data}
			<span class="font-semibold text-[15px] tracking-tight text-gray-900 dark:text-gray-100"
				>{userProfile.data.name}</span
			>
		{/if}

		<textarea
			bind:value={content}
			placeholder={resolvedPlaceholder}
			class="w-full bg-transparent text-gray-900 dark:text-gray-100 text-[15px] resize-none outline-none placeholder:text-gray-400 dark:placeholder:text-gray-500 mt-1 pb-2 leading-relaxed"
			rows="1"
			oninput={(e) => {
				const target = e.target as HTMLTextAreaElement;
				target.style.height = 'auto';
				target.style.height = target.scrollHeight + 'px';
			}}
		></textarea>

		<!-- Image Previews -->
		{#if imagePreviews.length > 0}
			<div class="flex gap-2 mt-2 mb-2 overflow-x-auto pb-2 snap-x" in:fade>
				{#each imagePreviews as preview, i}
					<div class="relative shrink-0 snap-start">
						<img
							src={preview}
							alt={t('page48.composer.previewAlt')}
							class="h-32 w-auto rounded-xl border border-gray-200 dark:border-zinc-800 object-cover"
						/>
						<button
							class="absolute top-1 right-1 w-6 h-6 bg-black/60 hover:bg-black text-white rounded-full flex items-center justify-center transition-colors cursor-pointer"
							onclick={() => removeImage(i)}
						>
							<X size={14} />
						</button>
					</div>
				{/each}
			</div>
		{/if}

		<!-- Action Bar -->
		<div class="flex items-center justify-between mt-3 pt-2 border-t border-transparent">
			<!-- Media Input -->
			<button
				class="p-2 -ml-2 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 rounded-full transition-all disabled:opacity-50 group cursor-pointer"
				onclick={() => fileInput.click()}
				disabled={images.length >= 4 || isSubmitting}
				title={t('page48.composer.addPhoto')}
			>
				<ImageIcon size={20} class="group-hover:scale-110 transition-transform" />
			</button>
			<input
				type="file"
				accept="image/jpeg,image/png,image/webp"
				multiple
				class="hidden"
				bind:this={fileInput}
				onchange={handleFileSelect}
			/>

			<!-- Submit Button -->
			<button
				class="px-5 py-2 bg-black dark:bg-white text-white dark:text-black rounded-full font-semibold text-[14px] disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer hover:bg-gray-800 dark:hover:bg-gray-200 transition-all flex items-center gap-2 active:scale-95 shadow-sm"
				disabled={(!content.trim() && images.length === 0) || isSubmitting}
				onclick={handleSubmit}
			>
				{#if isSubmitting}
					<Loader2 size={16} class="animate-spin" />
				{/if}
				{isReply ? t('page48.composer.reply') : t('page48.composer.submit')}
			</button>
		</div>
	</div>
</div>
