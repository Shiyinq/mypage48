<script lang="ts">
	import { createEventDispatcher, tick } from 'svelte';
	import { fade } from 'svelte/transition';
	import type { Ticket } from '$lib/types';
	import { storageApi } from '$lib/apis/storage';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { getExternalMediaUrl } from '$lib/utils/media';

	// Icons
	import {
		Bold,
		Italic,
		List,
		ListOrdered,
		Link as LinkIcon,
		Image as ImageIcon,
		Save,
		Eye,
		PenLine,
		Heading1,
		Heading2,
		Quote,
		Code,
		Minus
	} from 'lucide-svelte';

	// Markdown parsing
	import { marked } from 'marked';
	import DOMPurify from 'dompurify';

	export let ticket: Ticket;

	const { t } = useTranslation();
	const dispatch = createEventDispatcher();

	let isEditing = false;
	let content = '';
	let isUploading = false;
	let textareaEl: HTMLTextAreaElement;
    let scrollContainer: HTMLDivElement;

	let currentTicketId = '';

	// When ticket changes, update local state only if it's a new ticket
	$: if (ticket && ticket._id !== currentTicketId) {
		currentTicketId = ticket._id;
		content = ticket.notes || '';
		isEditing = !content; // Start in edit mode if empty
	}

	async function toggleMode() {
        const currentScroll = scrollContainer?.scrollTop || 0;
		isEditing = !isEditing;
		if (isEditing) {
			await tick();
            if (textareaEl) {
                textareaEl.setSelectionRange(0, 0);
                textareaEl.focus();
                if (scrollContainer) {
                    scrollContainer.scrollTop = currentScroll;
                }
            }
		}
	}

	async function handleSave() {
		if (content !== ticket.notes) {
			dispatch('save', { ticketId: ticket._id, note: content });
		}
		isEditing = false;
	}

	function toggleSidebar() {
		dispatch('toggleSidebar');
	}

	// Rich text helpers
	function insertText(prefix: string, suffix: string = '') {
		if (!textareaEl) return;

		const start = textareaEl.selectionStart;
		const end = textareaEl.selectionEnd;
		const text = textareaEl.value;

		const selectedText = text.substring(start, end);
		const newText = text.substring(0, start) + prefix + selectedText + suffix + text.substring(end);

		content = newText;

		// Preserve cursor
		setTimeout(() => {
			textareaEl.focus();
			textareaEl.setSelectionRange(start + prefix.length, end + prefix.length);
		}, 0);
	}

	async function handleImageUpload(e: Event) {
		const target = e.target as HTMLInputElement;
		const file = target.files?.[0];
		if (!file) return;

		// Clear input so same file can be uploaded again if needed
		target.value = '';

		isUploading = true;
		try {
			// Convert to base64
			const reader = new FileReader();
			const base64 = await new Promise<string>((resolve, reject) => {
				reader.onload = () => resolve(reader.result as string);
				reader.onerror = reject;
				reader.readAsDataURL(file);
			});

			// 'ticket' is a valid ImageCategory
			const res = await storageApi.uploadImage(base64, 'ticket');
			const imageUrl = getExternalMediaUrl(res.filename);
			
			insertText(`![](${imageUrl})`);
		} catch (e) {
			console.error('Failed to upload image', e);
		} finally {
			isUploading = false;
		}
	}

	$: parsedHtml = isEditing ? '' : DOMPurify.sanitize(marked.parse(content) as string);
</script>

