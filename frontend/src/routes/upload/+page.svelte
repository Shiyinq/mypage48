<script lang="ts">
	import { onMount } from 'svelte';
	import {
		Upload,
		CheckCircle2,
		AlertCircle,
		Ticket as TicketIcon,
		RefreshCw,
		Trash2,
		Camera,
		PlusCircle
	} from 'lucide-svelte';
	import { fade, fly } from 'svelte/transition';
	import SEO from '$lib/components/SEO.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { showToast, setlistsStore, ticketsStore } from '$lib/stores';
	import { extractTicketData } from '$lib/apis/llm';
	import { THEATER_ROWS } from '$lib/constants/time';
	import { SHOW_IMAGES } from '$lib/constants/shows';
	import { page } from '$app/stores';
	import { LoaderCircle } from 'lucide-svelte';
	import type { Ticket } from '$lib/types';
	import type { Setlist } from '$lib/apis/setlists';

	const { t } = useTranslation();

	const SHOW_OPTIONS = SHOW_IMAGES.map((s) => s.title);

	let mode: 'CHOOSING' | 'SCANNING' | 'MANUAL' | 'ANALYZING' | 'PREVIEW' | 'SUCCESS' =
		$state('CHOOSING');
	let fileInput: HTMLInputElement | undefined = $state();
	let videoEl: HTMLVideoElement | undefined = $state();
	let canvasEl: HTMLCanvasElement | undefined = $state();
	let stream: MediaStream | null = $state(null);

	// Ticket Data state - Aligned with Partial<Ticket>
	let ticketData = $state<Partial<Ticket>>({
		event: {
			title: '',
			date: '', // YYYY-MM-DD
			day: '',
			time: '',
			venue: 'JKT48 Theater'
		},
		seat: {
			section: '',
			number: ''
		},
		imageUrl: ''
	});

	onMount(() => {
		const urlMode = $page.url.searchParams.get('mode');
		if (urlMode === 'scan') {
			mode = 'SCANNING';
			startCamera();
		} else if (urlMode === 'manual') {
			mode = 'MANUAL';
		}
	});

	const startCamera = async () => {
		try {
			stream = await navigator.mediaDevices.getUserMedia({
				video: { facingMode: 'environment' }
			});
			if (videoEl) videoEl.srcObject = stream;
		} catch (_err) {
			showToast($t('upload.cameraError'), 'error');
			mode = 'CHOOSING';
		}
	};

	const stopCamera = () => {
		if (stream) {
			stream.getTracks().forEach((track) => track.stop());
			stream = null;
		}
	};

	const captureImage = () => {
		if (!videoEl || !canvasEl) return;
		const context = canvasEl.getContext('2d');
		if (!context) return;

		canvasEl.width = videoEl.videoWidth;
		canvasEl.height = videoEl.videoHeight;
		context.drawImage(videoEl, 0, 0, canvasEl.width, canvasEl.height);

		const base64 = canvasEl.toDataURL('image/jpeg', 0.8);
		stopCamera();
		analyzeImage(base64);
	};

	const handleFileUpload = (e: Event) => {
		const target = e.target as HTMLInputElement;
		const file = target.files?.[0];
		if (!file) return;

		const reader = new FileReader();
		reader.onload = (event) => {
			const base64 = event.target?.result as string;
			analyzeImage(base64);
		};
		reader.readAsDataURL(file);
	};

	const analyzeImage = async (base64: string) => {
		mode = 'ANALYZING';
		try {
			const result = await extractTicketData(base64);
			await setlistsStore.load();

			const currentSetlists = setlistsStore.data
				? setlistsStore.data.map((s: Setlist) => s.title)
				: SHOW_OPTIONS;

			const detectedTitle =
				currentSetlists.find((opt: string) =>
					(result.title || '').toLowerCase().includes(opt.toLowerCase())
				) || '';
			const inputChar = (result.section || '').toUpperCase().trim().charAt(0);
			const detectedRow = (THEATER_ROWS as ReadonlyArray<string>).includes(inputChar)
				? inputChar
				: '';

			ticketData = {
				event: {
					title: detectedTitle,
					date: result.date || new Date().toISOString().split('T')[0],
					day: result.day || '',
					time: result.time || '',
					venue: 'JKT48 Theater'
				},
				seat: {
					section: detectedRow,
					number: result.number || ''
				},
				imageUrl: base64
			};
			mode = 'PREVIEW';
		} catch {
			showToast($t('upload.ocrError'), 'error');
			mode = 'CHOOSING';
		}
	};

	const handleSubmit = async () => {
		try {
			await ticketsStore.create(ticketData);
			mode = 'SUCCESS';
			showToast($t('upload.success'), 'success');
		} catch {
			showToast($t('upload.saveError'), 'error');
		}
	};

	const reset = () => {
		stopCamera();
		mode = 'CHOOSING';
		ticketData = {
			event: { title: '', date: '', day: '', time: '', venue: 'JKT48 Theater' },
			seat: { section: '', number: '' },
			imageUrl: ''
		};
	};
