<script lang="ts">
	import { tickets, showToast } from '$lib/stores';
	import { goto } from '$app/navigation';
	import { extractTicketData } from '$lib/services/geminiService';
	import { theater } from '$lib/apis/theater';
	import type { Ticket } from '$lib/types';
	import {
		Loader2,
		Upload,
		Camera,
		CheckCircle,
		AlertCircle,
		NotebookPen,
		Keyboard,
		ScanLine,
		Calendar,
		Clock,
		MapPin,
		DollarSign,
		Hash,
		Ticket as TicketIcon,
		X,
		ChevronDown,
		ImagePlus,
		User,
		Sparkles,
		TrendingUp
	} from 'lucide-svelte';
	import SEO from '$lib/components/SEO.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import MemberSelector from '$lib/components/MemberSelector.svelte';

	const { t } = useTranslation();

	// Constants
	const SHOW_OPTIONS = [
		'Pertaruhan Cinta',
		'Pajama Drive',
		'Aturan Anti Cinta',
		'Sambil Menggandeng Erat Tanganku',
		'Cara Meminum Ramune',
		'Ingin Bertemu',
		'KIRA KIRA GIRLS'
	];
	const ROW_OPTIONS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'];

	let mode: 'SELECTION' | 'ANALYZING' | 'EDITING' = 'SELECTION';
	let image: string | null = null;
	let error: string | null = null;
	let isSubmitting = false;

	// 2-Shot
	let showTwoShot = false;
	let twoShotImage: string | null = null;
	let twoShotInputRef: HTMLInputElement;

	// Temporary state matching Ticket structure but editable
	let formData = {
		event: {
			title: '',
			date: new Date().toISOString().split('T')[0],
			day: '',
			time: '',
			gate_open: '',
			venue: 'JKT48 Theater'
		},
		seat: {
			section: '',
			number: ''
		},
		ticket_id: '',
		price: 200000,
		currency: 'IDR',
		notes: '',
		rules: { refund_allowed: false, exchange_allowed: false },
		two_shot: {
			imageUrl: '',
			member_name: '',
			type: 'Roulette' as 'Roulette' | 'Birthday',
			price: 100000
		}
	};

	let fileInputRef: HTMLInputElement;

	// Normalization
	const normalizeTime = (raw: string | undefined): string => {
		if (!raw) return '';
		const clean = raw.trim().toUpperCase();
		const amPmMatch = clean.match(/(\d{1,2})[:.](\d{2})\s*(AM|PM)?/);
		if (amPmMatch) {
			let [_, h, m, period] = amPmMatch;
			let hours = parseInt(h, 10);
			if (period === 'PM' && hours < 12) hours += 12;
			if (period === 'AM' && hours === 12) hours = 0;
			return `${hours.toString().padStart(2, '0')}:${m}`;
		}
		const simpleMatch = clean.match(/(\d{1,2})[:.](\d{2})/);
		return simpleMatch ? `${simpleMatch[1].padStart(2, '0')}:${simpleMatch[2]}` : '';
	};

	const handleFileChange = (e: Event) => {
		const target = e.target as HTMLInputElement;
		const file = target.files?.[0];
		if (!file) return;
		const reader = new FileReader();
		reader.onloadend = () => {
			image = reader.result as string;
			if (mode === 'SELECTION') analyzeImage(image);
		};
		reader.readAsDataURL(file);
	};

	const analyzeImage = async (base64: string) => {
		mode = 'ANALYZING';
		error = null;
		try {
			const result = await extractTicketData(base64);
			// ... Match logic ...
			const detectedTitle =
				SHOW_OPTIONS.find((opt) =>
					(result.title || '').toLowerCase().includes(opt.toLowerCase())
				) || '';
			const detectedRow = ROW_OPTIONS.includes(
				(result.section || '').toUpperCase().trim().charAt(0)
			)
				? (result.section || '').toUpperCase().trim().charAt(0)
				: '';

			formData = {
				...formData,
				ticket_id: result.ticket_id || '',
				price: result.price || 200000,
				event: {
					...formData.event,
					title: detectedTitle,
					date: result.date || formData.event.date,
					day: result.day || '',
					time: normalizeTime(result.time),
					gate_open: normalizeTime(result.gate_open)
				},
				seat: { ...formData.seat, section: detectedRow, number: result.number || '' }
			};
			mode = 'EDITING';
		} catch (e) {
			console.error(e);
			error = 'Could not read ticket details automatically.';
			mode = 'EDITING';
		}
	};

	const handleTwoShotFileChange = (e: Event) => {
		const target = e.target as HTMLInputElement;
		const file = target.files?.[0];
		if (!file) return;
		const reader = new FileReader();
		reader.onloadend = () => {
			twoShotImage = reader.result as string;
		};
		reader.readAsDataURL(file);
	};

	const onCancel = () => goto('/');

	const handleFormSubmit = async () => {
		isSubmitting = true;
		try {
			// Prepare object for API
			const payload = {
				ticket_id: formData.ticket_id || `MANUAL-${Date.now()}`,
				event: formData.event,
				seat: { ...formData.seat, number: Number(formData.seat.number) },
				price: Number(formData.price),
				currency: 'IDR',
				rules: formData.rules,
				imageUrl: image || undefined,
				notes: formData.notes,
				two_shot: showTwoShot
					? {
							imageUrl: twoShotImage || undefined,
							member_name: formData.two_shot.member_name,
							type: formData.two_shot.type,
							price: Number(formData.two_shot.price)
						}
					: undefined
			};

			await theater.createTicket(payload);
			// Fetch fresh data from server after create
			const freshTickets = await theater.getMyTickets();
			tickets.set(freshTickets);
			showToast('Ticket saved successfully!');
			goto('/');
		} catch (e) {
			console.error(e);
			showToast('Failed to save ticket. Please try again.', 'error');
		} finally {
			isSubmitting = false;
		}
	};

	const handleManualEntry = () => {
		mode = 'EDITING';
		image = null;
	};

	// Validation
	$: isFormValid =
		formData.event.title &&
		formData.event.date &&
		formData.event.time &&
		formData.seat.section &&
		formData.seat.number &&
		formData.price > 0 &&
		formData.ticket_id &&
		(!showTwoShot || (showTwoShot && formData.two_shot.member_name));
