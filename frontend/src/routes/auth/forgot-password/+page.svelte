<script lang="ts">
	import { authStore } from '$lib/stores/auth';
	import { showToast } from '$lib/stores';
	import { logger } from '$lib/utils/logger';
	import { getErrorMessage } from '$lib/utils/api';
	import { Mail, ArrowLeft, LoaderCircle, KeyRound } from 'lucide-svelte';
	import SEO from '$lib/components/SEO.svelte';
	import AuthLayout from '$lib/components/layouts/AuthLayout.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { forgotPasswordSchema } from '$lib/schemas/auth';
	import { ZodError } from 'zod';

	const { t } = useTranslation();

	let email = $state('');
	let isLoading = $state(false);
	let isSent = $state(false);
	let error: string | null = $state(null);
	let errors: Record<string, string> = $state({});

	let isValid = $derived(email.length > 0 && Object.values(errors).every((e) => !e));

	const validateField = (field: 'email', value: string) => {
		try {
			const fieldSchema = forgotPasswordSchema.pick({ [field]: true });
			fieldSchema.parse({ [field]: value });
			errors[field] = '';
		} catch (err) {
			if (err instanceof ZodError) {
				const fieldErrors = err.flatten().fieldErrors as Record<string, string[] | undefined>;
				errors[field] = fieldErrors[field]?.[0] || '';
			}
		}
	};

	const handleSubmit = async () => {
		isLoading = true;
		error = null;
		errors = {};

		try {
			forgotPasswordSchema.parse({ email });

			await authStore.forgotPassword({ email });
			isSent = true;
			showToast($t('auth.forgotPassword.sent'), 'success');
		} catch (err) {
			if (err instanceof ZodError) {
				const fieldErrors = err.flatten().fieldErrors;
				errors = Object.fromEntries(
					Object.entries(fieldErrors).map(([key, val]) => [
						key,
						Array.isArray(val) && val.length > 0 ? val[0] : ''
					])
				);
				return;
			}

			const errorMsg = getErrorMessage(err);
			logger.error('Forgot password failed', err, { context: 'ForgotPasswordPage' });
			error = errorMsg || $t('auth.forgotPassword.error');
			showToast(error, 'error');
		} finally {
			isLoading = false;
		}
	};
</script>

<SEO
	title={$t('auth.forgotPassword.title')}
	path="/auth/forgot-password"
	description={$t('seo.forgotPassword')}
/>

<AuthLayout
	title={$t('auth.forgotPassword.title')}
	subtitle={isSent
		? $t('auth.forgotPassword.successMessage', { email })
		: $t('auth.forgotPassword.instruction')}
	icon={KeyRound}
>
	{#if !isSent}
		<form
			onsubmit={(e) => {
				e.preventDefault();
				handleSubmit();
			}}
			class="space-y-6"
			novalidate
		>
			<div>
				<label
					class="block text-sm font-bold text-gray-500 dark:text-gray-400 mb-1.5"
					for="email-input">{$t('auth.forgotPassword.emailLabel')}</label
				>
				<div class="relative">
					<div class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 dark:text-zinc-500">
						<Mail class="w-5 h-5" />
					</div>
					<input
						id="email-input"
						type="email"
						bind:value={email}
						oninput={() => validateField('email', email)}
						class={`w-full pl-12 pr-4 py-3.5 bg-white/80 dark:bg-zinc-800/50 border rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none font-medium text-gray-900 dark:text-white transition-all placeholder-gray-400 dark:placeholder-zinc-600 ${errors.email ? 'border-red-500' : 'border-gray-200 dark:border-zinc-700'}`}
						placeholder="member@mypage48.com"
					/>
				</div>
				{#if errors.email}
					<p class="text-xs text-red-600 font-bold mt-2 ml-1">{errors.email}</p>
				{/if}
				{#if error}
					<p class="text-xs text-red-600 font-bold mt-2 ml-1">{error}</p>
				{/if}
			</div>

			<button
				type="submit"
				disabled={isLoading || !isValid}
				class="w-full idol-gradient text-white py-4 rounded-2xl font-bold text-lg shadow-sm hover:shadow-md hover:scale-[1.01] transition-all active:scale-95 flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed cursor-pointer border border-white/20"
			>
				{#if isLoading}
					<LoaderCircle class="w-5 h-5 animate-spin" /> {$t('auth.forgotPassword.submitting')}
				{:else}
					{$t('auth.forgotPassword.submit')}
				{/if}
			</button>
		</form>
	{:else}
		<div class="space-y-4">
			<button
				onclick={() => (isSent = false)}
				class="w-full py-4 rounded-2xl font-bold text-lg text-gray-700 dark:text-gray-200 bg-gray-100 dark:bg-zinc-800 hover:bg-gray-200 dark:hover:bg-zinc-700 transition-all cursor-pointer"
			>
				{$t('auth.forgotPassword.tryAnother')}
			</button>
			<p class="text-xs text-gray-400 text-center">
				{$t('auth.forgotPassword.spamCheck')}
			</p>
		</div>
	{/if}

	{#snippet footer()}
		<div>
			<a
				href="/login"
				class="text-sm font-bold text-red-500 hover:text-red-600 transition-colors inline-flex items-center gap-2"
			>
				<ArrowLeft class="w-4 h-4" />
				{$t('auth.forgotPassword.backToLogin')}
			</a>
		</div>
	{/snippet}
</AuthLayout>