</script>

<SEO title={$t('upload.title')} path="/upload" />

<div class="max-w-4xl mx-auto px-4 py-8">
	<div class="space-y-8">
		<!-- Header -->
		<div class="text-center space-y-2">
			<h1 class="text-3xl font-black text-slate-900 dark:text-white uppercase tracking-tight">
				{$t('upload.title')}
			</h1>
			<p class="text-slate-500 dark:text-slate-400 font-medium tracking-wide">
				{$t('upload.subtitle')}
			</p>
		</div>

		<div class="glass-panel p-6 md:p-10 rounded-[2.5rem] border-themed relative overflow-hidden">
			{#if mode === 'CHOOSING'}
				<div in:fade class="grid grid-cols-1 md:grid-cols-2 gap-6 relative z-10">
					<button
						onclick={() => {
							mode = 'SCANNING';
							startCamera();
						}}
						class="group flex flex-col items-center justify-center p-8 rounded-[2rem] bg-pink-50 dark:bg-pink-900/10 border-2 border-dashed border-pink-200 dark:border-pink-500/20 hover:border-pink-500 transition-all space-y-4"
					>
						<div
							class="w-16 h-16 rounded-full bg-pink-500 text-white flex items-center justify-center shadow-lg shadow-pink-500/20 group-hover:scale-110 transition-transform"
						>
							<Camera class="w-8 h-8" />
						</div>
						<div class="text-center">
							<h3 class="font-bold text-slate-900 dark:text-white">{$t('upload.capture')}</h3>
							<p class="text-xs text-slate-500 dark:text-slate-400 mt-1">
								{$t('upload.captureDesc')}
							</p>
						</div>
					</button>

					<button
						onclick={() => fileInput?.click()}
						class="group flex flex-col items-center justify-center p-8 rounded-[2rem] bg-slate-50 dark:bg-zinc-800/10 border-2 border-dashed border-slate-200 dark:border-white/10 hover:border-slate-500 transition-all space-y-4"
					>
						<div
							class="w-16 h-16 rounded-full bg-slate-900 dark:bg-white text-white dark:text-slate-900 flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform"
						>
							<Upload class="w-8 h-8" />
						</div>
						<div class="text-center">
							<h3 class="font-bold text-slate-900 dark:text-white">{$t('upload.upload')}</h3>
							<p class="text-xs text-slate-500 dark:text-slate-400 mt-1">
								{$t('upload.uploadDesc')}
							</p>
						</div>
						<input
							type="file"
							accept="image/*"
							class="hidden"
							bind:this={fileInput}
							onchange={handleFileUpload}
						/>
					</button>

					<div class="md:col-span-2 pt-4 border-t border-themed text-center">
						<button
							onclick={() => (mode = 'MANUAL')}
							class="inline-flex items-center gap-2 text-sm font-bold text-slate-500 hover:text-slate-900 dark:hover:text-white transition-colors cursor-pointer"
						>
							<PlusCircle class="w-4 h-4 text-pink-500" />
							{$t('upload.manualLink')}
						</button>
					</div>
				</div>
			{:else if mode === 'SCANNING'}
				<div in:fade class="space-y-6 flex flex-col items-center">
					<div
						class="relative w-full aspect-square md:aspect-video bg-black rounded-[2rem] overflow-hidden"
					>
						<!-- eslint-disable-next-line jsx-a11y/media-has-caption -->
						<video bind:this={videoEl} autoplay playsinline class="w-full h-full object-cover"
						></video>
						<div
							class="absolute inset-0 border-2 border-white/30 m-8 rounded-xl pointer-events-none"
						>
							<div class="absolute inset-0 flex items-center justify-center">
								<div class="w-64 h-96 border-2 border-pink-500 rounded-lg animate-pulse"></div>
							</div>
						</div>
					</div>

					<div class="flex items-center gap-4">
						<button
							onclick={reset}
							class="px-6 py-3 rounded-xl font-bold text-slate-500 hover:text-slate-900 dark:hover:text-white transition-colors"
						>
							{$t('common.cancel')}
						</button>
						<button
							onclick={captureImage}
							class="px-10 py-3 rounded-xl bg-pink-500 text-white font-black uppercase tracking-widest shadow-lg shadow-pink-500/20 active:scale-95 transition-all"
						>
							{$t('upload.snap')}
						</button>
					</div>
					<canvas bind:this={canvasEl} class="hidden"></canvas>
				</div>
			{:else if mode === 'ANALYZING'}
				<div
					in:fade
					class="py-20 flex flex-col items-center justify-center space-y-6 text-slate-500 dark:text-slate-400"
				>
					<div class="relative">
						<LoaderCircle class="w-16 h-16 animate-spin text-pink-500 mx-auto" />
						<div class="absolute inset-0 m-auto w-6 h-6 animate-reverse-spin">
							<RefreshCw class="w-full h-full text-pink-300" />
						</div>
					</div>
					<div class="text-center space-y-1">
						<p class="text-lg font-black text-slate-900 dark:text-white uppercase tracking-widest">
							{$t('upload.analyzing')}
						</p>
						<p class="text-xs font-medium uppercase tracking-widest opacity-60">
							{$t('upload.analyzingDesc')}
						</p>
					</div>
				</div>
			{:else if mode === 'PREVIEW' || mode === 'MANUAL'}
				<div in:fly={{ y: 20 }} class="space-y-8">
					<div class="grid grid-cols-1 md:grid-cols-2 gap-8">
						{#if ticketData.imageUrl}
							<div class="order-2 md:order-1 space-y-3">
								<p class="text-[10px] font-black uppercase text-slate-400 tracking-widest">
									{$t('upload.preview')}
								</p>
								<div class="rounded-3xl overflow-hidden shadow-2xl border-themed group relative">
									<img
										src={ticketData.imageUrl}
										alt="Ticket Preview"
										class="w-full aspect-[3/4] object-cover"
									/>
									<button
										onclick={() => (ticketData.imageUrl = '')}
										class="absolute top-4 right-4 p-2 bg-black/50 hover:bg-red-500 text-white rounded-xl backdrop-blur-md opacity-0 group-hover:opacity-100 transition-all cursor-pointer"
									>
										<Trash2 class="w-4 h-4" />
									</button>
								</div>
							</div>
						{/if}

						<div class="order-1 md:order-2 space-y-6 pt-4">
							<div class="grid grid-cols-1 gap-6">
								<!-- Show Select -->
								<div class="space-y-2">
									<label
										for="show"
										class="text-[10px] font-black uppercase text-slate-400 tracking-widest flex items-center gap-2"
									>
										<TicketIcon class="w-3 h-3 text-pink-500" />
										{$t('upload.label.show')}
									</label>
									<select
										id="show"
										bind:value={ticketData.event!.title}
										class="w-full px-4 py-3 bg-slate-50 dark:bg-zinc-800/50 border border-themed rounded-2xl text-sm font-bold focus:ring-2 focus:ring-pink-500/20 transition-all"
									>
										{#each setlistsStore.data || SHOW_OPTIONS as opt}
											{@const val = typeof opt === 'string' ? opt : opt.title}
											<option value={val}>{val}</option>
										{/each}
									</select>
								</div>

								<!-- Date -->
								<div class="space-y-2">
									<label
										for="date"
										class="text-[10px] font-black uppercase text-slate-400 tracking-widest"
									>
										{$t('upload.label.date')}
									</label>
									<input
										id="date"
										type="date"
										bind:value={ticketData.event!.date}
										class="w-full px-4 py-3 bg-slate-50 dark:bg-zinc-800/50 border border-themed rounded-2xl text-sm font-bold focus:ring-2 focus:ring-pink-500/20 transition-all"
									/>
								</div>

								<div class="grid grid-cols-2 gap-4">
									<div class="space-y-2">
										<label
											for="row"
											class="text-[10px] font-black uppercase text-slate-400 tracking-widest"
										>
											{$t('upload.label.row')}
										</label>
										<select
											id="row"
											bind:value={ticketData.seat!.section}
											class="w-full px-4 py-3 bg-slate-50 dark:bg-zinc-800/50 border border-themed rounded-2xl text-sm font-bold"
										>
											{#each THEATER_ROWS as row}
												<option value={row}>{row}</option>
											{/each}
										</select>
									</div>
									<div class="space-y-2">
										<label
											for="number"
											class="text-[10px] font-black uppercase text-slate-400 tracking-widest"
										>
											{$t('upload.label.seatNumber')}
										</label>
										<input
											id="number"
											type="text"
											bind:value={ticketData.seat!.number}
											class="w-full px-4 py-3 bg-slate-50 dark:bg-zinc-800/50 border border-themed rounded-2xl text-sm font-bold"
										/>
									</div>
								</div>
							</div>
						</div>
					</div>

					<div class="flex items-center justify-end gap-3 pt-6 border-t border-themed">
						<button
							onclick={reset}
							class="px-6 py-3 rounded-xl font-bold text-slate-500 hover:text-slate-900 dark:hover:text-white transition-colors cursor-pointer"
						>
							{$t('common.cancel')}
						</button>
						<button
							onclick={handleSubmit}
							class="px-10 py-3 rounded-xl bg-slate-900 dark:bg-white text-white dark:text-slate-900 font-black uppercase tracking-widest shadow-xl active:scale-95 transition-all cursor-pointer"
						>
							{$t('upload.save')}
						</button>
					</div>
				</div>
			{:else if mode === 'SUCCESS'}
				<div in:fade class="py-10 flex flex-col items-center justify-center space-y-6 text-center">
					<div class="relative">
						<div class="absolute inset-0 bg-emerald-500 blur-2xl opacity-20 animate-pulse"></div>
						<CheckCircle2 class="w-24 h-24 text-emerald-500 relative z-10" />
					</div>
					<div class="space-y-2">
						<h2
							class="text-2xl font-black text-slate-900 dark:text-white uppercase tracking-tighter"
						>
							{$t('upload.successTitle')}
						</h2>
						<p class="text-slate-500 dark:text-slate-400 max-w-xs mx-auto font-medium">
							{$t('upload.successDesc')}
						</p>
					</div>
					<div class="flex items-center gap-3 pt-4">
						<button
							onclick={reset}
							class="px-8 py-3 rounded-xl bg-slate-50 dark:bg-zinc-800 text-slate-900 dark:text-white font-bold hover:bg-slate-100 transition-all cursor-pointer"
						>
							{$t('upload.addAnother')}
						</button>
						<a
							href="/history"
							class="px-8 py-3 rounded-xl bg-slate-900 dark:bg-white text-white dark:text-slate-900 font-bold hover:bg-black transition-all"
						>
							{$t('upload.viewHistory')}
						</a>
					</div>
				</div>
			{/if}
		</div>

		<div class="flex items-center gap-2 p-4 bg-amber-500/10 border border-amber-500/20 rounded-2xl">
			<AlertCircle class="w-5 h-5 text-amber-500 shrink-0" />
			<p class="text-xs font-bold text-amber-600 dark:text-amber-400 leading-relaxed">
				{$t('upload.privacyNotice')}
			</p>
		</div>
	</div>
</div>

<style>
	@keyframes reverse-spin {
		from {
			transform: rotate(360deg);
		}
		to {
			transform: rotate(0deg);
		}
	}
	.animate-reverse-spin {
		animation: reverse-spin 2s linear infinite;
	}
</style>
