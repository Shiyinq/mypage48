<script lang="ts">
	import { Check, X } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	interface Props {
		password?: string;
	}

	let { password = '' }: Props = $props();

	const { t } = useTranslation();

	let requirements = $derived([
		{
			label: 'Min. 8 characters',
			valid: password.length >= 8
		},
		{
			label: 'Max. 64 characters',
			valid: password.length <= 64 && password.length > 0
		},
		{
			label: 'One uppercase letter',
			valid: /[A-Z]/.test(password)
		},
		{
			label: 'One lowercase letter',
			valid: /[a-z]/.test(password)
		},
		{
			label: 'One number',
			valid: /[0-9]/.test(password)
		},
		{
			label: 'One symbol',
			valid: /[^A-Za-z0-9]/.test(password)
		},
		{
			label: 'No spaces',
			valid: !/\s/.test(password) && password.length > 0
		}
	]);
</script>

<div
	class="grid grid-cols-2 gap-x-2 gap-y-0.5 mt-2 p-2 bg-gray-50 dark:bg-zinc-800/30 rounded-lg border border-gray-100 dark:border-zinc-800"
>
	{#each requirements as req}
		<div
			class="flex items-center gap-2 text-xs transition-colors duration-200"
			class:text-green-600={req.valid}
			class:dark:text-green-400={req.valid}
			class:text-gray-400={!req.valid && password.length === 0}
			class:text-red-500={!req.valid && password.length > 0}
		>
			{#if req.valid}
				<div class="p-0.5 rounded-full bg-green-100 dark:bg-green-900/30">
					<Check class="w-3 h-3" />
				</div>
			{:else if password.length > 0}
				<div class="p-0.5 rounded-full bg-red-100 dark:bg-red-900/30">
					<X class="w-3 h-3" />
				</div>
			{:else}
				<div class="w-4 h-4 flex items-center justify-center">
					<div class="w-1 h-1 rounded-full bg-gray-300 dark:bg-zinc-600"></div>
				</div>
			{/if}
			<span class="font-medium">{req.label}</span>
		</div>
	{/each}
</div>
