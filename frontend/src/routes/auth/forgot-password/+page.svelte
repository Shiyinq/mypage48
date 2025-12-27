<script lang="ts">
	import { goto } from '$app/navigation';
	import { auth } from '$lib/apis/auth';
	import { showToast } from '$lib/stores';
	import { Mail, ArrowLeft, Loader2, KeyRound } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	const { t } = useTranslation();

	let email = '';
	let isLoading = false;
	let isSent = false;
	let error: string | null = null;

	const handleSubmit = async () => {
		isLoading = true;
		error = null;

		try {
			await auth.forgotPassword({ email });
			isSent = true;
			showToast($t('auth.forgotPassword.sent'), 'success');
		} catch (e: any) {
			console.error(e);
			if (e.detail && typeof e.detail === 'string') {
				error = e.detail;
			} else if (e.message) {
				error = e.message;
			} else {
				error = $t('auth.forgotPassword.failed');
			}
			showToast(error || $t('auth.forgotPassword.error'), 'error');
		} finally {
			isLoading = false;
		}
	};
</script>

<div
	class="min-h-screen flex items-center justify-center p-4 bg-gray-50 dark:bg-zinc-950 relative overflow-hidden"
>
	<!-- Background decorations -->
	<div class="absolute top-0 left-0 w-full h-full overflow-hidden -z-10">
		<div
			class="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-blue-500/10 blur-[100px] animate-pulse"
		></div>
		<div
			class="absolute bottom-[-10%] right-[-20%] w-[50%] h-[50%] rounded-full bg-purple-500/10 blur-[100px] animate-pulse"
		></div>
	</div>

	<div class="w-full max-w-md">
		<a
			href="/login"
			class="inline-flex items-center gap-2 text-sm font-bold text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white mb-6 transition-colors"
		>
			<ArrowLeft class="w-4 h-4" />
			{$t('auth.forgotPassword.backToLogin')}
		</a>

		<div
			class="bg-white/80 dark:bg-zinc-900/80 backdrop-blur-xl p-8 rounded-3xl shadow-2xl border border-white/60 dark:border-zinc-800 animate-fade-in"
		>
			<div class="text-center mb-8">
				<div
					class="w-16 h-16 rounded-full bg-red-50 dark:bg-red-900/20 flex items-center justify-center mx-auto mb-4 text-red-500 dark:text-red-400"
				>
					<KeyRound class="w-8 h-8" />
				</div>
				<h1 class="text-2xl font-black text-gray-900 dark:text-white mb-2">
					{$t('auth.forgotPassword.title')}
				</h1>
				<p class="text-gray-500 dark:text-gray-400 font-medium text-sm">
					{#if isSent}
						{$t('auth.forgotPassword.successMessage', { email })}
					{:else}
						{$t('auth.forgotPassword.instruction')}
					{/if}
				</p>
			</div>

			{#if !isSent}
				<form on:submit|preventDefault={handleSubmit} class="space-y-6">
					<div>
						<label class="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-1.5 ml-1"
							>{$t('auth.forgotPassword.emailLabel')}</label
						>
						<div class="relative">
							<div
								class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 dark:text-zinc-500"
							>
								<Mail class="w-5 h-5" />
							</div>
							<input
								type="email"
								required
								bind:value={email}
								class="w-full pl-12 pr-4 py-3.5 bg-white/80 dark:bg-zinc-800/50 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none font-medium text-gray-900 dark:text-white transition-all placeholder-gray-400 dark:placeholder-zinc-600"
								placeholder="member@mypage48.com"
							/>
						</div>
						{#if error}
							<p class="text-xs text-red-600 font-bold mt-2 ml-1">{error}</p>
						{/if}
					</div>

					<button
						type="submit"
						disabled={isLoading}
						class="w-full idol-gradient text-white py-4 rounded-2xl font-bold text-lg shadow-lg shadow-red-200 hover:shadow-xl hover:scale-[1.02] transition-all active:scale-95 flex items-center justify-center gap-2 disabled:opacity-70"
					>
						{#if isLoading}
							<Loader2 class="w-5 h-5 animate-spin" /> {$t('auth.forgotPassword.submitting')}
						{:else}
							{$t('auth.forgotPassword.submit')}
						{/if}
					</button>
				</form>
			{:else}
				<div class="space-y-4">
					<button
						on:click={() => (isSent = false)}
						class="w-full py-4 rounded-2xl font-bold text-gray-700 dark:text-gray-200 bg-gray-100 dark:bg-zinc-800 hover:bg-gray-200 dark:hover:bg-zinc-700 transition-all"
					>
						{$t('auth.forgotPassword.tryAnother')}
					</button>
					<p class="text-xs text-gray-400 text-center">
						{$t('auth.forgotPassword.spamCheck')}
					</p>
				</div>
			{/if}
		</div>
	</div>
</div>
