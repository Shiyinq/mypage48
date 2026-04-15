<script lang="ts">
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import Input from '$lib/components/Input.svelte';
	import Button from '$lib/components/Button.svelte';
	import { MessageSquare, Send, Loader2 } from 'lucide-svelte';
	import { showToast } from '$lib/stores';
	import { userProfile, isAuthenticated } from '$lib/stores';
	import { onMount } from 'svelte';
	import { feedbackStore, isFeedbackLoading } from '$lib/stores/feedback.svelte';
	import { goto } from '$app/navigation';
	import { PageHeader } from '$lib/components';

	const { t } = useTranslation();

	let type: 'issue' | 'suggestion' | 'other' = $state('issue');
	let message = $state('');
	let email = $state('');
	let name = $state('');
	let isInitialized = $state(false);

	onMount(() => {
		if (!isAuthenticated.value) {
			goto('/login');
			return;
		}

		if (userProfile.data && !isInitialized) {
			email = userProfile.data.email || '';
			name = userProfile.data.name || '';
			isInitialized = true;
		}
	});

	// Reactively update only if fields are empty and data becomes available (e.g. initial load latency)
	$effect(() => {
		if ($userProfile?.data && !isInitialized) {
			email = $userProfile.data.email || '';
			name = $userProfile.data.name || '';
			isInitialized = true;
		}
	});

	const handleSubmit = async () => {
		if (message.length < 10) {
			showToast(t('feedback.validation.messageTooShort'), 'error');
			return;
		}

		// loading is handled by store but we check it here to prevent double submit locally
		if ($isFeedbackLoading) return;

		try {
			await feedbackStore.submit({
				type,
				message,
				email: email || undefined,
				name: name || undefined
			});

			showToast(t('feedback.success'), 'success');
			// Reset form
			message = '';
			// Don't reset name/email for logged in user convenience
			// email = '';
			// name = '';
			const issueType = 'issue';
			type = issueType;
		} catch (error) {
			console.error(error);
			showToast(t('feedback.error'), 'error');
		}
	};
</script>

<SEO title={t('feedback.title')} />

<div class="max-w-2xl mx-auto p-4 animate-fade-in pb-24">
	<!-- Page Header -->
	<div class="mb-8">
		<PageHeader
			title={t('feedback.title')}
			subtitle={t('feedback.subtitle')}
			icon={MessageSquare}
			theme="red"
		/>
	</div>

	<!-- Form -->
	<div
		class="bg-white dark:bg-zinc-900 rounded-[2.5rem] p-8 md:p-10 shadow-sm border border-slate-100 dark:border-zinc-800"
	>
		<form
			onsubmit={(e) => {
				e.preventDefault();
				handleSubmit();
			}}
			class="space-y-6"
		>
			<!-- Type -->
			<div class="space-y-2">
				<label
					class="text-sm font-bold text-slate-900 dark:text-white ml-1 block"
					for="feedback-type"
				>
					{t('feedback.form.type.label')}
				</label>
				<div class="grid grid-cols-3 gap-3">
					<button
						type="button"
						class="px-4 py-3 rounded-2xl text-sm font-bold transition-all border {type === 'issue'
							? 'bg-red-50 text-red-600 border-red-200 dark:bg-red-900/20 dark:text-red-400 dark:border-red-900/50'
							: 'bg-slate-50 text-slate-600 border-transparent hover:bg-slate-100 dark:bg-zinc-800/50 dark:text-slate-400 dark:hover:bg-zinc-800'}"
						onclick={() => (type = 'issue')}
						style="cursor: pointer;"
					>
						{t('feedback.form.type.issue')}
					</button>
					<button
						type="button"
						class="px-4 py-3 rounded-2xl text-sm font-bold transition-all border {type ===
						'suggestion'
							? 'bg-blue-50 text-blue-600 border-blue-200 dark:bg-blue-900/20 dark:text-blue-400 dark:border-blue-900/50'
							: 'bg-slate-50 text-slate-600 border-transparent hover:bg-slate-100 dark:bg-zinc-800/50 dark:text-slate-400 dark:hover:bg-zinc-800'}"
						onclick={() => (type = 'suggestion')}
						style="cursor: pointer;"
					>
						{t('feedback.form.type.suggestion')}
					</button>
					<button
						type="button"
						class="px-4 py-3 rounded-2xl text-sm font-bold transition-all border {type === 'other'
							? 'bg-amber-50 text-amber-600 border-amber-200 dark:bg-amber-900/20 dark:text-amber-400 dark:border-amber-900/50'
							: 'bg-slate-50 text-slate-600 border-transparent hover:bg-slate-100 dark:bg-zinc-800/50 dark:text-slate-400 dark:hover:bg-zinc-800'}"
						onclick={() => (type = 'other')}
						style="cursor: pointer;"
					>
						{t('feedback.form.type.other')}
					</button>
				</div>
			</div>

			<!-- Message -->
			<div class="space-y-2">
				<label class="text-sm font-bold text-slate-900 dark:text-white ml-1 block" for="message">
					{t('feedback.form.message.label')}
				</label>
				<textarea
					id="message"
					bind:value={message}
					rows="5"
					class="w-full px-4 py-3 rounded-2xl bg-slate-50 dark:bg-zinc-800/50 border-2 border-transparent focus:border-red-500 focus:bg-white dark:focus:bg-zinc-900 focus:ring-0 transition-all outline-none text-slate-900 dark:text-white placeholder:text-slate-400 resize-none font-medium"
					placeholder={t('feedback.form.message.placeholder')}
					required
				></textarea>
			</div>

			<!-- Contact Info (Optional) -->
			<div class="grid md:grid-cols-2 gap-6 pt-4 border-t border-slate-100 dark:border-zinc-800">
				<Input
					label={t('feedback.form.name.label')}
					bind:value={name}
					placeholder={t('feedback.form.name.placeholder')}
				/>
				<Input
					label={t('feedback.form.email.label')}
					type="email"
					bind:value={email}
					placeholder={t('feedback.form.email.placeholder')}
				/>
			</div>

			<!-- Submit -->
			<div class="pt-4">
				<Button
					type="submit"
					variant="primary"
					full
					disabled={$isFeedbackLoading || message.length < 10}
				>
					{#if $isFeedbackLoading}
						<Loader2 class="w-5 h-5 animate-spin mr-2" />
						{t('common.loading')}
					{:else}
						<Send class="w-5 h-5 mr-2" />
						{t('common.submit')}
					{/if}
				</Button>
			</div>
		</form>
	</div>
</div>
