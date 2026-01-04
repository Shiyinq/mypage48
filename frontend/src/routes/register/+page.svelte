<script lang="ts">
	import { goto } from '$app/navigation';
	import { showToast } from '$lib/stores';
	import { Lock, Mail, User, Hash, CheckCircle, Crown, Shield } from 'lucide-svelte';
	import { auth } from '$lib/apis/auth';
	import type { RegisterRequest } from '$lib/types';
	import SEO from '$lib/components/SEO.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import AuthLayout from '$lib/components/layouts/AuthLayout.svelte';

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

	const handleSubmit = async () => {
		if (formData.password !== formData.confirmPassword) {
			error = $t('auth.register.passwordsMismatch');
			return;
		}

		isLoading = true;
		error = null;

		try {
			await auth.register(formData);
			showToast($t('auth.register.success'), 'success');

			// Optional: delay redirect to let them read the message, or move them to login immediately
			setTimeout(() => {
				goto('/login');
			}, 2000);
		} catch (err) {
			const e = err as { detail?: string | string[]; message?: string };
			console.error(e);
			if (e.detail && typeof e.detail === 'string') {
				error = e.detail;
			} else if (e.message) {
				error = e.message;
			} else {
				error = $t('auth.register.failed');
			}
		} finally {
			isLoading = false;
		}
	};
</script>

<SEO title={$t('auth.register.title')} path="/register" description={$t('seo.register')} />

<AuthLayout title={$t('auth.register.title')} subtitle={$t('auth.register.subtitle')}>
	<form on:submit|preventDefault={handleSubmit} class="space-y-4">
		<div class="grid grid-cols-2 gap-4">
			<div>
				<label
					for="memberId"
					class="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-1.5 ml-1"
					>{$t('auth.register.memberId')}</label
				>
				<div class="relative">
					<div class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 dark:text-zinc-500">
						<Hash class="w-4 h-4" />
					</div>
					<input
						id="memberId"
						name="memberId"
						required
						bind:value={formData.memberId}
						class="w-full pl-9 pr-3 py-3 bg-white/80 dark:bg-zinc-800/50 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-2 focus:ring-red-500 outline-none font-medium text-gray-900 dark:text-white text-sm placeholder-gray-400 dark:placeholder-zinc-600"
						placeholder="JKT-XXXX"
					/>
				</div>
			</div>
			<div>
				<label
					for="username"
					class="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-1.5 ml-1"
					>{$t('auth.register.username')}</label
				>
				<div class="relative">
					<div class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 dark:text-zinc-500">
						<User class="w-4 h-4" />
					</div>
					<input
						id="username"
						name="username"
						required
						bind:value={formData.username}
						class="w-full pl-9 pr-3 py-3 bg-white/80 dark:bg-zinc-800/50 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-2 focus:ring-red-500 outline-none font-medium text-gray-900 dark:text-white text-sm placeholder-gray-400 dark:placeholder-zinc-600"
						placeholder="@username"
					/>
				</div>
			</div>
		</div>

		<div>
			<label
				for="fullName"
				class="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-1.5 ml-1"
				>{$t('auth.register.fullName')}</label
			>
			<input
				id="fullName"
				name="fullName"
				required
				bind:value={formData.fullName}
				class="w-full px-4 py-3 bg-white/80 dark:bg-zinc-800/50 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-2 focus:ring-red-500 outline-none font-medium text-gray-900 dark:text-white text-sm placeholder-gray-400 dark:placeholder-zinc-600"
				placeholder="e.g. Catherina Vallencia"
			/>
		</div>

		<div>
			<label
				for="email"
				class="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-1.5 ml-1"
				>{$t('auth.register.email')}</label
			>
			<div class="relative">
				<div class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 dark:text-zinc-500">
					<Mail class="w-4 h-4" />
				</div>
				<input
					type="email"
					id="email"
					name="email"
					required
					bind:value={formData.email}
					class="w-full pl-9 pr-3 py-3 bg-white/80 dark:bg-zinc-800/50 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-2 focus:ring-red-500 outline-none font-medium text-gray-900 dark:text-white text-sm placeholder-gray-400 dark:placeholder-zinc-600"
					placeholder="name@example.com"
				/>
			</div>
		</div>

		<div>
			<label
				for="ofcStatus"
				class="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-1.5 ml-1"
				>{$t('auth.register.ofcStatus')}</label
			>
			<div class="relative">
				<div class="absolute left-3 top-1/2 -translate-y-1/2 text-red-500">
					<Crown class="w-4 h-4" />
				</div>
				<select
					id="ofcStatus"
					name="ofcStatus"
					bind:value={formData.ofcStatus}
					class="w-full pl-9 pr-3 py-3 bg-white/80 dark:bg-zinc-800/50 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-2 focus:ring-red-500 outline-none font-medium text-gray-900 dark:text-white text-sm appearance-none cursor-pointer"
				>
					<option value="Active">{$t('auth.register.ofcActive')}</option>
					<option value="Inactive">{$t('auth.register.ofcInactive')}</option>
					<option value="Pending">{$t('auth.register.pendingRenewal')}</option>
				</select>
				<div class="absolute right-3 top-1/2 -translate-y-1/2">
					<CheckCircle class="w-4 h-4 text-green-500" />
				</div>
			</div>
		</div>

		<div class="grid md:grid-cols-2 gap-4">
			<div>
				<label
					for="password"
					class="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-1.5 ml-1"
					>{$t('auth.register.password')}</label
				>
				<div class="relative">
					<div class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 dark:text-zinc-500">
						<Lock class="w-4 h-4" />
					</div>
					<input
						type="password"
						id="password"
						name="password"
						required
						bind:value={formData.password}
						class="w-full pl-9 pr-3 py-3 bg-white/80 dark:bg-zinc-800/50 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-2 focus:ring-red-500 outline-none font-medium text-gray-900 dark:text-white text-sm placeholder-gray-400 dark:placeholder-zinc-600"
						placeholder="••••••••"
					/>
				</div>
			</div>
			<div>
				<label
					for="confirmPassword"
					class="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-1.5 ml-1"
					>{$t('auth.register.confirmPassword')}</label
				>
				<div class="relative">
					<div class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 dark:text-zinc-500">
						<Shield class="w-4 h-4" />
					</div>
					<input
						type="password"
						id="confirmPassword"
						name="confirmPassword"
						required
						bind:value={formData.confirmPassword}
						class={`w-full pl-9 pr-3 py-3 bg-white/80 dark:bg-zinc-800/50 border rounded-xl focus:ring-2 focus:ring-red-500 outline-none font-medium text-gray-900 dark:text-white text-sm ${error ? 'border-red-500 bg-red-50 dark:bg-red-900/20' : 'border-gray-200 dark:border-zinc-700'} placeholder-gray-400 dark:placeholder-zinc-600`}
						placeholder="••••••••"
					/>
				</div>
			</div>
		</div>

		{#if error}
			<p
				class="text-xs text-red-600 dark:text-red-400 font-bold text-center bg-red-50 dark:bg-red-900/20 p-2 rounded-lg border border-red-100 dark:border-red-800"
			>
				{error}
			</p>
		{/if}

		<button
			type="submit"
			disabled={isLoading}
			class="w-full idol-gradient text-white py-4 rounded-2xl font-bold text-lg shadow-lg shadow-red-200 hover:shadow-xl hover:scale-[1.02] transition-all active:scale-95 flex items-center justify-center gap-2 mt-4 disabled:opacity-70 disabled:cursor-not-allowed cursor-pointer"
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
