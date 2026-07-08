<script lang="ts">
	import { goto } from '$app/navigation';
	import { onDestroy } from 'svelte';
	import { showToast } from '$lib/stores';
	import { logger } from '$lib/utils/logger';
	import { getErrorMessage } from '$lib/utils/api';
	import { authStore } from '$lib/stores/auth.svelte';
	import { Lock, Mail, User, Shield, MailCheck } from 'lucide-svelte';
	import SEO from '$lib/components/SEO.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import AuthLayout from '$lib/components/layouts/AuthLayout.svelte';

	import PasswordStrengthChecklist from '$lib/components/auth/PasswordStrengthChecklist.svelte';
	import PasswordInput from '$lib/components/PasswordInput.svelte';
	import { registerSchema, registerBaseSchema } from '$lib/schemas/auth';
	import { ZodError } from 'zod';

	const { t } = useTranslation();

	let formData = $state({
		username: '',
		fullName: '',
		email: '',
		password: '',
		confirmPassword: ''
	});

	let isLoading = $state(false);
	let isSuccess = $state(false);
	let isResending = $state(false);
	let resendCountdown = $state(0);
	let countdownTimer: ReturnType<typeof setInterval> | null = null;
	let error: string | null = $state(null);
	let errors: Record<string, string> = $state({});

	let isValid = $derived(
		Object.values(formData).every((val) => val.length > 0) && Object.values(errors).every((e) => !e)
	);

	const validateField = (field: keyof typeof formData) => {
		try {
			if (field === 'confirmPassword') {
				// Custom check for confirm password since it's a refinement
				if (formData.confirmPassword !== formData.password) {
					errors.confirmPassword = "Passwords don't match";
				} else {
					errors.confirmPassword = '';
				}
				return;
			}

			// @ts-expect-error - dynamic pick keys are not perfectly inferred by TS for Zod
			const fieldSchema = registerBaseSchema.pick({ [field]: true });
			fieldSchema.parse({ [field]: formData[field] });
			errors[field] = '';
		} catch (err) {
			if (err instanceof ZodError) {
				const fieldErrors = err.flatten().fieldErrors as Record<string, string[] | undefined>;
				errors[field] = fieldErrors[field]?.[0] || '';
			}
		}
	};

	const startCountdown = () => {
		resendCountdown = 60;
		if (countdownTimer) clearInterval(countdownTimer);
		countdownTimer = setInterval(() => {
			if (resendCountdown > 0) {
				resendCountdown--;
			} else {
				if (countdownTimer) {
					clearInterval(countdownTimer);
					countdownTimer = null;
				}
			}
		}, 1000);
	};

	const handleResendVerification = async () => {
		if (isResending) return;
		isResending = true;

		try {
			await authStore.sendVerificationEmail({ email: formData.email });
			showToast(t('auth.login.resendSuccess'), 'success');
			startCountdown();
		} catch (err) {
			logger.error('Failed to resend verification email', err, { context: 'RegisterPage' });
			showToast(getErrorMessage(err), 'error');
		} finally {
			isResending = false;
		}
	};

	onDestroy(() => {
		if (countdownTimer) clearInterval(countdownTimer);
	});

	const handleSubmit = async () => {
		isLoading = true;
		error = null;
		errors = {};

		try {
			// Client-side validation
			registerSchema.parse(formData);

			await authStore.register(formData);
			isSuccess = true;
			startCountdown();
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
			logger.error('Registration failed', err, { context: 'RegisterPage' });
			error = errorMsg || t('auth.register.failed');
		} finally {
			isLoading = false;
		}
	};
</script>

<SEO title={t('auth.register.title')} path="/register" description={t('seo.register')} />

<AuthLayout
	title={t('auth.register.title')}
	subtitle={t('auth.register.subtitle')}
	cardWidth="max-w-4xl"
