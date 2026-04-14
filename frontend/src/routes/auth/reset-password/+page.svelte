<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { authStore } from '$lib/stores/auth.svelte';
	import { showToast } from '$lib/stores';
	import { logger } from '$lib/utils/logger';
	import { getErrorMessage } from '$lib/utils/api';
	import { Lock, ArrowLeft, LoaderCircle, CircleCheck, ShieldCheck } from 'lucide-svelte';
	import SEO from '$lib/components/SEO.svelte';
	import AuthLayout from '$lib/components/layouts/AuthLayout.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { resetPasswordSchema, resetPasswordBaseSchema } from '$lib/schemas/auth';
	import PasswordInput from '$lib/components/PasswordInput.svelte';
	import PasswordStrengthChecklist from '$lib/components/auth/PasswordStrengthChecklist.svelte';
	import { ZodError } from 'zod';

	const { t } = useTranslation();

	let token = $state('');
	let newPassword = $state('');
	let confirmPassword = $state('');
	let isLoading = $state(false);
	let error: string | null = $state(null);
	let errors: Record<string, string> = $state({});
	let isSuccess = $state(false);

	onMount(() => {
		token = $page.url.searchParams.get('token') || '';
		if (!token) {
			error = $t('auth.resetPassword.invalidToken');
		}
	});

	let isValid = $derived(
		newPassword.length > 0 && confirmPassword.length > 0 && Object.values(errors).every((e) => !e)
	);

	const validateField = (field: 'newPassword' | 'confirmPassword', value: string) => {
		try {
			if (field === 'confirmPassword') {
				if (value !== newPassword) {
					errors.confirmPassword = "Passwords don't match";
				} else {
					errors.confirmPassword = '';
				}
				return;
			}

			const fieldSchema = resetPasswordBaseSchema.pick({ [field]: true });
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
			resetPasswordSchema.parse({ newPassword, confirmPassword });

			await authStore.resetPassword({
				token,
				new_password: newPassword,
				confirm_password: confirmPassword
			});
			isSuccess = true;
			showToast($t('auth.resetPassword.successToast'), 'success');
			setTimeout(() => {
				goto('/login');
			}, 2000);
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
			logger.error('Reset password failed', err, { context: 'ResetPasswordPage' });
			error = errorMsg || 'Failed to reset password';
			showToast(error, 'error');
		} finally {
			isLoading = false;
		}
	};
</script>

<SEO
	title={$t('auth.resetPassword.title')}
	path="/auth/reset-password"
	description={$t('seo.resetPassword')}
/>

<AuthLayout
	title={$t('auth.resetPassword.title')}
	subtitle={isSuccess ? $t('auth.resetPassword.successMessage') : $t('auth.resetPassword.subtitle')}
	icon={ShieldCheck}
>
	{#if isSuccess}
		<div class="text-center py-4">
			<div
				class="w-20 h-20 rounded-full bg-green-50 dark:bg-green-900/20 flex items-center justify-center mx-auto mb-6"
			>
				<CircleCheck class="w-10 h-10 text-green-500" />
			</div>
			<h1 class="text-2xl font-black text-gray-900 dark:text-white mb-2">
				{$t('auth.resetPassword.successTitle')}
			</h1>
		</div>
	{:else}
		<form
			onsubmit={(e) => {
				e.preventDefault();
				handleSubmit();
			}}
			class="space-y-4"
			novalidate
		>
			<div>
				<PasswordInput
					id="new-password"
					name="newPassword"
					label={$t('auth.resetPassword.newPassword')}
					placeholder="••••••••"
					bind:value={newPassword}
					error={errors.newPassword}
					oninput={() => validateField('newPassword', newPassword)}
				>
					{#snippet leading()}
						<Lock class="w-5 h-5" />
					{/snippet}
				</PasswordInput>
			</div>

			<div>
				<PasswordInput
					id="confirm-password"
					name="confirmPassword"
					label={$t('auth.resetPassword.confirmPassword')}
					placeholder="••••••••"
					bind:value={confirmPassword}
					error={errors.confirmPassword}
					oninput={() => validateField('confirmPassword', confirmPassword)}
				>
					{#snippet leading()}
						<Lock class="w-5 h-5" />
					{/snippet}
				</PasswordInput>
				<PasswordStrengthChecklist password={newPassword} />
			</div>

			{#if error}
				<div
					class="p-3 bg-red-50 dark:bg-red-900/20 rounded-xl border border-red-100 dark:border-red-800 text-center"
				>
					<p class="text-xs text-red-600 dark:text-red-400 font-bold">{error}</p>
				</div>
			{/if}

			<button
				type="submit"
				disabled={isLoading || !token || !isValid}
				class="w-full idol-gradient text-white py-4 rounded-2xl font-bold text-lg shadow-sm hover:shadow-md hover:scale-[1.01] transition-all active:scale-95 flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed cursor-pointer border border-white/20"
			>
				{#if isLoading}
					<LoaderCircle class="w-5 h-5 animate-spin" /> {$t('auth.resetPassword.submitting')}
				{:else}
					{$t('auth.resetPassword.submit')}
				{/if}
			</button>
		</form>
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
