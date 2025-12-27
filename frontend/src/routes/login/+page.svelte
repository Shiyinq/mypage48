<script lang="ts">
	import { goto } from '$app/navigation';
	import { isAuthenticated, showToast } from '$lib/stores';
	import { Ticket, Lock, Mail, ArrowRight, User } from 'lucide-svelte';
	import { auth } from '$lib/apis/auth';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';

	const { t } = useTranslation();

	let email = '';
	let password = '';
	let isLoading = false;
	let error: string | null = null;

	const handleSubmit = async () => {
		isLoading = true;
		error = null;
		try {
			// Backend expects 'username' field, which can be email or username
			await auth.login({ username: email, password });
			isAuthenticated.set(true);
			showToast($t('auth.login.welcomeBack'));
			goto('/');
		} catch (e: any) {
			console.error(e);
			// status = 'error'; // ensure local status variable matches if used

			if (e.detail && typeof e.detail === 'string') {
				error = e.detail;
			} else if (e.message) {
				error = e.message;
			} else {
				error = $t('auth.login.invalidCredentials');
			}

			// Show toast for better visibility
			showToast(error || $t('common.error'), 'error');
		} finally {
			isLoading = false;
		}
	};
</script>

<SEO title={$t('auth.login.title')} path="/login" description={$t('seo.login')} />

<div class="min-h-screen flex items-center justify-center p-4 relative overflow-hidden">
	<div class="absolute top-0 left-0 w-full h-full overflow-hidden -z-10">
		<div
			class="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-red-500/20 blur-[100px] animate-pulse"
		></div>
		<div
			class="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-purple-500/20 blur-[100px] animate-pulse"
		></div>
	</div>

	<div class="w-full max-w-md">
		<div class="text-center mb-8 animate-fade-in">
			<div
				class="w-16 h-16 rounded-full idol-gradient flex items-center justify-center text-white shadow-xl mx-auto mb-4 ring-4 ring-white/50 dark:ring-white/10"
			>
				<Ticket class="w-8 h-8" />
			</div>
			<h1 class="text-3xl font-black text-gray-900 dark:text-white tracking-tight">
				MyPage<span class="text-red-600">48</span>
			</h1>
			<p class="text-gray-500 dark:text-gray-400 font-medium mt-2">{$t('auth.login.subtitle')}</p>
		</div>

		<div
			class="glass-panel p-8 rounded-3xl shadow-2xl border border-white/60 dark:border-zinc-800 backdrop-blur-xl animate-[slideUpFade_0.5s_ease-out]"
		>
			<form on:submit|preventDefault={handleSubmit} class="space-y-5">
				<div>
					<label class="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-1.5 ml-1"
						>{$t('auth.login.emailLabel')}</label
					>
					<div class="relative">
						<div class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 dark:text-zinc-500">
							<Mail class="w-5 h-5" />
						</div>
						<input
							type="email"
							required
							bind:value={email}
							class="w-full pl-12 pr-4 py-3.5 bg-white/80 dark:bg-zinc-800/50 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none font-medium text-gray-900 dark:text-white transition-all placeholder-gray-400 dark:placeholder-zinc-600"
							placeholder={$t('auth.login.emailPlaceholder')}
						/>
					</div>
				</div>

				<div>
					<label class="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-1.5 ml-1"
						>{$t('auth.login.passwordLabel')}</label
					>
					<div class="relative">
						<div class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 dark:text-zinc-500">
							<Lock class="w-5 h-5" />
						</div>
						<input
							type="password"
							required
							bind:value={password}
							class="w-full pl-12 pr-4 py-3.5 bg-white/80 dark:bg-zinc-800/50 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none font-medium text-gray-900 dark:text-white transition-all placeholder-gray-400 dark:placeholder-zinc-600"
							placeholder={$t('auth.login.passwordPlaceholder')}
						/>
					</div>
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
					disabled={isLoading}
					class="w-full idol-gradient text-white py-4 rounded-2xl font-bold text-lg shadow-lg shadow-red-200 hover:shadow-xl hover:scale-[1.02] transition-all active:scale-95 flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed"
				>
					{#if isLoading}
						<span class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"
						></span>
					{:else}
						{$t('auth.login.signIn')} <ArrowRight class="w-5 h-5" />
					{/if}
				</button>
			</form>

			<div class="mt-8 pt-6 border-t border-gray-100 dark:border-zinc-800 text-center">
				<p class="text-sm text-gray-500 dark:text-gray-400">{$t('auth.login.noAccount')}</p>
				<button
					on:click={() => goto('/register')}
					class="mt-2 text-red-600 font-bold text-sm hover:underline flex items-center justify-center gap-1 mx-auto"
				>
					{$t('auth.login.registerCta')}
					<User class="w-4 h-4" />
				</button>
			</div>
		</div>
	</div>
</div>