>
	{#if isSuccess}
		<div
			class="flex flex-col items-center justify-center py-8 text-center space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500"
		>
			<div
				class="w-20 h-20 bg-red-50 dark:bg-red-900/20 rounded-full flex items-center justify-center text-red-500 mb-2 ring-8 ring-red-50/50 dark:ring-red-900/10"
			>
				<MailCheck class="w-10 h-10" />
			</div>

			<div class="space-y-2">
				<h3 class="text-2xl font-bold text-gray-900 dark:text-white px-4 leading-snug">
					{t('auth.register.success')}
				</h3>
				<p class="text-gray-500 dark:text-gray-400 max-w-sm mx-auto leading-relaxed px-4">
					{t('auth.register.successDesc')}
				</p>
			</div>

			<div class="pt-4 w-full max-w-sm mx-auto space-y-3 px-4">
				{#if resendCountdown > 0}
					<p
						class="text-xs text-red-600/70 dark:text-red-400/70 font-bold uppercase tracking-wider animate-pulse mb-4"
					>
						{t('auth.login.resendWait', { seconds: resendCountdown })}
					</p>
				{:else}
					<button
						type="button"
						onclick={handleResendVerification}
						disabled={isResending}
						class="w-full bg-white dark:bg-zinc-800 border-2 border-red-100 dark:border-red-900/30 text-red-600 dark:text-red-400 py-3.5 rounded-2xl font-bold text-sm hover:bg-red-50 dark:hover:bg-red-900/20 transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
					>
						{t('auth.login.resendVerification')}
						{#if isResending}
							<span
								class="w-4 h-4 border-2 border-red-600/30 border-t-red-600 rounded-full animate-spin"
							></span>
						{/if}
					</button>
				{/if}

				<button
					onclick={() => goto('/login')}
					class="w-full text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 py-3.5 rounded-2xl font-bold text-sm cursor-pointer transition-colors"
				>
					{t('auth.login.signIn')}
				</button>
			</div>

			<div
				class="w-full max-w-lg mx-auto text-left border-t border-gray-100 dark:border-zinc-800/50 pt-5 px-4 sm:px-0 !mt-2"
			>
				<h4 class="text-sm font-bold text-gray-900 dark:text-white mb-3">
					{t('auth.register.faq.title')}
				</h4>
				<div
					class="bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-900/30 rounded-xl p-3.5 sm:p-4"
				>
					<h5
						class="text-sm font-bold text-amber-900 dark:text-amber-500 mb-2.5 flex items-start gap-2 leading-snug"
					>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							width="16"
							height="16"
							viewBox="0 0 24 24"
							fill="none"
							stroke="currentColor"
							stroke-width="2"
							stroke-linecap="round"
							stroke-linejoin="round"
							class="lucide lucide-alert-circle shrink-0 mt-0.5"
							><circle cx="12" cy="12" r="10" /><line x1="12" x2="12" y1="8" y2="12" /><line
								x1="12"
								x2="12.01"
								y1="16"
								y2="16"
							/></svg
						>
						{t('auth.register.faq.missingEmailTitle')}
					</h5>
					<ul
						class="text-xs text-amber-800 dark:text-amber-400/80 leading-relaxed ml-4 sm:ml-5 list-disc pl-1 space-y-2"
					>
						<li>{t('auth.register.faq.missingEmailPoint1')}</li>
						<li>{t('auth.register.faq.missingEmailPoint2')}</li>
						<li>{t('auth.register.faq.missingEmailPoint3')}</li>
						<li>
							{t('auth.register.faq.missingEmailPoint4', {
								buttonName: t('auth.login.resendVerification')
							})}
						</li>
					</ul>
				</div>
			</div>
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
			<div class="grid md:grid-cols-2 gap-4">
				<!-- Left Column: Personal Information -->
				<div class="space-y-3">
					<div>
						<label
							for="fullName"
							class="block text-sm font-bold text-gray-500 dark:text-gray-400 mb-1.5"
							>{t('auth.register.fullName')}</label
						>
						<input
							id="fullName"
							name="fullName"
							bind:value={formData.fullName}
							oninput={() => validateField('fullName')}
							class={`w-full px-4 py-3.5 bg-white/80 dark:bg-zinc-800/50 border rounded-xl focus:ring-2 focus:ring-red-500 outline-none font-medium text-gray-900 dark:text-white transition-all placeholder-gray-400 dark:placeholder-zinc-600 ${errors.fullName ? 'border-red-500' : 'border-gray-200 dark:border-zinc-700'}`}
							placeholder="Catherina Vallencia"
						/>
						{#if errors.fullName}
							<p class="text-xs text-red-500 mt-1 ml-1 font-medium">{errors.fullName}</p>
						{/if}
					</div>

					<div>
						<label
							for="email"
							class="block text-sm font-bold text-gray-500 dark:text-gray-400 mb-1.5"
							>{t('auth.register.email')}</label
						>
						<div class="relative">
							<div
								class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 dark:text-zinc-500"
							>
								<Mail class="w-5 h-5" />
							</div>
							<input
								type="email"
								id="email"
								name="email"
								bind:value={formData.email}
								oninput={() => validateField('email')}
								class={`w-full pl-12 pr-4 py-3.5 bg-white/80 dark:bg-zinc-800/50 border rounded-xl focus:ring-2 focus:ring-red-500 outline-none font-medium text-gray-900 dark:text-white transition-all placeholder-gray-400 dark:placeholder-zinc-600 ${errors.email ? 'border-red-500' : 'border-gray-200 dark:border-zinc-700'}`}
								placeholder="erine@oline.com"
							/>
						</div>
						{#if errors.email}
							<p class="text-xs text-red-500 mt-1 ml-1 font-medium">{errors.email}</p>
						{/if}
					</div>

					<div>
						<label
							for="username"
							class="block text-sm font-bold text-gray-500 dark:text-gray-400 mb-1.5"
							>{t('auth.register.username')}</label
						>
						<div class="relative">
							<div
								class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 dark:text-zinc-500"
							>
								<User class="w-5 h-5" />
							</div>
							<input
								id="username"
								name="username"
								bind:value={formData.username}
								oninput={() => validateField('username')}
								class={`w-full pl-12 pr-4 py-3.5 bg-white/80 dark:bg-zinc-800/50 border rounded-xl focus:ring-2 focus:ring-red-500 outline-none font-medium text-gray-900 dark:text-white transition-all placeholder-gray-400 dark:placeholder-zinc-600 ${errors.username ? 'border-red-500' : 'border-gray-200 dark:border-zinc-700'}`}
								placeholder="olinecantik"
							/>
						</div>
						{#if errors.username}
							<p class="text-xs text-red-500 mt-1 ml-1 font-medium">{errors.username}</p>
						{/if}
					</div>
				</div>

				<!-- Right Column: Account Security -->
				<div class="space-y-4">
					<div>
						<PasswordInput
							id="password"
							name="password"
							label={t('auth.register.password')}
							placeholder="••••••••"
							bind:value={formData.password}
							error={errors.password}
							oninput={() => validateField('password')}
						>
							{#snippet leading()}
								<Lock class="w-5 h-5" />
							{/snippet}
						</PasswordInput>
					</div>
					<div>
						<PasswordInput
							id="confirmPassword"
							name="confirmPassword"
							label={t('auth.register.confirmPassword')}
							placeholder="••••••••"
							bind:value={formData.confirmPassword}
							error={errors.confirmPassword}
							oninput={() => validateField('confirmPassword')}
						>
							{#snippet leading()}
								<Shield class="w-5 h-5" />
							{/snippet}
						</PasswordInput>
					</div>

					<PasswordStrengthChecklist password={formData.password} />
				</div>
			</div>

			{#if error}
				<p
					class="text-xs text-red-600 dark:text-red-400 font-bold text-center bg-red-50 dark:bg-red-900/20 p-2 rounded-xl border border-red-100 dark:border-red-800"
				>
					{error}
				</p>
			{/if}

			<div>
				<button
					type="submit"
					disabled={isLoading || !isValid}
					class="w-full idol-gradient text-white py-4 rounded-2xl font-bold text-lg shadow-sm hover:shadow-md hover:scale-[1.01] transition-all active:scale-95 flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed cursor-pointer border border-white/20"
				>
					{#if isLoading}
						{t('auth.register.submitting')}
					{:else}
						{t('auth.register.submit')}
					{/if}
				</button>
			</div>
		</form>
	{/if}

	{#snippet footer()}
		{#if !isSuccess}
			<div>
				<p class="text-sm text-gray-500 dark:text-gray-400">{t('auth.register.hasAccount')}</p>
				<button
					onclick={() => goto('/login')}
					class="mt-2 text-red-600 font-bold text-sm hover:underline flex items-center justify-center gap-1 mx-auto cursor-pointer"
				>
					{t('auth.register.signIn')}
				</button>
			</div>
		{/if}
	{/snippet}
</AuthLayout>
