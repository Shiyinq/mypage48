<script lang="ts">
	export let params: Record<string, string> | undefined = undefined;
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { showToast } from '$lib/stores';
	import { logger } from '$lib/utils/logger';
	import { getErrorMessage } from '$lib/utils/api';
	import { authStore } from '$lib/stores/auth';
	import { Lock, Mail, User, Hash, CircleCheck, Crown, Shield } from 'lucide-svelte';
	import type { RegisterRequest } from '$lib/types';
	import SEO from '$lib/components/SEO.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import AuthLayout from '$lib/components/layouts/AuthLayout.svelte';

	import PasswordStrengthChecklist from '$lib/components/auth/PasswordStrengthChecklist.svelte';
	import { registerSchema, registerBaseSchema } from '$lib/schemas/auth';
	import { ZodError } from 'zod';

	const { t } = useTranslation();

	let formData: RegisterRequest = {
		memberId: '',
		username: '',
		fullName: '',
		email: '',
		ofcStatus: 'Active',
		password: '',
		confirmPassword: ''
	};

	let isLoading = false;
	let error: string | null = null;
	let errors: Record<string, string> = {};

	$: isValid =
		Object.values(formData).every((val) => val.length > 0) &&
		Object.values(errors).every((e) => !e);

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

			// @ts-ignore - pick is valid on z.object
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

