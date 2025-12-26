<script lang="ts">
	import { goto } from '$app/navigation';
	import { auth } from '$lib/apis/auth';
	import { showToast } from '$lib/stores';
	import { Mail, ArrowLeft, Loader2, KeyRound } from 'lucide-svelte';

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
			showToast('Reset link sent! Check your email.', 'success');
		} catch (e: any) {
			console.error(e);
			if (e.detail && typeof e.detail === 'string') {
				error = e.detail;
			} else if (e.message) {
				error = e.message;
			} else {
				error = 'Failed to send reset link. Please try again.';
			}
			showToast(error || 'Error sending link', 'error');
		} finally {
			isLoading = false;
		}
	};
</script>

<div class="min-h-screen flex items-center justify-center p-4 bg-gray-50 relative overflow-hidden">
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
			class="inline-flex items-center gap-2 text-sm font-bold text-gray-500 hover:text-gray-900 mb-6 transition-colors"
		>
			<ArrowLeft class="w-4 h-4" /> Back to Login
		</a>

		<div
			class="bg-white/80 backdrop-blur-xl p-8 rounded-3xl shadow-2xl border border-white/60 animate-fade-in"
		>
			<div class="text-center mb-8">
				<div
					class="w-16 h-16 rounded-full bg-red-50 flex items-center justify-center mx-auto mb-4 text-red-500"
				>
					<KeyRound class="w-8 h-8" />
				</div>
				<h1 class="text-2xl font-black text-gray-900 mb-2">Forgot Password?</h1>
				<p class="text-gray-500 font-medium text-sm">
					{#if isSent}
						We've sent a password reset link to <span class="font-bold text-gray-900">{email}</span
						>. Please check your inbox.
					{:else}
						Enter your email address and we'll send you a link to reset your password.
					{/if}
				</p>
			</div>

			{#if !isSent}
				<form on:submit|preventDefault={handleSubmit} class="space-y-6">
					<div>
						<label class="block text-xs font-bold text-gray-500 mb-1.5 ml-1">Email Address</label>
						<div class="relative">
							<div class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">
								<Mail class="w-5 h-5" />
							</div>
							<input
								type="email"
								required
								bind:value={email}
								class="w-full pl-12 pr-4 py-3.5 bg-white/80 border border-gray-200 rounded-xl focus:ring-2 focus:ring-red-500 focus:border-red-500 outline-none font-medium text-gray-900 transition-all placeholder-gray-400"
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
							<Loader2 class="w-5 h-5 animate-spin" /> Sending...
						{:else}
							Send Reset Link
						{/if}
					</button>
				</form>
			{:else}
				<div class="space-y-4">
					<button
						on:click={() => (isSent = false)}
						class="w-full py-4 rounded-2xl font-bold text-gray-700 bg-gray-100 hover:bg-gray-200 transition-all"
					>
						Try another email
					</button>
					<p class="text-xs text-gray-400 text-center">
						Didn't receive the email? Check your spam folder or try again.
					</p>
				</div>
			{/if}
		</div>
	</div>
</div>
