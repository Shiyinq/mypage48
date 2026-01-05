<script lang="ts">
	import { ticketsStore, showToast } from '$lib/stores';
	import { invalidateDashboard } from '$lib/stores/dashboard';
	import { invalidateTheater } from '$lib/stores/theater';
	import { validateImageFile, getValidationErrorI18nKey } from '$lib/utils/fileValidation';
	import { calculateDayFromDate, calculateGateOpenTime } from '$lib/utils/ticketUtils';
	import ValidationAlertModal from '$lib/components/ValidationAlertModal.svelte';
	import type { Ticket } from '$lib/types';
	import {
		LoaderCircle,
		Camera,
		CircleCheck,
		NotebookPen,
		Calendar,
		Clock,
		MapPin,
		DollarSign,
		Hash,
		Ticket as TicketIcon,
		ChevronDown,
		ImagePlus,
		Sparkles
	} from 'lucide-svelte';
	import { createEventDispatcher } from 'svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import MemberSelector from '$lib/components/MemberSelector.svelte';
	import { SHOW_IMAGES, THEATER_ROWS } from '$lib/constants';

	export let ticket: Ticket;

	const dispatch = createEventDispatcher();
	const { t } = useTranslation();
	const SHOW_OPTIONS = SHOW_IMAGES.map((s) => s.title);
	const ROW_OPTIONS = THEATER_ROWS;

	let isSubmitting = false;
	let fileInputRef: HTMLInputElement;
	let twoShotInputRef: HTMLInputElement;

	// State
	let formData = {
		event: { ...ticket.event },
		seat: { ...ticket.seat },
		ticket_id: ticket.ticket_id,
		price: ticket.price,
		currency: ticket.currency,
		notes: ticket.notes || '',
		rules: { ...ticket.rules },
		two_shot: ticket.two_shot
			? { ...ticket.two_shot }
			: {
					imageUrl: '',
					member_name: '',
					type: 'Roulette' as 'Roulette' | 'Birthday',
					price: 100000
				}
	};

	let image: string | null = ticket.imageUrl || null;
	let showTwoShot = !!ticket.two_shot;
	let twoShotImage: string | null = ticket.two_shot?.imageUrl || null;

	// Validation alert modal state
	let showValidationAlert = false;
	let validationAlertMessage = '';

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

	// Reactive Day Calculation
	$: if (formData.event.date) {
		const newDay = calculateDayFromDate(formData.event.date);
		if (newDay && newDay !== formData.event.day) {
			formData.event.day = newDay;
			formData = { ...formData }; // Force update
		}
	}

	// Reactive Gate Open Calculation (30 mins before Show Time)
	$: if (formData.event.time) {
		const newGateOpen = calculateGateOpenTime(formData.event.time);
		if (newGateOpen && newGateOpen !== formData.event.gate_open) {
			formData.event.gate_open = newGateOpen;
			formData = { ...formData }; // Force update
		}
	}

	// Handlers
	const handleFileChange = (e: Event) => {
		const target = e.target as HTMLInputElement;
		const file = target.files?.[0];
		if (!file) return;

		// Validate file before processing
		const validation = validateImageFile(file);
		if (!validation.valid) {
			validationAlertMessage = $t(getValidationErrorI18nKey(validation.error));
			showValidationAlert = true;
			target.value = ''; // Reset input
			return;
		}

		const reader = new FileReader();
		reader.onloadend = () => {
			image = reader.result as string;
		};
		reader.readAsDataURL(file);
	};

	const handleTwoShotFileChange = (e: Event) => {
		const target = e.target as HTMLInputElement;
		const file = target.files?.[0];
		if (!file) return;

		// Validate file before processing
		const validation = validateImageFile(file);
		if (!validation.valid) {
			validationAlertMessage = $t(getValidationErrorI18nKey(validation.error));
			showValidationAlert = true;
			target.value = ''; // Reset input
			return;
		}

		const reader = new FileReader();
		reader.onloadend = () => {
			twoShotImage = reader.result as string;
		};
		reader.readAsDataURL(file);
	};

	const handleSubmit = async () => {
		isSubmitting = true;
		try {
			const payload = {
				ticket_id: formData.ticket_id,
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
					: null
			};

			const updated = await ticketsStore.updateTicket(ticket._id, payload);

			// Invalidate dashboard and theater cache
			invalidateDashboard();
			invalidateTheater();

			showToast('Ticket updated successfully!');
			dispatch('save', updated);
			dispatch('close');
		} catch (e) {
			console.error(e);
			showToast('Failed to update ticket.', 'error');
		} finally {
			isSubmitting = false;
		}
	};
</script>

