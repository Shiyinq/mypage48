<script lang="ts">
	import { preventDefault } from 'svelte/legacy';

	import { goto } from '$app/navigation';
	import { isAuthenticated, showToast } from '$lib/stores';
	import { logger } from '$lib/utils/logger';
	import { getErrorMessage } from '$lib/utils/api';
	import { authStore } from '$lib/stores/auth';
	import { Lock, ArrowRight, User } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import AuthLayout from '$lib/components/layouts/AuthLayout.svelte';

	import { loginSchema } from '$lib/schemas/auth';
	import { ZodError } from 'zod';
	import PasswordInput from '$lib/components/PasswordInput.svelte';

	const { t } = useTranslation();

	let email = $state('');
	let password = $state('');
	let isLoading = $state(false);
	let error: string | null = null;
	let errors: Record<string, string> = $state({});

	let isValid = $derived(
		email.length > 0 && password.length > 0 && Object.values(errors).every((e) => !e)
	);

	const validateField = (field: 'email' | 'password', value: string) => {
		try {
			// @ts-expect-error - dynamic pick keys are not perfectly inferred by TS for Zod
			const fieldSchema = loginSchema.pick({ [field]: true });
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
			// Client-side validation
			loginSchema.parse({ email, password });

			await authStore.login({ username: email, password });
			isAuthenticated.set(true);
			showToast($t('auth.login.welcomeBack'));
			goto('/');
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
			logger.error('Login failed', err, { context: 'LoginPage' });
			error = errorMsg || $t('auth.login.failed');
			showToast(error, 'error');
		} finally {
			isLoading = false;
		}
	};
</script>

<SEO title={$t('auth.login.title')} path="/login" description={$t('seo.login')} />

<AuthLayout title={$t('auth.login.title')} subtitle={$t('auth.login.subtitle')}>
	<form onsubmit={preventDefault(handleSubmit)} class="space-y-5" novalidate>
		<div>
			<label for="email" class="block text-sm font-bold text-gray-500 dark:text-gray-400 mb-1.5"
				>{$t('auth.login.emailLabel')}</label
			>
			<div class="relative">
				<div class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 dark:text-zinc-500">
					<User class="w-5 h-5" />
				</div>
				<input
					type="text"
					id="email"
					name="username"
					bind:value={email}
					oninput={() => validateField('email', email)}
					class={`w-full pl-12 pr-4 py-3.5 bg-white/80 dark:bg-zinc-800/50 border rounded-xl focus:ring-2 focus:ring-red-500 outline-none font-medium text-gray-900 dark:text-white transition-all placeholder-gray-400 dark:placeholder-zinc-600 ${errors.email ? 'border-red-500' : 'border-gray-200 dark:border-zinc-700'}`}
					placeholder={$t('auth.login.emailPlaceholder')}
				/>
			</div>
			{#if errors.email}
				<p class="text-xs text-red-500 mt-1 ml-1 font-medium">{errors.email}</p>
			{/if}
		</div>

		<div>
			<PasswordInput
				id="password"
				name="password"
				label={$t('auth.login.passwordLabel')}
				placeholder={$t('auth.login.passwordPlaceholder')}
				bind:value={password}
				error={errors.password}
				oninput={() => validateField('password', password)}
			>
				{#snippet leading()}
					<Lock class="w-5 h-5" />
				{/snippet}
			</PasswordInput>
		</div>

		<div class="flex justify-end">
			<a
				href="/auth/forgot-password"
				class="text-xs font-bold text-red-600 hover:text-red-700 hover:underline"
			>
				{$t('auth.login.forgotPassword')}
			</a>
		</div>

		<button
			type="submit"
			disabled={isLoading || !isValid}
			class="w-full idol-gradient text-white py-4 rounded-2xl font-bold text-lg shadow-sm hover:shadow-md hover:scale-[1.01] transition-all active:scale-95 flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed cursor-pointer border border-white/20"
		>
			{#if isLoading}
				<span class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"
				></span>
			{:else}
				{$t('auth.login.signIn')} <ArrowRight class="w-5 h-5" />
			{/if}
		</button>
	</form>

	{#snippet footer()}
		<div>
			<p class="text-sm text-gray-500 dark:text-gray-400">{$t('auth.login.noAccount')}</p>
			<button
				onclick={() => goto('/register')}
				class="mt-2 text-red-600 font-bold text-sm hover:underline flex items-center justify-center gap-1 mx-auto cursor-pointer"
			>
				{$t('auth.login.registerCta')}
				<User class="w-4 h-4" />
			</button>
		</div>
	{/snippet}
</AuthLayout>