</script>

<SEO title={$t('upload.title')} path="/upload" description={$t('seo.upload')} />

{#if mode === 'SELECTION'}
	<div
		class="min-h-[80vh] flex flex-col items-center justify-center p-4 animate-fade-in max-w-4xl mx-auto"
	>
		<div class="text-center mb-10">
			<h2 class="text-3xl font-black text-gray-800 dark:text-white mb-2">{$t('upload.title')}</h2>
			<p class="text-gray-500 dark:text-gray-400">{$t('upload.subtitle')}</p>
		</div>
		<div class="grid md:grid-cols-2 gap-6 w-full">
			<button
				on:click={() => fileInputRef.click()}
				class="group relative overflow-hidden bg-white dark:bg-zinc-800 p-8 rounded-3xl border-2 border-red-100 dark:border-red-900/30 hover:border-red-500 dark:hover:border-red-500 shadow-lg hover:shadow-xl transition-all duration-300 text-left flex flex-col h-64 justify-between cursor-pointer"
			>
				<div
					class="absolute top-0 right-0 w-32 h-32 bg-red-50 dark:bg-red-900/10 rounded-bl-full -mr-10 -mt-10 transition-transform group-hover:scale-110"
				></div>
				<div
					class="p-4 bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 rounded-2xl w-fit z-10"
				>
					<ScanLine class="w-8 h-8" />
				</div>
				<div class="z-10">
					<h3
						class="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-1 group-hover:text-red-600 dark:group-hover:text-red-400 transition-colors"
					>
						{$t('upload.scanTicket')}
					</h3>
					<p class="text-sm font-medium text-gray-600 dark:text-gray-400 leading-relaxed">
						{$t('upload.scanDescription')}
					</p>
				</div>
			</button>
			<button
				on:click={handleManualEntry}
				class="group relative overflow-hidden bg-white dark:bg-zinc-800 p-8 rounded-3xl border-2 border-gray-100 dark:border-zinc-700 hover:border-gray-400 dark:hover:border-zinc-500 shadow-lg hover:shadow-xl transition-all duration-300 text-left flex flex-col h-64 justify-between cursor-pointer"
			>
				<div
					class="absolute top-0 right-0 w-32 h-32 bg-gray-50 dark:bg-zinc-700/50 rounded-bl-full -mr-10 -mt-10 transition-transform group-hover:scale-110"
				></div>
				<div
					class="p-4 bg-gray-100 dark:bg-zinc-700 text-gray-600 dark:text-gray-300 rounded-2xl w-fit z-10"
				>
					<Keyboard class="w-8 h-8" />
				</div>
				<div class="z-10">
					<h3
						class="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-1 group-hover:text-gray-600 dark:group-hover:text-gray-300 transition-colors"
					>
						{$t('upload.manualEntry')}
					</h3>
					<p class="text-sm font-medium text-gray-600 dark:text-gray-400">
						{$t('upload.manualDescription')}
					</p>
				</div>
			</button>
		</div>
		<button
			on:click={onCancel}
			class="mt-12 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 font-medium text-sm flex items-center gap-2 px-4 py-2 rounded-full hover:bg-gray-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
		>
			<X class="w-4 h-4" />
			{$t('common.cancel')}
		</button>
	</div>
{/if}

{#if mode === 'ANALYZING'}
	<div
		class="h-[80vh] flex flex-col items-center justify-center text-gray-400 space-y-6 animate-fade-in"
	>
		<div class="relative">
			<div
				class="w-20 h-20 border-4 border-red-100 border-t-red-600 rounded-full animate-spin"
			></div>
			<div class="absolute inset-0 flex items-center justify-center">
				<ScanLine class="w-8 h-8 text-red-600 animate-pulse" />
			</div>
		</div>
		<div class="text-center">
			<h3 class="text-xl font-bold text-gray-800">Analyzing Ticket</h3>
			<p class="text-sm text-gray-500 mt-1">Extracting show info...</p>
		</div>
	</div>
{/if}

{#if mode === 'EDITING'}
	<div class="max-w-5xl mx-auto p-4 pb-24 animate-fade-in">
		<div class="flex items-center justify-between mb-6">
			<div class="flex items-center gap-3">
				<div
					class="p-3 rounded-2xl bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 shadow-lg shadow-red-100 dark:shadow-red-900/20 border-2 border-white dark:border-zinc-700 transform -rotate-6"
				>
					<Keyboard class="w-6 h-6" />
				</div>
				<div>
					<h2 class="text-2xl font-bold text-themed leading-none relative w-fit">
						{$t('forms.newTicket')}
						<span
							class="absolute -bottom-1 left-0 w-full h-2 bg-red-200/60 dark:bg-red-500/30 -z-10 transform -skew-x-12 rounded-sm"
						></span>
					</h2>
					<p class="text-sm text-gray-500 dark:text-gray-400 mt-1">{$t('forms.addToCollection')}</p>
				</div>
			</div>
			<button
				on:click={onCancel}
				class="text-sm font-bold text-gray-500 dark:text-gray-400 hover:text-red-600 bg-white dark:bg-zinc-800 px-4 py-2 rounded-full shadow-sm border border-gray-200 dark:border-zinc-700 cursor-pointer"
				>{$t('forms.cancel')}</button
			>
		</div>

		<div class="grid gap-8 lg:grid-cols-2">
			<!-- Image Preview -->
			<div class="flex flex-col gap-4">
				<div class="sticky top-24">
					{#if image}
						<div
							class="relative rounded-3xl overflow-hidden border border-gray-200 dark:border-zinc-700 bg-gray-100 dark:bg-zinc-800 shadow-lg aspect-[4/5] lg:aspect-auto lg:h-[calc(100vh-200px)] group"
						>
							<img src={image} alt="Preview" class="w-full h-full object-contain p-4" />
							<div
								class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center"
							>
								<button
									on:click={() => fileInputRef.click()}
									class="bg-white text-gray-800 px-4 py-2 rounded-full font-bold text-sm flex items-center gap-2 shadow-lg hover:scale-105 transition-transform"
									><ImagePlus class="w-4 h-4" /> {$t('forms.changePhoto')}</button
								>
							</div>
						</div>
					{:else}
						<div
							on:click={() => fileInputRef.click()}
							class="rounded-3xl border-3 border-dashed border-gray-200 dark:border-zinc-700 bg-gray-50 dark:bg-zinc-800 hover:bg-red-50 dark:hover:bg-red-900/20 hover:border-red-200 dark:hover:border-red-500/50 transition-all cursor-pointer flex flex-col items-center justify-center aspect-[4/5] lg:aspect-auto lg:h-[calc(100vh-200px)] text-gray-400 dark:text-gray-500 hover:text-red-500"
						>
							<div class="p-4 rounded-full bg-white dark:bg-zinc-700 shadow-sm mb-4">
								<ImagePlus class="w-8 h-8" />
							</div>
							<p class="font-bold text-lg">{$t('forms.uploadTicketPhoto')}</p>
							<p class="text-xs text-gray-400 dark:text-gray-500 mt-1">{$t('forms.optional')}</p>
						</div>
					{/if}
					{#if error}
						<div
							class="bg-red-50 text-red-600 p-4 rounded-2xl mt-4 text-sm flex items-start gap-3 border border-red-100 shadow-sm"
						>
							<AlertCircle class="w-5 h-5 flex-shrink-0 mt-0.5" />
							<div>
								<p class="font-bold">{$t('forms.analysisIssue')}</p>
								<p>{error}</p>
							</div>
						</div>
					{/if}
				</div>
			</div>

			<!-- FORM -->
			<div
				class="bg-white/80 dark:bg-zinc-800/80 backdrop-blur-xl p-6 md:p-8 rounded-3xl border border-white/50 dark:border-zinc-700 shadow-xl h-fit"
			>
				<form on:submit|preventDefault={handleFormSubmit} class="space-y-8">
					<!-- Event Details -->
					<div class="space-y-4">
						<h3
							class="text-xs font-black text-gray-400 dark:text-gray-500 uppercase tracking-widest mb-4 flex items-center gap-2"
						>
							<TicketIcon class="w-4 h-4" />
							{$t('forms.eventDetails')}
						</h3>
						<div>
							<label class="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-1.5 ml-1"
								>{$t('forms.showTitle')}</label
							>
							<div class="relative group">
								<div
									class="absolute left-3 top-1/2 -translate-y-1/2 text-red-400 z-10 pointer-events-none"
								>
									<TicketIcon class="w-5 h-5" />
								</div>
								<select
									bind:value={formData.event.title}
									class="w-full pl-10 pr-10 py-3 bg-gray-50 dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none font-bold text-gray-900 dark:text-gray-100 transition-all appearance-none cursor-pointer"
								>
									<option value="" disabled>{$t('forms.selectSetlist')}</option>
									{#each SHOW_OPTIONS as show}<option value={show}>{show}</option>{/each}
								</select>
								<ChevronDown
									class="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none"
								/>
							</div>
						</div>
						<div class="grid grid-cols-2 gap-4">
							<div>
								<label class="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-1.5 ml-1"
									>{$t('forms.date')}</label
								>
								<div class="relative">
									<div class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
										<Calendar class="w-4 h-4" />
									</div>
									<input
										type="date"
										bind:value={formData.event.date}
										class="w-full pl-9 pr-3 py-3 bg-gray-50 dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-red-500 outline-none text-sm font-medium text-gray-900 dark:text-gray-100"
									/>
								</div>
							</div>
							<div>
								<label class="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-1.5 ml-1"
									>{$t('forms.showTime')}</label
								>
								<div class="relative">
									<div class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
										<Clock class="w-4 h-4" />
									</div>
									<input
										type="time"
										bind:value={formData.event.time}
										class="w-full pl-9 pr-3 py-3 bg-gray-50 dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-red-500 outline-none text-sm font-medium text-gray-900 dark:text-gray-100"
									/>
								</div>
							</div>
						</div>
					</div>

					<!-- Seat & Price -->
					<div class="space-y-4 pt-4 border-t border-gray-100 dark:border-zinc-700">
						<h3
							class="text-xs font-black text-gray-400 dark:text-gray-500 uppercase tracking-widest mb-4 flex items-center gap-2"
						>
							<MapPin class="w-4 h-4" />
							{$t('forms.seatPayment')}
						</h3>
						<div class="grid grid-cols-3 gap-4">
							<div>
								<label class="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-1.5 ml-1"
									>{$t('forms.row')}</label
								>
								<div class="relative">
									<select
										bind:value={formData.seat.section}
										class="w-full p-3 bg-gray-50 dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-red-500 outline-none text-center font-black text-lg text-gray-900 dark:text-gray-100 appearance-none cursor-pointer"
									>
										<option value="" disabled>-</option>
										{#each ROW_OPTIONS as r}<option value={r}>{r}</option>{/each}
									</select>
									<ChevronDown
										class="absolute right-2 top-1/2 -translate-y-1/2 w-3 h-3 text-gray-300 pointer-events-none"
									/>
								</div>
							</div>
							<div class="col-span-2">
								<label class="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-1.5 ml-1"
									>{$t('forms.seatNumber')}</label
								>
								<input
									type="number"
									bind:value={formData.seat.number}
									class="w-full p-3 bg-gray-50 dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-red-500 outline-none text-center font-black text-lg text-gray-900 dark:text-gray-100 placeholder-gray-300 dark:placeholder-gray-600"
									placeholder="1"
								/>
							</div>
						</div>
						<div class="grid grid-cols-2 gap-4">
							<div>
								<label class="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-1.5 ml-1"
									>{$t('forms.price')}</label
								>
								<div class="relative">
									<div class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
										<DollarSign class="w-4 h-4" />
									</div>
									<input
										type="number"
										bind:value={formData.price}
										class="w-full pl-9 pr-3 py-3 bg-gray-50 dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-red-500 outline-none font-medium text-gray-900 dark:text-gray-100"
										placeholder="200000"
									/>
								</div>
							</div>
							<div>
								<label class="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-1.5 ml-1"
									>{$t('forms.ticketId')}</label
								>
								<div class="relative">
									<div class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
										<Hash class="w-4 h-4" />
									</div>
									<input
										type="text"
										bind:value={formData.ticket_id}
										class="w-full pl-9 pr-3 py-3 bg-gray-50 dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-red-500 outline-none text-sm font-medium text-gray-900 dark:text-gray-100"
										placeholder="T123456"
									/>
								</div>
							</div>
						</div>
					</div>

					<!-- 2-Shot -->
					<div class="space-y-4">
						<div
							class="flex items-center justify-between pt-4 border-t border-gray-100 dark:border-zinc-700 mb-4"
						>
							<h3
								class="text-xs font-black text-gray-400 dark:text-gray-500 uppercase tracking-widest flex items-center gap-2"
							>
								<Camera class="w-4 h-4" />
								{$t('forms.twoShotDetails')}
							</h3>
							<button
								type="button"
								on:click={() => (showTwoShot = !showTwoShot)}
								class={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 cursor-pointer ${showTwoShot ? 'bg-red-600' : 'bg-gray-200 dark:bg-zinc-700'}`}
							>
								<span
									class={`inline-block h-4 w-4 transform rounded-full bg-white transition duration-200 ease-in-out ${showTwoShot ? 'translate-x-6' : 'translate-x-1'}`}
								/>
							</button>
						</div>
						{#if showTwoShot}
							<div
								class="bg-red-50/50 dark:bg-zinc-800/50 rounded-2xl p-4 border border-red-100 dark:border-red-500/30 space-y-4 animate-fade-in"
							>
								<div>
									<label class="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-2 ml-1"
										>{$t('forms.twoShotPhoto')}</label
									>
									<div
										on:click={() => twoShotInputRef.click()}
										class="w-full h-32 border-2 border-dashed border-red-200 dark:border-red-900/30 rounded-xl bg-white dark:bg-zinc-900 hover:bg-red-50 dark:hover:bg-red-900/10 transition-colors cursor-pointer flex items-center justify-center overflow-hidden relative group"
									>
										{#if twoShotImage}
											<img src={twoShotImage} alt="2shot" class="w-full h-full object-contain" />
											<div
												class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center text-white font-bold text-xs"
											>
												{$t('forms.changePhoto')}
											</div>
										{:else}
											<div class="flex flex-col items-center text-red-400 dark:text-red-500">
												<Camera class="w-6 h-6 mb-1" />
												<span class="text-xs font-medium">{$t('forms.uploadPhoto')}</span>
											</div>
										{/if}
									</div>
								</div>

								<div>
									<label
										class="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-1.5 ml-1"
										>{$t('forms.memberName')}</label
									>
									<MemberSelector
										bind:value={formData.two_shot.member_name}
										placeholder={$t('forms.memberNamePlaceholder')}
										title={$t('forms.selectMember')}
										subtitle={$t('forms.selectMemberDesc')}
									/>
								</div>

								<div class="grid grid-cols-2 gap-4">
									<div>
										<label
											class="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-1.5 ml-1"
											>{$t('forms.type')}</label
										>
										<div class="relative">
											<div class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
												<Sparkles class="w-4 h-4" />
											</div>
											<select
												bind:value={formData.two_shot.type}
												class="w-full pl-9 pr-8 py-3 bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-red-500 outline-none text-sm font-medium text-gray-900 dark:text-gray-100 appearance-none cursor-pointer"
											>
												<option value="Roulette">Roulette</option>
												<option value="Birthday">Birthday</option>
											</select>
											<ChevronDown
												class="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none"
											/>
										</div>
									</div>

									<div>
										<label
											class="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-1.5 ml-1"
											>{$t('forms.price')}</label
										>
										<div class="relative">
											<div class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
												<DollarSign class="w-4 h-4" />
											</div>
											<input
												type="number"
												bind:value={formData.two_shot.price}
												class="w-full pl-9 pr-3 py-3 bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-red-500 outline-none text-sm font-medium text-gray-900 dark:text-gray-100"
											/>
										</div>
									</div>
								</div>
							</div>
						{/if}
					</div>

					<!-- Notes -->
					<div class="space-y-4 pt-4 border-t border-gray-100 dark:border-zinc-700">
						<h3
							class="text-xs font-black text-gray-400 dark:text-gray-500 uppercase tracking-widest mb-4 flex items-center gap-2"
						>
							<NotebookPen class="w-4 h-4" />
							{$t('forms.experienceLog')}
						</h3>
						<textarea
							bind:value={formData.notes}
							class="w-full p-4 bg-yellow-50/50 dark:bg-zinc-800/50 border border-yellow-200 dark:border-zinc-700 rounded-xl focus:ring-2 focus:ring-yellow-400 dark:focus:ring-zinc-600 outline-none text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-600 min-h-[120px]"
							placeholder={$t('forms.notesPlaceholder')}
						></textarea>
					</div>

					<button
						type="submit"
						disabled={isSubmitting || !isFormValid}
						class="w-full idol-gradient text-white py-4 rounded-2xl font-bold text-lg shadow-lg shadow-red-200 hover:shadow-xl hover:scale-[1.01] transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer disabled:shadow-none disabled:transform-none"
					>
						{#if isSubmitting}
							<Loader2 class="w-6 h-6 animate-spin" />
						{:else}
							<CheckCircle class="w-6 h-6" />
						{/if}
						{$t('forms.saveTicket')}
					</button>
				</form>
			</div>
		</div>
	</div>
{/if}

<input
	type="file"
	bind:this={fileInputRef}
	class="hidden"
	accept="image/*"
	on:change={handleFileChange}
/>
<input
	type="file"
	bind:this={twoShotInputRef}
	class="hidden"
	accept="image/*"
	on:change={handleTwoShotFileChange}
/>
