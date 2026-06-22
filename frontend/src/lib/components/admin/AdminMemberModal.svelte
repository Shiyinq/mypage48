<script lang="ts">
	import { X, User, LoaderCircle, CircleCheck, Sparkles, ChevronDown } from 'lucide-svelte';
	import type { Member } from '$lib/apis/members';
	import { fade } from 'svelte/transition';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { storageStore } from '$lib/stores';
	import AdminImageUpload from './AdminImageUpload.svelte';
	import { cleanseStorageUrl } from '$lib/utils/markdown';
	import { getErrorMessage } from '$lib/utils/api';
	import { showToast } from '$lib/stores';
	import { logger } from '$lib/utils/logger';

	interface Props {
		show?: boolean;
		member?: Partial<Member>;
		isCreating?: boolean;
		isSubmitting?: boolean;
		onsubmit?: (data: Partial<Member>) => Promise<void> | void;
	}

	let {
		show = $bindable(false),
		member = {},
		isCreating = false,
		isSubmitting = false,
		onsubmit
	}: Props = $props();

	const { t } = useTranslation();

	let localLoading = $state(false);
	let formData = $state({
		name: '',
		nickname: '',
		generation: '',
		jiko: '',
		img: '',
		blurHash: '' as string | undefined,
		active: true,
		member_type: 'DREAM',
		birthdate: '',
		bloodType: '',
		height: '',
		horoscope: '',
		socials: {
			twitter: '',
			instagram: '',
			tiktok: '',
			threads: '',
			showroom: '',
			idn_app: ''
		}
	});

	// Safe Form Reset Pattern
	let prevShow = $state(false);
	$effect(() => {
		if (show !== prevShow) {
			if (show) {
				// Modal opened - reset form
				formData = {
					name: member.name || '',
					nickname: member.nickname || '',
					generation: member.generation || '',
					jiko: member.jiko || '',
					img: member.img || '',
					blurHash: member.blurHash,
					active: member.active ?? true,
					member_type: member.member_type || 'DREAM',
					birthdate: parseIndoDateToISO(member.birthdate || ''),
					bloodType: member.bloodType || '',
					height: member.height ? member.height.replace('cm', '') : '',
					horoscope: member.horoscope || '',
					socials: {
						twitter: member.socials?.twitter || '',
						instagram: member.socials?.instagram || '',
						tiktok: member.socials?.tiktok || '',
						threads: member.socials?.threads || '',
						showroom: member.socials?.showroom || '',
						idn_app: member.socials?.idn_app || ''
					}
				};
			}
			prevShow = show;
		}
	});

	// Realtime Validation
	let isNameValid = $derived(formData.name.length > 0);
	let isNicknameValid = $derived(formData.nickname.length > 0);
	let isGenValid = $derived(formData.generation.length > 0);
	let isFormValid = $derived(isNameValid && isNicknameValid && isGenValid);

	function generateSlug(name: string): string {
		return name.toLowerCase().trim().replace(/\s+/g, '_');
	}

	const monthsMapIndo = [
		'Januari',
		'Februari',
		'Maret',
		'April',
		'Mei',
		'Juni',
		'Juli',
		'Agustus',
		'September',
		'Oktober',
		'November',
		'Desember'
	];

	function formatDateToIndo(dateStr: string): string {
		if (!dateStr) return '';
		const date = new Date(dateStr);
		const day = date.getDate();
		const month = monthsMapIndo[date.getMonth()];
		const year = date.getFullYear();
		return `${day} ${month} ${year}`;
	}

	function parseIndoDateToISO(indoDate: string): string {
		if (!indoDate || indoDate === '-') return '';
		const parts = indoDate.split(' ');
		if (parts.length !== 3) return '';

		const day = parts[0].padStart(2, '0');
		const monthStr = parts[1];
		const year = parts[2];

		const monthIndex = monthsMapIndo.indexOf(monthStr);
		if (monthIndex === -1) return '';

		const month = (monthIndex + 1).toString().padStart(2, '0');
		return `${year}-${month}-${day}`;
	}

	async function handleSubmit() {
		if (!isFormValid || localLoading) return;
		localLoading = true;

		try {
			let finalData = { ...formData };

			// Format physical details
			if (finalData.birthdate && finalData.birthdate.includes('-')) {
				finalData.birthdate = formatDateToIndo(finalData.birthdate);
			}

			if (finalData.height) {
				const heightStr = String(finalData.height);
				if (!heightStr.endsWith('cm')) {
					finalData.height = `${heightStr}cm`;
				}
			}

			if (formData.img && formData.img.startsWith('data:image/')) {
				try {
					const uploadResult = await storageStore.uploadImage(
						formData.img,
						'member',
						generateSlug(formData.name)
					);
					finalData.img = cleanseStorageUrl(uploadResult.filename);
					finalData.blurHash = uploadResult.blurHash;
				} catch (error) {
					logger.error('Failed to upload member image:', error);
					const errorMessage = getErrorMessage(error);
					showToast(errorMessage || 'Failed to upload image', 'error');
					localLoading = false;
					return;
				}
			} else if (finalData.img) {
				// Cleanse existing URL to remove domain/proxy part before sending to API
				finalData.img = cleanseStorageUrl(finalData.img);
			}

			await onsubmit?.(finalData);
		} finally {
			localLoading = false;
		}
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
							class="p-3 rounded-2xl bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 shadow-lg shadow-red-100 dark:shadow-red-900/20 border-2 border-white dark:border-zinc-700 transform -rotate-6"
						>
							<User class="w-6 h-6" />
						</div>
						<div>
							<h2
								class="text-2xl font-bold text-gray-900 dark:text-white leading-none relative w-fit"
							>
								{isCreating
									? t('admin.members.modal.addTitle')
									: t('admin.members.modal.editTitle')}
								<span
									class="absolute -bottom-1 left-0 w-full h-2 bg-red-200/60 dark:bg-red-500/30 -z-10 transform -skew-x-12 rounded-sm"
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

				<form
					onsubmit={(e) => {
						e.preventDefault();
						handleSubmit();
					}}
					class="space-y-6"
				>
					<!-- Basic Info -->
					<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
						<div class="space-y-6">
							<div class="space-y-2">
								<label
									for="member-name"
									class="text-sm font-bold text-gray-700 dark:text-gray-300 ml-1"
									>{t('admin.members.modal.name')}</label
								>
								<input
									id="member-name"
									name="name"
									type="text"
									autocomplete="off"
									bind:value={formData.name}
									placeholder="e.g. Feni Fitriyanti"
									class="w-full px-4 py-3 bg-gray-50 dark:bg-zinc-800/50 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-transparent outline-none transition-all"
								/>
								{#if !isNameValid && formData.name.length > 0}
									<p class="text-xs text-red-500 ml-1">{t('admin.members.modal.nameRequired')}</p>
								{/if}
							</div>

							<div class="space-y-2">
								<label
									for="member-nickname"
									class="text-sm font-bold text-gray-700 dark:text-gray-300 ml-1"
									>{t('admin.members.modal.nickname')}</label
								>
								<input
									id="member-nickname"
									name="nickname"
									type="text"
									autocomplete="off"
									bind:value={formData.nickname}
									placeholder="e.g. Feni"
									class="w-full px-4 py-3 bg-gray-50 dark:bg-zinc-800/50 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-transparent outline-none transition-all"
								/>
							</div>

							<div class="space-y-2">
								<label
									for="member-gen"
									class="text-sm font-bold text-gray-700 dark:text-gray-300 ml-1"
									>{t('admin.members.modal.generation')}</label
								>
								<div class="relative">
									<select
										id="member-gen"
										name="generation"
										bind:value={formData.generation}
										class="w-full px-4 pr-10 py-3 bg-gray-50 dark:bg-zinc-800/50 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-transparent outline-none transition-all cursor-pointer appearance-none"
									>
										<option value="">{t('admin.members.modal.selectPlaceholder')}</option>
										{#each Array.from({ length: 20 }, (_, i) => i + 1) as gen}
											<option value={gen.toString()}>Gen {gen}</option>
										{/each}
									</select>
									<ChevronDown
										class="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 pointer-events-none"
									/>
								</div>
							</div>

							<div class="space-y-2">
								<label
									for="member-type"
									class="text-sm font-bold text-gray-700 dark:text-gray-300 ml-1"
									>{t('admin.members.modal.memberType')}</label
								>
								<div class="relative">
									<select
										id="member-type"
										name="member_type"
										bind:value={formData.member_type}
										class="w-full px-4 pr-10 py-3 bg-gray-50 dark:bg-zinc-800/50 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-transparent outline-none transition-all cursor-pointer appearance-none"
									>
										<option value="DREAM">DREAM</option>
										<option value="PASSION">PASSION</option>
										<option value="LOVE">LOVE</option>
										<option value="TRAINEE">TRAINEE</option>
										<option value="JKT48_VIRTUAL">JKT48 VIRTUAL</option>
									</select>
									<ChevronDown
										class="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 pointer-events-none"
									/>
								</div>
							</div>
						</div>

						<AdminImageUpload
							image={formData.img}
							label={t('admin.members.modal.imageUrl')}
							onSelect={(base64) => (formData.img = base64)}
						/>
					</div>

					<!-- Physical Details -->
					<div
						class="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-gray-100 dark:border-zinc-800"
					>
						<div class="space-y-2">
							<label
								for="member-birthdate"
								class="text-sm font-bold text-gray-700 dark:text-gray-300 ml-1"
								>{t('admin.members.modal.birthdate')}</label
							>
							<input
								id="member-birthdate"
								name="birthdate"
								type="date"
								bind:value={formData.birthdate}
								class="w-full px-4 py-2 bg-gray-50 dark:bg-zinc-800/50 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-2 focus:ring-red-500 outline-none transition-all text-sm cursor-pointer"
							/>
						</div>
						<div class="space-y-2">
							<label
								for="member-blood"
								class="text-sm font-bold text-gray-700 dark:text-gray-300 ml-1"
								>{t('admin.members.modal.bloodType')}</label
							>
							<div class="relative">
								<select
									id="member-blood"
									name="bloodType"
									bind:value={formData.bloodType}
									class="w-full px-4 pr-10 py-2 bg-gray-50 dark:bg-zinc-800/50 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-2 focus:ring-red-500 outline-none transition-all text-sm cursor-pointer appearance-none"
								>
									<option value="">{t('admin.members.modal.selectPlaceholder')}</option>
									<option value="A">A</option>
									<option value="B">B</option>
									<option value="AB">AB</option>
									<option value="O">O</option>
								</select>
								<ChevronDown
									class="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none"
								/>
							</div>
						</div>
						<div class="space-y-2">
							<label
								for="member-height"
								class="text-sm font-bold text-gray-700 dark:text-gray-300 ml-1"
								>{t('admin.members.modal.height')}</label
							>
							<div class="relative">
								<input
									id="member-height"
									name="height"
									type="number"
									min="0"
									bind:value={formData.height}
									placeholder="e.g. 162"
									class="w-full px-4 py-2 bg-gray-50 dark:bg-zinc-800/50 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-2 focus:ring-red-500 outline-none transition-all text-sm"
								/>
								<span
									class="absolute right-4 top-1/2 -translate-y-1/2 text-sm text-gray-400 pointer-events-none"
									>cm</span
								>
							</div>
						</div>
						<div class="space-y-2">
							<label
								for="member-horoscope"
								class="text-sm font-bold text-gray-700 dark:text-gray-300 ml-1"
								>{t('admin.members.modal.horoscope')}</label
							>
							<div class="relative">
								<select
									id="member-horoscope"
									name="horoscope"
									bind:value={formData.horoscope}
									class="w-full px-4 pr-10 py-2 bg-gray-50 dark:bg-zinc-800/50 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-2 focus:ring-red-500 outline-none transition-all text-sm cursor-pointer appearance-none"
								>
									<option value="">{t('admin.members.modal.selectPlaceholder')}</option>
									<option value="Aries">Aries</option>
									<option value="Taurus">Taurus</option>
									<option value="Gemini">Gemini</option>
									<option value="Cancer">Cancer</option>
									<option value="Leo">Leo</option>
									<option value="Virgo">Virgo</option>
									<option value="Libra">Libra</option>
									<option value="Scorpio">Scorpio</option>
									<option value="Sagittarius">Sagittarius</option>
									<option value="Capricorn">Capricorn</option>
									<option value="Aquarius">Aquarius</option>
									<option value="Pisces">Pisces</option>
								</select>
								<ChevronDown
									class="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none"
								/>
							</div>
						</div>
					</div>

					<!-- Jikoshoukai -->
					<div class="space-y-2">
						<label for="member-jiko" class="text-sm font-bold text-gray-700 dark:text-gray-300 ml-1"
							>{t('admin.members.modal.jikoshoukai')}</label
						>
						<div class="relative">
							<textarea
								id="member-jiko"
								name="jiko"
								bind:value={formData.jiko}
								placeholder="Enter catchphrase..."
								class="w-full px-4 py-3 bg-yellow-50/50 dark:bg-zinc-800/50 border border-yellow-200 dark:border-zinc-700 rounded-xl focus:ring-2 focus:ring-yellow-400 outline-none transition-all min-h-[100px] text-sm"
							></textarea>
							<Sparkles
								class="absolute top-3 right-3 w-4 h-4 text-yellow-500/50 pointer-events-none"
							/>
						</div>
					</div>

					<!-- Socials -->
					<div class="space-y-4 pt-4 border-t border-gray-100 dark:border-zinc-800">
						<h3 class="text-sm font-bold text-gray-900 dark:text-white flex items-center gap-2">
							{t('admin.members.modal.socials')}
						</h3>
						<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
							<div class="space-y-1">
								<label for="social-twitter" class="text-xs font-semibold text-gray-500 ml-1"
									>Twitter (X)</label
								>
								<input
									id="social-twitter"
									name="socials_twitter"
									type="text"
									bind:value={formData.socials.twitter}
									placeholder="URL"
									class="w-full px-3 py-2 bg-gray-50 dark:bg-zinc-800/50 border border-gray-200 dark:border-zinc-700 rounded-lg text-sm focus:ring-2 focus:ring-blue-400 outline-none"
								/>
							</div>
							<div class="space-y-1">
								<label for="social-instagram" class="text-xs font-semibold text-gray-500 ml-1"
									>Instagram</label
								>
								<input
									id="social-instagram"
									name="socials_instagram"
									type="text"
									bind:value={formData.socials.instagram}
									placeholder="URL"
									class="w-full px-3 py-2 bg-gray-50 dark:bg-zinc-800/50 border border-gray-200 dark:border-zinc-700 rounded-lg text-sm focus:ring-2 focus:ring-pink-500 outline-none"
								/>
							</div>
							<div class="space-y-1">
								<label for="social-tiktok" class="text-xs font-semibold text-gray-500 ml-1"
									>TikTok</label
								>
								<input
									id="social-tiktok"
									name="socials_tiktok"
									type="text"
									bind:value={formData.socials.tiktok}
									placeholder="URL"
									class="w-full px-3 py-2 bg-gray-50 dark:bg-zinc-800/50 border border-gray-200 dark:border-zinc-700 rounded-lg text-sm focus:ring-2 focus:ring-black dark:focus:ring-white outline-none"
								/>
							</div>
							<div class="space-y-1">
								<label for="social-threads" class="text-xs font-semibold text-gray-500 ml-1"
									>Threads</label
								>
								<input
									id="social-threads"
									name="socials_threads"
									type="text"
									bind:value={formData.socials.threads}
									placeholder="URL"
									class="w-full px-3 py-2 bg-gray-50 dark:bg-zinc-800/50 border border-gray-200 dark:border-zinc-700 rounded-lg text-sm focus:ring-2 focus:ring-black dark:focus:ring-white outline-none"
								/>
							</div>
							<div class="space-y-1">
								<label for="social-showroom" class="text-xs font-semibold text-gray-500 ml-1"
									>Showroom</label
								>
								<input
									id="social-showroom"
									name="socials_showroom"
									type="text"
									bind:value={formData.socials.showroom}
									placeholder="URL"
									class="w-full px-3 py-2 bg-gray-50 dark:bg-zinc-800/50 border border-gray-200 dark:border-zinc-700 rounded-lg text-sm focus:ring-2 focus:ring-blue-400 outline-none"
								/>
							</div>
							<div class="space-y-1">
								<label for="social-idn" class="text-xs font-semibold text-gray-500 ml-1"
									>IDN App</label
								>
								<input
									id="social-idn"
									name="socials_idn_app"
									type="text"
									bind:value={formData.socials.idn_app}
									placeholder="URL"
									class="w-full px-3 py-2 bg-gray-50 dark:bg-zinc-800/50 border border-gray-200 dark:border-zinc-700 rounded-lg text-sm focus:ring-2 focus:ring-red-500 outline-none"
								/>
							</div>
						</div>
					</div>

					<!-- Active Status -->
					<div class="flex items-center gap-3 pt-2">
						<button
							type="button"
							aria-label="Toggle active status"
							class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 {formData.active
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
							{t('admin.members.modal.accountStatus')}: {formData.active
								? t('admin.members.modal.active')
								: t('admin.members.modal.inactive')}
						</span>
					</div>

					<!-- Actions -->
					<div class="pt-6 flex gap-3">
						<button
							type="button"
							onclick={handleClose}
							class="flex-1 px-4 py-3 rounded-xl font-bold text-gray-600 dark:text-gray-300 bg-gray-100 dark:bg-zinc-800 hover:bg-gray-200 dark:hover:bg-zinc-700 transition-colors cursor-pointer"
						>
							{t('common.cancel')}
						</button>
						<button
							type="submit"
							disabled={!isFormValid || isSubmitting || localLoading}
							class="flex-[2] px-4 py-3 rounded-xl font-bold text-white bg-gradient-to-r from-red-600 to-red-500 hover:from-red-500 hover:to-red-400 shadow-lg shadow-red-500/30 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-all cursor-pointer"
						>
							{#if isSubmitting || localLoading}
								<LoaderCircle class="w-5 h-5 animate-spin" />
								{t('admin.members.modal.saving')}
							{:else}
								<CircleCheck class="w-5 h-5" />
								{isCreating ? t('admin.members.modal.create') : t('admin.members.modal.save')}
							{/if}
						</button>
					</div>
				</form>
			</div>
		</div>
	</div>
{/if}
