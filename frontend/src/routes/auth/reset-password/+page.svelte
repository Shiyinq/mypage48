<script lang="ts">
	export let params: Record<string, string> | undefined = undefined;
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { authStore } from '$lib/stores/auth';
	import { showToast } from '$lib/stores';
	import { logger } from '$lib/utils/logger';
	import { getErrorMessage } from '$lib/utils/api';
	import { Lock, ArrowLeft, LoaderCircle, CircleCheck, ShieldCheck } from 'lucide-svelte';
	import SEO from '$lib/components/SEO.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { resetPasswordSchema, resetPasswordBaseSchema } from '$lib/schemas/auth';
	import PasswordInput from '$lib/components/PasswordInput.svelte';
	import PasswordStrengthChecklist from '$lib/components/auth/PasswordStrengthChecklist.svelte';
	import { ZodError } from 'zod';

	const { t } = useTranslation();

	let token = '';
	let newPassword = '';
	let confirmPassword = '';
	let isLoading = false;
	let error: string | null = null;
	let errors: Record<string, string> = {};
	let isSuccess = false;

	onMount(() => {
		token = $page.url.searchParams.get('token') || '';
		if (!token) {
			error = $t('auth.resetPassword.invalidToken');
		}
	});

	$: isValid =
		newPassword.length > 0 && confirmPassword.length > 0 && Object.values(errors).every((e) => !e);

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

			// @ts-ignore - pick is valid on z.object
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

<div
	class="min-h-screen flex items-center justify-center p-4 bg-gray-50 dark:bg-zinc-950 relative overflow-hidden"
>
	<!-- Background decorations -->
	<div class="absolute top-0 left-0 w-full h-full overflow-hidden -z-10">
		<div
			class="absolute top-[-20%] right-[-10%] w-[50%] h-[50%] rounded-full bg-red-500/10 blur-[100px] animate-pulse"
		></div>
		<div
			class="absolute bottom-[-10%] left-[-20%] w-[50%] h-[50%] rounded-full bg-orange-500/10 blur-[100px] animate-pulse"
		></div>
	</div>

	<div class="w-full max-w-md">
		<div
			class="bg-white/80 dark:bg-zinc-900/80 backdrop-blur-xl p-8 rounded-3xl shadow-2xl border border-white/60 dark:border-zinc-800 animate-fade-in"
		>
			{#if isSuccess}
				<div class="text-center py-8">
					<div
						class="w-20 h-20 rounded-full bg-green-50 dark:bg-green-900/20 flex items-center justify-center mx-auto mb-6"
					>
						<CircleCheck class="w-10 h-10 text-green-500" />
					</div>
					<h1 class="text-2xl font-black text-gray-900 dark:text-white mb-2">
						{$t('auth.resetPassword.successTitle')}
					</h1>
					<p class="text-gray-500 dark:text-gray-400 font-medium mb-8">
						{$t('auth.resetPassword.successMessage')}
					</p>
					<button
						on:click={() => goto('/login')}
						class="w-full py-4 rounded-2xl font-bold idol-gradient text-white shadow-lg shadow-green-200 hover:shadow-xl hover:scale-[1.02] transition-all cursor-pointer"
					>
						{$t('auth.resetPassword.goToLogin')}
					</button>
				</div>
			{:else}
				<div class="text-center mb-8">
					<div
						class="w-16 h-16 rounded-full bg-red-50 dark:bg-red-900/20 flex items-center justify-center mx-auto mb-4 text-red-500 dark:text-red-400"
					>
						<ShieldCheck class="w-8 h-8" />
					</div>
					<h1 class="text-2xl font-black text-gray-900 dark:text-white mb-2">
						{$t('auth.resetPassword.title')}
					</h1>
					<p class="text-gray-500 dark:text-gray-400 font-medium text-sm">
						{$t('auth.resetPassword.subtitle')}
					</p>
				</div>

				<form on:submit|preventDefault={handleSubmit} class="space-y-5" novalidate>
					<div>
						<PasswordInput
							id="new-password"
							name="newPassword"
							label={$t('auth.resetPassword.newPassword')}
							placeholder="••••••••"
							bind:value={newPassword}
							error={errors.newPassword}
							on:input={() => validateField('newPassword', newPassword)}
						>
							<Lock class="w-5 h-5" slot="leading" />
						</PasswordInput>
						<PasswordStrengthChecklist password={newPassword} />
					</div>

					<div>
						<PasswordInput
							id="confirm-password"
							name="confirmPassword"
							label={$t('auth.resetPassword.confirmPassword')}
							placeholder="••••••••"
							bind:value={confirmPassword}
							error={errors.confirmPassword}
							on:input={() => validateField('confirmPassword', confirmPassword)}
						>
							<Lock class="w-5 h-5" slot="leading" />
						</PasswordInput>
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
						class="w-full idol-gradient text-white py-4 rounded-2xl font-bold text-lg shadow-lg shadow-red-200 hover:shadow-xl hover:scale-[1.02] transition-all active:scale-95 flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed cursor-pointer"
					>
						{#if isLoading}
							<LoaderCircle class="w-5 h-5 animate-spin" /> {$t('auth.resetPassword.submitting')}
						{:else}
							{$t('auth.resetPassword.submit')}
						{/if}
					</button>

					<div class="text-center mt-6">
						<a
							href="/login"
							class="text-sm font-bold text-red-500 hover:text-red-600 transition-colors inline-flex items-center gap-2"
						>
							<ArrowLeft class="w-4 h-4" />
							{$t('auth.forgotPassword.backToLogin')}
						</a>
					</div>
				</form>
			{/if}
		</div>
	</div>
</div>
