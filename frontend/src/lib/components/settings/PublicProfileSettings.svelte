<script lang="ts">
	import { Image as ImageIcon, ExternalLink } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { userProfile } from '$lib/stores/profile.svelte';

	const { t } = useTranslation();

	let shareUrl = $state('');

	$effect(() => {
		if (typeof window !== 'undefined' && userProfile.data?.username) {
			shareUrl = `${window.location.origin}/profile/${userProfile.data.username}`;
		}
	});

	function copyToClipboard() {
		navigator.clipboard.writeText(shareUrl);
	}
</script>

<div class="space-y-6">
	<div class="flex items-center gap-3 mb-2">
		<div class="p-2 bg-pink-100 dark:bg-pink-900/30 rounded-lg text-pink-600">
			<ImageIcon class="w-5 h-5" />
		</div>
		<div>
			<h3 class="text-lg font-bold text-slate-900 dark:text-white">
				{$t('settings.profile.publicProfile')}
			</h3>
			<p class="text-sm text-slate-500 dark:text-slate-400">
				{$t('settings.profile.publicProfileDesc')}
			</p>
		</div>
	</div>

	{#if userProfile.data?.username}
		<div class="glass-panel p-6 rounded-2xl border-themed space-y-4">
			<div class="flex items-center justify-between">
				<span class="text-sm font-medium text-slate-500 dark:text-slate-400">
					{$t('settings.profile.profileUrl')}
				</span>
				<a
					href={shareUrl}
					target="_blank"
					class="text-xs font-bold text-pink-600 hover:text-pink-500 flex items-center gap-1 transition-colors"
				>
					{$t('settings.profile.viewProfile')}
					<ExternalLink class="w-3 h-3" />
				</a>
			</div>

			<div class="flex items-center gap-2">
				<div
					class="flex-1 px-4 py-3 bg-slate-50 dark:bg-zinc-800/50 rounded-xl border border-slate-100 dark:border-white/5 font-mono text-sm text-slate-600 dark:text-slate-300 truncate"
				>
					{shareUrl}
				</div>
				<button
					onclick={copyToClipboard}
					class="px-4 py-3 bg-slate-900 dark:bg-white text-white dark:text-slate-900 rounded-xl text-sm font-bold hover:bg-black dark:hover:bg-slate-200 transition-all active:scale-95 cursor-pointer"
				>
					{$t('common.copy')}
				</button>
			</div>
		</div>
	{:else}
		<div
			class="glass-panel p-6 rounded-2xl border-themed text-center space-y-2 opacity-60 grayscale bg-slate-50/50 dark:bg-zinc-800/20"
		>
			<p class="text-sm font-bold text-slate-900 dark:text-white">
				{$t('settings.profile.usernameRequired')}
			</p>
			<p class="text-xs text-slate-500 dark:text-slate-400">
				{$t('settings.profile.usernameRequiredDesc')}
			</p>
		</div>
	{/if}
</div>