<AuthLayout title={$t('auth.register.title')} subtitle={$t('auth.register.subtitle')}>
	<form on:submit|preventDefault={handleSubmit} class="space-y-3" novalidate>
		<div class="grid grid-cols-2 gap-3">
			<div>
				<label
					for="memberId"
					class="block text-[10px] uppercase tracking-wider font-bold text-gray-500 dark:text-gray-400 mb-0.5 ml-1"
					>{$t('auth.register.memberId')}</label
				>
				<div class="relative">
					<div class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 dark:text-zinc-500">
						<Hash class="w-3.5 h-3.5" />
					</div>
					<input
						id="memberId"
						name="memberId"
						bind:value={formData.memberId}
						on:input={() => validateField('memberId')}
						class={`w-full pl-8 pr-3 py-2 bg-white/80 dark:bg-zinc-800/50 border rounded-lg focus:ring-2 focus:ring-red-500 outline-none font-medium text-gray-900 dark:text-white text-sm placeholder-gray-400 dark:placeholder-zinc-600 ${errors.memberId ? 'border-red-500' : 'border-gray-200 dark:border-zinc-700'}`}
						placeholder="JKT-XXXX"
					/>
				</div>
				{#if errors.memberId}
					<p class="text-[10px] text-red-500 mt-0.5 ml-1 font-medium">{errors.memberId}</p>
				{/if}
			</div>
			<div>
				<label
					for="username"
					class="block text-[10px] uppercase tracking-wider font-bold text-gray-500 dark:text-gray-400 mb-0.5 ml-1"
					>{$t('auth.register.username')}</label
				>
				<div class="relative">
					<div class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 dark:text-zinc-500">
						<User class="w-3.5 h-3.5" />
					</div>
					<input
						id="username"
						name="username"
						bind:value={formData.username}
						on:input={() => validateField('username')}
						class={`w-full pl-8 pr-3 py-2 bg-white/80 dark:bg-zinc-800/50 border rounded-lg focus:ring-2 focus:ring-red-500 outline-none font-medium text-gray-900 dark:text-white text-sm placeholder-gray-400 dark:placeholder-zinc-600 ${errors.username ? 'border-red-500' : 'border-gray-200 dark:border-zinc-700'}`}
						placeholder="@username"
					/>
				</div>
				{#if errors.username}
					<p class="text-[10px] text-red-500 mt-0.5 ml-1 font-medium">{errors.username}</p>
				{/if}
			</div>
		</div>

		<div class="grid grid-cols-2 gap-3">
			<div>
				<label
					for="fullName"
					class="block text-[10px] uppercase tracking-wider font-bold text-gray-500 dark:text-gray-400 mb-0.5 ml-1"
					>{$t('auth.register.fullName')}</label
				>
				<input
					id="fullName"
					name="fullName"
					bind:value={formData.fullName}
					on:input={() => validateField('fullName')}
					class={`w-full px-3 py-2 bg-white/80 dark:bg-zinc-800/50 border rounded-lg focus:ring-2 focus:ring-red-500 outline-none font-medium text-gray-900 dark:text-white text-sm placeholder-gray-400 dark:placeholder-zinc-600 ${errors.fullName ? 'border-red-500' : 'border-gray-200 dark:border-zinc-700'}`}
					placeholder="Name"
				/>
				{#if errors.fullName}
					<p class="text-[10px] text-red-500 mt-0.5 ml-1 font-medium">{errors.fullName}</p>
				{/if}
			</div>
			<div>
				<label
					for="email"
					class="block text-[10px] uppercase tracking-wider font-bold text-gray-500 dark:text-gray-400 mb-0.5 ml-1"
					>{$t('auth.register.email')}</label
				>
				<div class="relative">
					<div class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 dark:text-zinc-500">
						<Mail class="w-3.5 h-3.5" />
					</div>
					<input
						type="email"
						id="email"
						name="email"
						bind:value={formData.email}
						on:input={() => validateField('email')}
						class={`w-full pl-8 pr-3 py-2 bg-white/80 dark:bg-zinc-800/50 border rounded-lg focus:ring-2 focus:ring-red-500 outline-none font-medium text-gray-900 dark:text-white text-sm placeholder-gray-400 dark:placeholder-zinc-600 ${errors.email ? 'border-red-500' : 'border-gray-200 dark:border-zinc-700'}`}
						placeholder="Email"
					/>
				</div>
				{#if errors.email}
					<p class="text-[10px] text-red-500 mt-0.5 ml-1 font-medium">{errors.email}</p>
				{/if}
			</div>
		</div>

		<div>
			<label
				for="ofcStatus"
				class="block text-[10px] uppercase tracking-wider font-bold text-gray-500 dark:text-gray-400 mb-0.5 ml-1"
				>{$t('auth.register.ofcStatus')}</label
			>
			<div class="relative">
				<div class="absolute left-3 top-1/2 -translate-y-1/2 text-red-500">
					<Crown class="w-3.5 h-3.5" />
				</div>
				<select
					id="ofcStatus"
					name="ofcStatus"
					bind:value={formData.ofcStatus}
					class="w-full pl-8 pr-3 py-2 bg-white/80 dark:bg-zinc-800/50 border border-gray-200 dark:border-zinc-700 rounded-lg focus:ring-2 focus:ring-red-500 outline-none font-medium text-gray-900 dark:text-white text-sm appearance-none cursor-pointer"
				>
					<option value="Active">{$t('auth.register.ofcActive')}</option>
					<option value="Inactive">{$t('auth.register.ofcInactive')}</option>
					<option value="Pending">{$t('auth.register.pendingRenewal')}</option>
				</select>
				<div class="absolute right-3 top-1/2 -translate-y-1/2">
					<CircleCheck class="w-3.5 h-3.5 text-green-500" />
				</div>
			</div>
		</div>

		<div class="grid grid-cols-2 gap-3">
			<div>
				<label
					for="password"
					class="block text-[10px] uppercase tracking-wider font-bold text-gray-500 dark:text-gray-400 mb-0.5 ml-1"
					>{$t('auth.register.password')}</label
				>
				<div class="relative">
					<div class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 dark:text-zinc-500">
						<Lock class="w-3.5 h-3.5" />
					</div>
					<input
						type="password"
						id="password"
						name="password"
						bind:value={formData.password}
						on:input={() => validateField('password')}
						class={`w-full pl-8 pr-3 py-2 bg-white/80 dark:bg-zinc-800/50 border rounded-lg focus:ring-2 focus:ring-red-500 outline-none font-medium text-gray-900 dark:text-white text-sm placeholder-gray-400 dark:placeholder-zinc-600 ${errors.password ? 'border-red-500' : 'border-gray-200 dark:border-zinc-700'}`}
						placeholder="••••••••"
					/>
				</div>
			</div>
			<div>
				<label
					for="confirmPassword"
					class="block text-[10px] uppercase tracking-wider font-bold text-gray-500 dark:text-gray-400 mb-0.5 ml-1"
					>{$t('auth.register.confirmPassword')}</label
				>
				<div class="relative">
					<div class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 dark:text-zinc-500">
						<Shield class="w-3.5 h-3.5" />
					</div>
					<input
						type="password"
						id="confirmPassword"
						name="confirmPassword"
						bind:value={formData.confirmPassword}
						on:input={() => validateField('confirmPassword')}
						class={`w-full pl-8 pr-3 py-2 bg-white/80 dark:bg-zinc-800/50 border rounded-lg focus:ring-2 focus:ring-red-500 outline-none font-medium text-gray-900 dark:text-white text-sm placeholder-gray-400 dark:placeholder-zinc-600 ${errors.confirmPassword ? 'border-red-500' : 'border-gray-200 dark:border-zinc-700'}`}
						placeholder="••••••••"
					/>
				</div>
			</div>
		</div>

		<PasswordStrengthChecklist password={formData.password} />
		{#if errors.password}
			<p class="text-[10px] text-red-500 mt-0.5 ml-1 font-medium text-center">{errors.password}</p>
		{/if}
		{#if errors.confirmPassword}
			<p class="text-[10px] text-red-500 mt-0.5 ml-1 font-medium text-center">
				{errors.confirmPassword}
			</p>
		{/if}

		{#if error}
			<p
				class="text-[10px] text-red-600 dark:text-red-400 font-bold text-center bg-red-50 dark:bg-red-900/20 p-1.5 rounded-lg border border-red-100 dark:border-red-800"
			>
				{error}
			</p>
		{/if}

		<button
			type="submit"
			disabled={isLoading || !isValid}
			class="w-full idol-gradient text-white py-2.5 rounded-xl font-bold text-base shadow-lg shadow-red-200 hover:shadow-xl hover:scale-[1.02] transition-all active:scale-95 flex items-center justify-center gap-2 mt-2 disabled:opacity-70 disabled:cursor-not-allowed cursor-pointer"
		>
			{#if isLoading}
				{$t('auth.register.submitting')}
			{:else}
				{$t('auth.register.submit')}
			{/if}
		</button>
	</form>

	<div slot="footer">
		<p class="text-sm text-gray-500 dark:text-gray-400">{$t('auth.register.hasAccount')}</p>
		<button
			on:click={() => goto('/login')}
			class="mt-2 text-red-600 font-bold text-sm hover:underline flex items-center justify-center gap-1 mx-auto cursor-pointer"
		>
			{$t('auth.register.signIn')}
		</button>
	</div>
</AuthLayout>
