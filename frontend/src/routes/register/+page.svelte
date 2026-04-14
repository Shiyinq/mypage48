<script lang="ts">
	import { goto } from '$app/navigation';
	import { showToast } from '$lib/stores';
	import { logger } from '$lib/utils/logger';
	import { getErrorMessage } from '$lib/utils/api';
	import { authStore } from '$lib/stores/auth.svelte';
	import { Lock, Mail, User, Shield } from 'lucide-svelte';
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

	const handleSubmit = async () => {
		isLoading = true;
		error = null;
		errors = {};

		try {
			// Client-side validation
			registerSchema.parse(formData);

			await authStore.register(formData);
			showToast($t('auth.register.success'), 'success');

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
			logger.error('Registration failed', err, { context: 'RegisterPage' });
			error = errorMsg || $t('auth.register.failed');
		} finally {
			isLoading = false;
		}
	};
</script>

<SEO title={$t('auth.register.title')} path="/register" description={$t('seo.register')} />

<AuthLayout
	title={$t('auth.register.title')}
	subtitle={$t('auth.register.subtitle')}
	cardWidth="max-w-4xl"
>
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
						>{$t('auth.register.fullName')}</label
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
					<label for="email" class="block text-sm font-bold text-gray-500 dark:text-gray-400 mb-1.5"
						>{$t('auth.register.email')}</label
					>
					<div class="relative">
						<div class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 dark:text-zinc-500">
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
						>{$t('auth.register.username')}</label
					>
					<div class="relative">
						<div class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 dark:text-zinc-500">
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
						label={$t('auth.register.password')}
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
						label={$t('auth.register.confirmPassword')}
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
					{$t('auth.register.submitting')}
				{:else}
					{$t('auth.register.submit')}
				{/if}
			</button>
		</div>
	</form>

	{#snippet footer()}
		<div>
			<p class="text-sm text-gray-500 dark:text-gray-400">{$t('auth.register.hasAccount')}</p>
			<button
				onclick={() => goto('/login')}
				class="mt-2 text-red-600 font-bold text-sm hover:underline flex items-center justify-center gap-1 mx-auto cursor-pointer"
			>
				{$t('auth.register.signIn')}
			</button>
		</div>
	{/snippet}
</AuthLayout>
