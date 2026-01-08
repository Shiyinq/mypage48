<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { X, Save, User, LoaderCircle, CircleCheck, Sparkles } from 'lucide-svelte';
	import type { Member } from '$lib/apis/members';
	import { fly, fade } from 'svelte/transition';
	import { useTranslation } from '$lib/i18n/useTranslation';

	export let show = false;
	export let member: Partial<Member> = {};
	export let isCreating = false;
	export let isSubmitting = false;

	const dispatch = createEventDispatcher();
	const { t } = useTranslation();

	let formData = {
		name: member.name || '',
		nickname: member.nickname || '',
		generation: member.generation || '',
		jiko: member.jiko || '',
		img: member.img || '',
		active: member.active ?? true,
		socials: {
			twitter: member.socials?.twitter || '',
			instagram: member.socials?.instagram || '',
			tiktok: member.socials?.tiktok || '',
			threads: member.socials?.threads || '',
			showroom: member.socials?.showroom || '',
			idn_app: member.socials?.idn_app || ''
		}
	};

	// Safe Form Reset Pattern
	let prevShow = false;
	$: if (show !== prevShow) {
		if (show) {
			// Modal opened - reset form
			formData = {
				name: member.name || '',
				nickname: member.nickname || '',
				generation: member.generation || '',
				jiko: member.jiko || '',
				img: member.img || '',
				active: member.active ?? true,
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

	// Realtime Validation
	$: isNameValid = formData.name.length > 0;
	$: isNicknameValid = formData.nickname.length > 0;
	$: isGenValid = formData.generation.length > 0;
	$: isFormValid = isNameValid && isNicknameValid && isGenValid;

	function handleSubmit() {
		if (!isFormValid) return;
		dispatch('submit', formData);
	}

	function handleClose() {
		show = false;
	}
</script>

{#if show}
	<div class="fixed inset-0 z-[9999] flex items-center justify-center p-4 sm:p-6">
		<!-- Backdrop -->
		<!-- svelte-ignore a11y-click-events-have-key-events -->
		<!-- svelte-ignore a11y-no-static-element-interactions -->
		<div
			class="absolute inset-0 bg-black/80 backdrop-blur-sm transition-opacity duration-300"
			on:click={handleClose}
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
									? $t('admin.members.modal.addTitle')
									: $t('admin.members.modal.editTitle')}
								<span
									class="absolute -bottom-1 left-0 w-full h-2 bg-red-200/60 dark:bg-red-500/30 -z-10 transform -skew-x-12 rounded-sm"
								></span>
							</h2>
						</div>
					</div>

					<button
						on:click={handleClose}
						class="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-full transition-all cursor-pointer"
					>
						<X class="w-6 h-6" />
					</button>
				</div>

				<form on:submit|preventDefault={handleSubmit} class="space-y-6">
					<!-- Basic Info -->
					<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
						<div class="space-y-2">
							<label
								for="member-name"
								class="text-sm font-bold text-gray-700 dark:text-gray-300 ml-1"
								>{$t('admin.members.modal.name')}</label
							>
							<input
								id="member-name"
								type="text"
								bind:value={formData.name}
								placeholder="e.g. Feni Fitriyanti"
								class="w-full px-4 py-3 bg-gray-50 dark:bg-zinc-800/50 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-transparent outline-none transition-all"
							/>
							{#if !isNameValid && formData.name.length > 0}
								<p class="text-xs text-red-500 ml-1">{$t('admin.members.modal.nameRequired')}</p>
							{/if}
						</div>

						<div class="space-y-2">
							<label
								for="member-nickname"
								class="text-sm font-bold text-gray-700 dark:text-gray-300 ml-1"
								>{$t('admin.members.modal.nickname')}</label
							>
							<input
								id="member-nickname"
								type="text"
								bind:value={formData.nickname}
								placeholder="e.g. Feni"
								class="w-full px-4 py-3 bg-gray-50 dark:bg-zinc-800/50 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-transparent outline-none transition-all"
							/>
						</div>

						<div class="space-y-2">
							<label
								for="member-gen"
								class="text-sm font-bold text-gray-700 dark:text-gray-300 ml-1"
								>{$t('admin.members.modal.generation')}</label
							>
							<input
								id="member-gen"
								type="text"
								bind:value={formData.generation}
								placeholder="e.g. 3"
								class="w-full px-4 py-3 bg-gray-50 dark:bg-zinc-800/50 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-transparent outline-none transition-all"
							/>
						</div>

						<div class="space-y-2">
							<label
								for="member-img"
								class="text-sm font-bold text-gray-700 dark:text-gray-300 ml-1"
								>{$t('admin.members.modal.imageUrl')}</label
							>
							<input
								id="member-img"
								type="text"
								bind:value={formData.img}
								placeholder="https://..."
								class="w-full px-4 py-3 bg-gray-50 dark:bg-zinc-800/50 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-transparent outline-none transition-all"
							/>
						</div>
					</div>

					<!-- Jikoshoukai -->
					<div class="space-y-2">
						<label for="member-jiko" class="text-sm font-bold text-gray-700 dark:text-gray-300 ml-1"
							>{$t('admin.members.modal.jikoshoukai')}</label
						>
						<div class="relative">
							<textarea
								id="member-jiko"
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
							{$t('admin.members.modal.socials')}
						</h3>
						<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
							<div class="space-y-1">
								<label for="social-twitter" class="text-xs font-semibold text-gray-500 ml-1"
									>Twitter (X)</label
								>
								<input
									id="social-twitter"
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
							class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 {formData.active
								? 'bg-green-500'
								: 'bg-gray-200 dark:bg-zinc-700'}"
							on:click={() => (formData.active = !formData.active)}
						>
							<span
								class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform {formData.active
									? 'translate-x-6'
									: 'translate-x-1'}"
							/>
						</button>
						<span class="text-sm font-medium text-gray-700 dark:text-gray-300">
							{$t('admin.members.modal.accountStatus')}: {formData.active
								? $t('admin.members.modal.active')
								: $t('admin.members.modal.inactive')}
						</span>
					</div>

					<!-- Actions -->
					<div class="pt-6 flex gap-3">
						<button
							type="button"
							on:click={handleClose}
							class="flex-1 px-4 py-3 rounded-xl font-bold text-gray-600 dark:text-gray-300 bg-gray-100 dark:bg-zinc-800 hover:bg-gray-200 dark:hover:bg-zinc-700 transition-colors cursor-pointer"
						>
							{$t('common.cancel')}
						</button>
						<button
							type="submit"
							disabled={!isFormValid || isSubmitting}
							class="flex-[2] px-4 py-3 rounded-xl font-bold text-white bg-gradient-to-r from-red-600 to-red-500 hover:from-red-500 hover:to-red-400 shadow-lg shadow-red-500/30 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-all cursor-pointer"
						>
							{#if isSubmitting}
								<LoaderCircle class="w-5 h-5 animate-spin" />
								{$t('admin.members.modal.saving')}
							{:else}
								<CircleCheck class="w-5 h-5" />
								{isCreating ? $t('admin.members.modal.create') : $t('admin.members.modal.save')}
							{/if}
						</button>
					</div>
				</form>
			</div>
		</div>
	</div>
{/if}
