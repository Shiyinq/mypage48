<script lang="ts">
	import { Camera, ChevronDown, DollarSign, Sparkles } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import MemberSelector from '$lib/components/MemberSelector.svelte';
	import { ImageOverlayActions } from '$lib/components/common';

	import { dragDrop } from '$lib/actions/dragDrop';

	interface Props {
		showTwoShot?: boolean;
		twoShotImage?: string | null;
		memberName?: string;
		twoShotType?: 'Roulette' | 'Birthday';
		twoShotPrice?: number;
		onphotoClick?: () => void;
		onSelectImage?: () => void;
		onEdit?: () => void;
		onDelete?: () => void;
		ondrop?: (file: File) => void;
	}

	let {
		showTwoShot = $bindable(false),
		twoShotImage = null,
		memberName = $bindable(''),
		twoShotType = $bindable('Roulette'),
		twoShotPrice = $bindable(100000),
		onphotoClick,
		onSelectImage,
		onEdit,
		onDelete,
		ondrop
	}: Props = $props();

	const { t } = useTranslation();

	let isDragging = $state(false);
</script>

<div class="space-y-4">
	<div
		class="flex items-center justify-between pt-4 border-t border-gray-100 dark:border-zinc-700 mb-4"
	>
		<h3
			class="text-xs font-black text-gray-400 dark:text-gray-500 uppercase tracking-widest flex items-center gap-2"
		>
			<Camera class="w-4 h-4" />
			{t('forms.twoShotDetails')}
		</h3>
		<button
			type="button"
			aria-label="Toggle two shot section"
			onclick={() => (showTwoShot = !showTwoShot)}
			class={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 cursor-pointer ${showTwoShot ? 'bg-red-600' : 'bg-gray-200 dark:bg-zinc-700'}`}
		>
			<span
				class={`inline-block h-4 w-4 transform rounded-full bg-white transition duration-200 ease-in-out ${showTwoShot ? 'translate-x-6' : 'translate-x-1'}`}
			></span>
		</button>
	</div>
	{#if showTwoShot}
		<div
			class="bg-red-50/50 dark:bg-zinc-800/50 rounded-2xl p-4 border border-red-100 dark:border-red-500/30 space-y-4 animate-fade-in"
		>
			<div>
				<label
					for="two-shot-photo"
					class="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-2 ml-1"
					>{t('forms.twoShotPhoto')}</label
				>
				<div
					id="two-shot-photo"
					use:dragDrop={{
						onDrop: (file) => ondrop?.(file),
						onDragChange: (state) => (isDragging = state)
					}}
					class="w-full h-32 border-2 border-dashed rounded-xl transition-all flex items-center justify-center overflow-hidden relative group
					{isDragging
						? 'border-red-500 bg-red-50 dark:bg-red-900/10 scale-[1.02] ring-4 ring-red-500/20'
						: 'border-red-200 dark:border-red-900/30 bg-white dark:bg-zinc-900 hover:bg-red-50 dark:hover:bg-red-900/10'}"
				>
					{#if twoShotImage}
						<img src={twoShotImage} alt="2shot" class="w-full h-full object-contain" />
						<ImageOverlayActions
							onSelect={() => {
								onphotoClick?.();
								onSelectImage?.();
							}}
							{onEdit}
							{onDelete}
							variant="twoshot"
						/>
					{:else}
						<button
							type="button"
							onclick={() => {
								onphotoClick?.();
								onSelectImage?.();
							}}
							class="w-full h-full flex flex-col items-center justify-center cursor-pointer {isDragging
								? 'text-red-500'
								: 'text-red-400 dark:text-red-500'}"
						>
							<Camera class="w-6 h-6 mb-1" />
							<span class="text-xs font-medium">{t('forms.uploadPhoto')}</span>
							<span class="text-[10px] mt-0.5 opacity-70">({t('forms.optional')})</span>
						</button>
					{/if}
				</div>
			</div>

			<div>
				<label
					class="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-1.5 ml-1"
					for="member-selector">{t('forms.memberName')}</label
				>
				<div id="member-selector">
					<MemberSelector
						bind:value={memberName}
						placeholder={t('forms.memberNamePlaceholder')}
						title={t('forms.selectMember')}
						subtitle={t('forms.selectMemberDesc')}
					/>
				</div>
			</div>

			<div class="grid grid-cols-2 gap-4">
				<div>
					<label
						class="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-1.5 ml-1"
						for="twoshot-type">{t('forms.type')}</label
					>
					<div class="relative">
						<div class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
							<Sparkles class="w-4 h-4" />
						</div>
						<select
							id="twoshot-type"
							bind:value={twoShotType}
							onchange={(e) => {
								twoShotPrice = e.currentTarget.value === 'Birthday' ? 250000 : 100000;
							}}
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
						for="twoshot-price">{t('forms.price')}</label
					>
					<div class="relative">
						<div class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
							<DollarSign class="w-4 h-4" />
						</div>
						<input
							id="twoshot-price"
							type="number"
							bind:value={twoShotPrice}
							class="w-full pl-9 pr-3 py-3 bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-red-500 outline-none text-sm font-medium text-gray-900 dark:text-gray-100"
						/>
					</div>
				</div>
			</div>
		</div>
	{/if}
</div>