<div class="fixed inset-0 z-[9999] flex items-center justify-center p-4 sm:p-6">
	<!-- Backdrop -->
	<!-- svelte-ignore a11y-click-events-have-key-events -->
	<!-- svelte-ignore a11y-no-static-element-interactions -->
	<div
		class="absolute inset-0 bg-black/80 backdrop-blur-sm transition-opacity duration-300"
		on:click={() => dispatch('close')}
	></div>

	<!-- Modal Content -->
	<div
		class="bg-white/95 dark:bg-zinc-900/95 backdrop-blur-xl w-full max-w-5xl h-[90vh] rounded-3xl shadow-2xl overflow-y-auto custom-scrollbar relative z-10 animate-fade-in"
	>
		<div class="max-w-5xl mx-auto p-4 md:p-8 pb-24">
			<!-- Header -->
			<div class="flex items-center justify-between mb-6">
				<div class="flex items-center gap-3">
					<div
						class="p-3 rounded-2xl bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 shadow-lg shadow-red-100 dark:shadow-red-900/20 border-2 border-white dark:border-zinc-700 transform -rotate-6"
					>
						<NotebookPen class="w-6 h-6" />
					</div>
					<div>
						<h2 class="text-2xl font-bold text-themed leading-none relative w-fit">
							{$t('forms.editTicket')}
							<span
								class="absolute -bottom-1 left-0 w-full h-2 bg-red-200/60 dark:bg-red-500/30 -z-10 transform -skew-x-12 rounded-sm"
							></span>
						</h2>
					</div>
				</div>

				<button
					on:click={() => dispatch('close')}
					class="text-sm font-bold text-gray-500 dark:text-gray-400 hover:text-red-600 bg-white dark:bg-zinc-800 px-4 py-2 rounded-full shadow-sm border border-gray-200 dark:border-zinc-700 cursor-pointer"
				>
					{$t('forms.cancel')}
				</button>
			</div>

			<div class="grid gap-8 lg:grid-cols-2">
				<!-- Left: Image Preview -->
				<div class="flex flex-col gap-4">
					<div class="sticky top-6">
						{#if image}
							<div
								class="relative rounded-3xl overflow-hidden border border-gray-200 dark:border-zinc-700 bg-gray-100 dark:bg-zinc-800 shadow-lg aspect-[4/5] lg:aspect-auto lg:h-[calc(100vh-300px)] group"
							>
								<img src={image} alt="Preview" class="w-full h-full object-contain p-4" />
								<div
									class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center"
								>
									<button
										on:click={() => fileInputRef.click()}
										class="bg-white text-gray-800 px-4 py-2 rounded-full font-bold text-sm flex items-center gap-2 shadow-lg hover:scale-105 transition-transform"
									>
										<ImagePlus class="w-4 h-4" />
										{$t('forms.changePhoto')}
									</button>
								</div>
							</div>
						{:else}
							<button
								type="button"
								on:click={() => fileInputRef.click()}
								class="w-full rounded-3xl border-3 border-dashed border-gray-200 dark:border-zinc-700 bg-gray-50 dark:bg-zinc-800 hover:bg-red-50 dark:hover:bg-red-900/20 hover:border-red-200 dark:hover:border-red-500/50 transition-all cursor-pointer flex flex-col items-center justify-center aspect-[4/5] lg:aspect-auto lg:h-[calc(100vh-300px)] text-gray-400 dark:text-gray-500 hover:text-red-500"
							>
								<div class="p-4 rounded-full bg-white dark:bg-zinc-700 shadow-sm mb-4">
									<ImagePlus class="w-8 h-8" />
								</div>
								<p class="font-bold text-lg">{$t('forms.uploadPhoto')}</p>
								<p class="text-xs text-gray-400 dark:text-gray-500 mt-1">
									({$t('forms.optional')})
								</p>
							</button>
						{/if}
					</div>
				</div>

				<!-- Right: Form -->
				<div
					class="bg-white/80 dark:bg-zinc-800/80 backdrop-blur-xl p-6 md:p-8 rounded-3xl border border-white/50 dark:border-zinc-700 shadow-xl h-fit"
				>
					<form on:submit|preventDefault={handleSubmit} class="space-y-8">
						<!-- Event Details -->
						<div class="space-y-4">
							<h3
								class="text-xs font-black text-gray-400 dark:text-gray-500 uppercase tracking-widest mb-4 flex items-center gap-2"
							>
								<TicketIcon class="w-4 h-4" />
								{$t('forms.eventDetails')}
							</h3>

							<div>
								<label
									class="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-1.5 ml-1"
									for="event-title">{$t('forms.showTitle')}</label
								>
								<div class="relative group">
									<div
										class="absolute left-3 top-1/2 -translate-y-1/2 text-red-400 z-10 pointer-events-none"
									>
										<TicketIcon class="w-5 h-5" />
									</div>
									<select
										id="event-title"
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
									<label
										class="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-1.5 ml-1"
										for="event-date">{$t('forms.date')}</label
									>
									<div class="relative">
										<div class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
											<Calendar class="w-4 h-4" />
										</div>
										<input
											id="event-date"
											type="date"
											bind:value={formData.event.date}
											class="w-full pl-9 pr-3 py-3 bg-gray-50 dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-red-500 outline-none text-sm font-medium text-gray-900 dark:text-gray-100"
										/>
									</div>
								</div>
								<div>
									<label
										class="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-1.5 ml-1"
										for="event-time">{$t('forms.showTime')}</label
									>
									<div class="relative">
										<div class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
											<Clock class="w-4 h-4" />
										</div>
										<input
											id="event-time"
											type="time"
											bind:value={formData.event.time}
											class="w-full pl-9 pr-3 py-3 bg-gray-50 dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-red-500 outline-none text-sm font-medium text-gray-900 dark:text-gray-100"
										/>
									</div>
								</div>
							</div>
						</div>

						<!-- Seat & Payment -->
						<div class="space-y-4 pt-4 border-t border-gray-100 dark:border-zinc-700">
							<h3
								class="text-xs font-black text-gray-400 dark:text-gray-500 uppercase tracking-widest mb-4 flex items-center gap-2"
							>
								<MapPin class="w-4 h-4" />
								{$t('forms.seatPayment')}
							</h3>
							<div class="grid grid-cols-3 gap-4">
								<div>
									<label
										class="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-1.5 ml-1"
										for="seat-section">{$t('forms.row')}</label
									>
									<div class="relative">
										<select
											id="seat-section"
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
									<label
										class="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-1.5 ml-1"
										for="seat-number">{$t('forms.seatNumber')}</label
									>
									<input
										id="seat-number"
										type="number"
										bind:value={formData.seat.number}
										class="w-full p-3 bg-gray-50 dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-red-500 outline-none text-center font-black text-lg text-gray-900 dark:text-gray-100 placeholder-gray-300 dark:placeholder-gray-600"
									/>
								</div>
							</div>
							<div class="grid grid-cols-2 gap-4">
								<div>
									<label
										class="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-1.5 ml-1"
										for="ticket-price">{$t('forms.price')}</label
									>
									<div class="relative">
										<div class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
											<DollarSign class="w-4 h-4" />
										</div>
										<input
											id="ticket-price"
											type="number"
											bind:value={formData.price}
											class="w-full pl-9 pr-3 py-3 bg-gray-50 dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-red-500 outline-none font-medium text-gray-900 dark:text-gray-100"
										/>
									</div>
								</div>
								<div>
									<label
										class="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-1.5 ml-1"
										for="ticket-id">{$t('forms.ticketId')}</label
									>
									<div class="relative">
										<div class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
											<Hash class="w-4 h-4" />
										</div>
										<input
											id="ticket-id"
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
						<div class="space-y-4 pt-4 border-t border-gray-100 dark:border-zinc-700">
							<div class="flex items-center justify-between mb-4">
								<h3
									class="text-xs font-black text-gray-400 dark:text-gray-500 uppercase tracking-widest flex items-center gap-2"
								>
									<Camera class="w-4 h-4" />
									{$t('forms.twoShotDetails')}
								</h3>
								<button
									type="button"
									on:click={() => (showTwoShot = !showTwoShot)}
									class={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 cursor-pointer ${showTwoShot ? 'bg-red-600' : 'bg-gray-200'}`}
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
										<label
											class="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-2 ml-1"
											for="twoshot-upload">{$t('forms.twoShotPhoto')}</label
										>
										<button
											id="twoshot-upload"
											type="button"
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
										</button>
									</div>

									<div>
										<label
											class="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-1.5 ml-1"
											for="member-selector">{$t('forms.memberName')}</label
										>
										<div id="member-selector">
											<MemberSelector
												bind:value={formData.two_shot.member_name}
												placeholder={$t('forms.memberNamePlaceholder')}
												title={$t('forms.selectMember')}
												subtitle={$t('forms.selectMemberDesc')}
											/>
										</div>
									</div>

									<div class="grid grid-cols-2 gap-4">
										<div>
											<label
												class="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-1.5 ml-1"
												for="twoshot-type">{$t('forms.type')}</label
											>
											<div class="relative">
												<div class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
													<Sparkles class="w-4 h-4" />
												</div>
												<select
													id="twoshot-type"
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
												for="twoshot-price">{$t('forms.price')}</label
											>
											<div class="relative">
												<div class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
													<DollarSign class="w-4 h-4" />
												</div>
												<input
													id="twoshot-price"
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

						<div class="pt-4">
							<button
								type="submit"
								disabled={isSubmitting || !isFormValid}
								class="w-full idol-gradient text-white py-4 rounded-2xl font-bold text-lg shadow-lg shadow-red-200 hover:shadow-xl hover:scale-[1.01] transition-all flex items-center justify-center gap-2 disabled:opacity-50 cursor-pointer disabled:cursor-not-allowed disabled:shadow-none disabled:transform-none"
							>
								{#if isSubmitting}
									<LoaderCircle class="w-6 h-6 animate-spin" />
								{:else}
									<CircleCheck class="w-6 h-6" />
								{/if}
								{$t('forms.updateTicket')}
							</button>
						</div>
					</form>
				</div>
			</div>
		</div>
	</div>
</div>

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

<!-- Validation Alert Modal -->
<ValidationAlertModal
	show={showValidationAlert}
	title={$t('validation.alert.title')}
	message={validationAlertMessage}
	onClose={() => (showValidationAlert = false)}
/>
