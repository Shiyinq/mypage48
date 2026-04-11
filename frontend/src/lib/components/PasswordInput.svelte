<script lang="ts">
	import { Eye, EyeOff } from 'lucide-svelte';
	import { createEventDispatcher } from 'svelte';

	export let value = '';
	export let id: string;
	export let name: string;
	export let label: string;
	export let placeholder = '••••••••';
	export let error: string | undefined = undefined;
	export let disabled = false;

	let visible = false;
	const dispatch = createEventDispatcher();

	function toggleVisibility() {
		visible = !visible;
	}

	function handleInput(e: Event) {
		const target = e.target as HTMLInputElement;
		value = target.value;
		dispatch('input', e);
	}
</script>

<div>
	<label for={id} class="block text-sm font-bold text-gray-500 dark:text-gray-400 mb-1.5">
		{label}
	</label>
	<div class="relative">
		<!-- Leading Icon Slot -->
		{#if $$slots.leading}
			<div class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 dark:text-zinc-500">
				<slot name="leading" />
			</div>
		{/if}

		<input
			type={visible ? 'text' : 'password'}
			{id}
			{name}
			{value}
			{placeholder}
			{disabled}
			on:input={handleInput}
			on:blur
			class={`w-full pl-12 pr-12 py-3.5 bg-white/80 dark:bg-zinc-800/50 border rounded-xl focus:ring-2 focus:ring-red-500 outline-none font-medium text-gray-900 dark:text-white transition-all placeholder-gray-400 dark:placeholder-zinc-600 ${
				error ? 'border-red-500' : 'border-gray-200 dark:border-zinc-700'
			} ${disabled ? 'opacity-70 cursor-not-allowed' : ''}`}
		/>

		<!-- Visibility Toggle -->
		<button
			type="button"
			class="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 dark:text-zinc-500 hover:text-gray-600 dark:hover:text-zinc-300 transition-colors focus:outline-none cursor-pointer"
			on:click={toggleVisibility}
			tabindex="-1"
			aria-label={visible ? 'Hide password' : 'Show password'}
		>
			{#if visible}
				<EyeOff class="w-5 h-5" />
			{:else}
				<Eye class="w-5 h-5" />
			{/if}
		</button>
	</div>
	{#if error}
		<p class="text-xs text-red-500 mt-1 ml-1 font-medium">{error}</p>
	{/if}
</div>
