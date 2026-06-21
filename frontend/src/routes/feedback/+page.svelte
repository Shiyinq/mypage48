<script lang="ts">
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import Button from '$lib/components/Button.svelte';
	import { MessageSquare, Send, Loader2, AlertCircle } from 'lucide-svelte';
	import { showToast } from '$lib/stores';
	import { userProfile, isAuthenticated } from '$lib/stores';
	import { onMount } from 'svelte';
	import { feedbackStore, isFeedbackLoading } from '$lib/stores/feedback.svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { PageHeader } from '$lib/components';

	import FeedbackList from '$lib/components/feedback/FeedbackList.svelte';

	const { t } = useTranslation();

	let type: 'issue' | 'suggestion' | 'other' = $state('issue');
	let message = $state('');
	let email = $state('');
	let name = $state('');
	let isInitialized = $state(false);

	let activeTab: 'submit' | 'my_feedback' = $state('submit');

	onMount(() => {
		if (!isAuthenticated.value) {
			goto('/login');
			return;
		}

		if ($page.url.searchParams.get('tab') === 'my_feedback') {
			activeTab = 'my_feedback';
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
				message
			});

			showToast(t('feedback.success'), 'success');
			// Reset form
			message = '';
			const issueType = 'issue';
			type = issueType;
			// Automatically switch to my feedback to see the submitted one
			activeTab = 'my_feedback';
		} catch (error) {
			console.error(error);
			showToast(t('feedback.error'), 'error');
		}
	};
</script>

<SEO title={t('feedback.title')} />

<div class="max-w-3xl mx-auto px-4 sm:px-6 pt-4 sm:pt-6 pb-48 md:pb-32">
	<!-- Page Header -->
	<div class="mb-6 sm:mb-8 text-center sm:text-left">
		<PageHeader
			title={t('feedback.title')}
			subtitle={t('feedback.subtitle')}
			icon={MessageSquare}
			theme="red"
		/>
	</div>

	<!-- Tabs -->
	<div class="flex items-center w-full mb-6 border-b border-slate-200 dark:border-zinc-800">
		<button
			class="flex-1 pb-3 text-sm font-bold transition-all cursor-pointer border-b-2 {activeTab ===
			'submit'
				? 'text-red-600 border-red-500 dark:text-red-400 dark:border-red-500'
				: 'text-slate-500 border-transparent hover:text-slate-700 hover:border-slate-300 dark:text-slate-400 dark:hover:text-slate-300 dark:hover:border-zinc-700'}"
			onclick={() => (activeTab = 'submit')}
		>
			{t('feedback.tabs.submit')}
		</button>
		<button
			class="flex-1 pb-3 text-sm font-bold transition-all cursor-pointer border-b-2 {activeTab ===
			'my_feedback'
				? 'text-red-600 border-red-500 dark:text-red-400 dark:border-red-500'
				: 'text-slate-500 border-transparent hover:text-slate-700 hover:border-slate-300 dark:text-slate-400 dark:hover:text-slate-300 dark:hover:border-zinc-700'}"
			onclick={() => (activeTab = 'my_feedback')}
		>
			{t('feedback.tabs.my_feedback')}
		</button>
	</div>

	<!-- Content -->
	{#if activeTab === 'submit'}
		<div
			class="bg-white dark:bg-zinc-900 rounded-3xl shadow-sm border border-slate-100 dark:border-zinc-800"
		>
			<form
				onsubmit={(e) => {
					e.preventDefault();
					handleSubmit();
				}}
				class="p-6 sm:p-8"
			>
				<!-- Feedback Type -->
				<div class="space-y-4 mb-8">
					<span class="text-sm font-bold text-slate-900 dark:text-white ml-1 block">
						{t('feedback.form.type.label')}
					</span>
					<div class="grid grid-cols-3 gap-2">
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
				<div class="space-y-2 mb-8">
					<div class="flex items-center justify-between ml-1 mb-2">
						<label class="text-sm font-bold text-slate-900 dark:text-white" for="message">
							{t('feedback.form.message.label')}
						</label>
						<span
							class="text-xs font-bold {message.length < 10
								? 'text-red-500'
								: message.length >= 1000
									? 'text-red-500'
									: 'text-slate-400'}"
						>
							{message.length}/1000
						</span>
					</div>
					<textarea
						id="message"
						name="message"
						bind:value={message}
						rows="5"
						maxlength="1000"
						class="w-full px-4 py-3 rounded-2xl bg-slate-50 dark:bg-zinc-800/50 border-2 border-transparent focus:border-red-500 focus:bg-white dark:focus:bg-zinc-900 focus:ring-0 transition-all outline-none text-slate-900 dark:text-white placeholder:text-slate-400 resize-y min-h-[120px] max-h-[400px] font-medium"
						placeholder={t('feedback.form.message.placeholder')}
						required
					></textarea>
				</div>

				<!-- Contact Info (Required, Readonly) -->
				<div class="pt-4 border-t border-slate-100 dark:border-zinc-800 space-y-6">
					<div
						class="bg-blue-50 dark:bg-blue-900/20 text-blue-800 dark:text-blue-300 p-4 rounded-xl text-sm flex items-start gap-3"
					>
						<AlertCircle class="w-5 h-5 shrink-0 mt-0.5" />
						<p>{t('feedback.form.info')}</p>
					</div>

					<div class="grid md:grid-cols-2 gap-6">
						<div class="space-y-2">
							<label class="text-sm font-bold text-slate-900 dark:text-white ml-1" for="name">
								{t('feedback.form.name.label')}
							</label>
							<input
								id="name"
								name="name"
								type="text"
								autocomplete="name"
								bind:value={name}
								placeholder={t('feedback.form.name.placeholder')}
								readonly
								class="w-full px-4 py-3 rounded-2xl bg-slate-50 dark:bg-zinc-800/50 border-2 border-transparent focus:border-red-500 focus:bg-white dark:focus:bg-zinc-900 focus:ring-0 transition-all outline-none text-slate-900 dark:text-white placeholder:text-slate-400 font-medium cursor-not-allowed opacity-70"
							/>
						</div>
						<div class="space-y-2">
							<label class="text-sm font-bold text-slate-900 dark:text-white ml-1" for="email">
								{t('feedback.form.email.label')}
							</label>
							<input
								id="email"
								name="email"
								type="email"
								autocomplete="email"
								bind:value={email}
								placeholder={t('feedback.form.email.placeholder')}
								readonly
								class="w-full px-4 py-3 rounded-2xl bg-slate-50 dark:bg-zinc-800/50 border-2 border-transparent focus:border-red-500 focus:bg-white dark:focus:bg-zinc-900 focus:ring-0 transition-all outline-none text-slate-900 dark:text-white placeholder:text-slate-400 font-medium cursor-not-allowed opacity-70"
							/>
						</div>
					</div>
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
	{:else}
		<FeedbackList />
	{/if}
</div>