<div class={`h-full flex flex-col relative w-full transition-colors duration-500 ${isEditing ? 'bg-transparent' : 'bg-white dark:bg-zinc-950'}`}>
	
	<!-- Header -->
	<div class="px-4 md:px-8 py-4 shrink-0 bg-white/95 dark:bg-zinc-950/95 backdrop-blur-md sticky top-0 z-20">
        <div class="flex items-start justify-between gap-3 md:gap-4 w-full max-w-3xl mx-auto">
            <!-- Left Info -->
            <div class="flex-1">
                <h1 class="text-xl md:text-2xl font-black text-gray-900 dark:text-white leading-tight balance-text mb-1.5">
                    {ticket.event.title}
                </h1>
                <div class="inline-flex items-center gap-2 px-2.5 py-0.5 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-full text-[9px] font-bold uppercase tracking-widest">
                    {ticket.event.date} • {ticket.event.time}
                </div>
            </div>

            <!-- Action Buttons -->
            <div class="flex items-center gap-2 shrink-0 pt-1">
                {#if isEditing}
                    <button on:click={toggleMode} class="px-3 py-1.5 text-xs font-semibold text-gray-600 dark:text-gray-400 bg-gray-100 hover:bg-gray-200 dark:bg-zinc-800 dark:hover:bg-zinc-700 rounded-lg flex items-center gap-1.5 transition-colors cursor-pointer">
                        <Eye class="w-3.5 h-3.5" />
                        <span class="hidden sm:inline">{$t('journal.previewToggle')}</span>
                    </button>
                    <button on:click={handleSave} class="px-4 py-1.5 text-xs font-black text-white bg-red-600 hover:bg-red-700 shadow-md shadow-red-500/20 rounded-lg flex items-center gap-1.5 transition-all cursor-pointer">
                        <Save class="w-3.5 h-3.5" />
                        <span class="hidden sm:inline">{$t('journal.save')}</span>
                    </button>
                {:else}
                    <button on:click={toggleMode} class="px-3 py-1.5 text-xs font-semibold text-gray-600 dark:text-gray-400 bg-gray-100 hover:bg-gray-200 dark:bg-zinc-800 dark:hover:bg-zinc-700 rounded-lg flex items-center gap-1.5 transition-colors cursor-pointer">
                        <PenLine class="w-3.5 h-3.5" />
                        <span class="hidden sm:inline">{$t('journal.writeToggle')}</span>
                    </button>
                {/if}
            </div>
        </div>
	</div>

	<!-- Editor & Preview Area -->
	<div bind:this={scrollContainer} class="flex-1 overflow-y-auto px-6 md:px-10 py-6 custom-scrollbar flex justify-center">
		<div class="w-full max-w-3xl flex flex-col min-h-full">
			
			<!-- Toolbar -->
            {#if isEditing}
			    <div class="flex items-center border-b border-gray-100 dark:border-zinc-800 pb-2 mb-4 shrink-0 transition-all">
                    <div class="flex gap-0.5 md:gap-1 items-center">
                        <button class="p-1.5 md:p-2 text-gray-500 hover:bg-gray-100 dark:hover:bg-zinc-800 rounded transition-colors cursor-pointer" title="Heading 1" on:click={() => insertText('# ')}>
                            <Heading1 class="w-4 h-4" />
                        </button>
                        <button class="p-1.5 md:p-2 text-gray-500 hover:bg-gray-100 dark:hover:bg-zinc-800 rounded transition-colors cursor-pointer" title="Heading 2" on:click={() => insertText('## ')}>
                            <Heading2 class="w-4 h-4" />
                        </button>
                        <div class="w-px h-4 bg-gray-200 dark:bg-zinc-700 mx-1"></div>
                        <button class="p-1.5 md:p-2 text-gray-500 hover:bg-gray-100 dark:hover:bg-zinc-800 rounded transition-colors cursor-pointer" title="Bold" on:click={() => insertText('**', '**')}>
                            <Bold class="w-4 h-4" />
                        </button>
                        <button class="p-1.5 md:p-2 text-gray-500 hover:bg-gray-100 dark:hover:bg-zinc-800 rounded transition-colors cursor-pointer" title="Italic" on:click={() => insertText('*', '*')}>
                            <Italic class="w-4 h-4" />
                        </button>
                        <div class="w-px h-4 bg-gray-200 dark:bg-zinc-700 mx-1"></div>
                        <button class="p-1.5 md:p-2 text-gray-500 hover:bg-gray-100 dark:hover:bg-zinc-800 rounded transition-colors cursor-pointer" title="Quote" on:click={() => insertText('> ')}>
                            <Quote class="w-4 h-4" />
                        </button>
                        <button class="p-1.5 md:p-2 text-gray-500 hover:bg-gray-100 dark:hover:bg-zinc-800 rounded transition-colors cursor-pointer" title="Code" on:click={() => insertText('`', '`')}>
                            <Code class="w-4 h-4" />
                        </button>
                        <div class="w-px h-4 bg-gray-200 dark:bg-zinc-700 mx-1"></div>
                        <button class="p-1.5 md:p-2 text-gray-500 hover:bg-gray-100 dark:hover:bg-zinc-800 rounded transition-colors cursor-pointer" title="List" on:click={() => insertText('- ')}>
                            <List class="w-4 h-4" />
                        </button>
                        <button class="p-1.5 md:p-2 text-gray-500 hover:bg-gray-100 dark:hover:bg-zinc-800 rounded transition-colors cursor-pointer" title="Ordered List" on:click={() => insertText('1. ')}>
                            <ListOrdered class="w-4 h-4" />
                        </button>
                        <div class="w-px h-4 bg-gray-200 dark:bg-zinc-700 mx-1"></div>
                        <button class="p-1.5 md:p-2 text-gray-500 hover:bg-gray-100 dark:hover:bg-zinc-800 rounded transition-colors cursor-pointer" title="Link" on:click={() => insertText('[', '](url)')}>
                            <LinkIcon class="w-4 h-4" />
                        </button>
                        <label class="p-1.5 md:p-2 text-gray-500 hover:bg-gray-100 dark:hover:bg-zinc-800 rounded cursor-pointer transition-colors relative" title="Image">
                            <ImageIcon class="w-4 h-4" />
                            <input type="file" accept="image/jpeg,image/png,image/webp" class="hidden" on:change={handleImageUpload} disabled={isUploading} />
                            {#if isUploading}
                                <span class="absolute inset-0 bg-white/80 dark:bg-zinc-900/80 flex items-center justify-center rounded">
                                    <span class="w-2 h-2 border-2 border-red-500 border-t-transparent rounded-full animate-spin"></span>
                                </span>
                            {/if}
                        </label>
                        <div class="w-px h-4 bg-gray-200 dark:bg-zinc-700 mx-1"></div>
                        <button class="p-1.5 md:p-2 text-gray-500 hover:bg-gray-100 dark:hover:bg-zinc-800 rounded transition-colors cursor-pointer" title="Divider" on:click={() => insertText('\n---\n')}>
                            <Minus class="w-4 h-4" />
                        </button>
                    </div>
                </div>
            {/if}

			<!-- Main TextField -->
			{#if isEditing}
				<!-- Editing Mode -->
				<div class="flex-1 flex flex-col h-full relative group">
					<textarea
						bind:this={textareaEl}
						bind:value={content}
						placeholder={$t('journal.startWriting')}
						class="w-full flex-1 min-h-[500px] resize-none outline-none bg-transparent text-gray-800 dark:text-gray-200 text-lg sm:text-xl leading-relaxed custom-scrollbar pb-20 font-serif placeholder:font-sans placeholder:text-gray-300 dark:placeholder:text-gray-700"
					></textarea>
				</div>
			{:else}
				<!-- Preview Mode -->
				<div class="flex-1 pb-20 w-full relative">
					{#if !content}
						<!-- Empty View Mode -->
						<div class="flex flex-col items-center justify-center p-12 opacity-50 cursor-pointer pb-32" on:click={toggleMode} on:keydown={(e) => e.key === 'Enter' && toggleMode()} role="button" tabindex="0">
							<PenLine class="w-10 h-10 mb-4 text-gray-300 dark:text-gray-700" />
							<p class="text-sm font-medium text-gray-400 dark:text-gray-500 text-center max-w-sm">
								{$t('journal.startWriting')}
							</p>
						</div>
					{:else}
						<div class="prose prose-red prose-img:rounded-xl prose-img:shadow-lg dark:prose-invert max-w-none prose-lg md:prose-xl prose-p:leading-relaxed font-serif w-full shrink-0 h-full">
							{@html parsedHtml}
						</div>
					{/if}
				</div>
			{/if}
		</div>
	</div>
</div>

<style>
	/* Minimal styling for prose area */
	:global(.prose img) {
		margin-left: auto;
		margin-right: auto;
		max-height: 600px;
		object-fit: cover;
	}
	.balance-text {
		text-wrap: balance;
	}
</style>
