<script lang="ts">
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { History, LogIn, UserPlus } from 'lucide-svelte';
	import { EmptyState } from '$lib/components';
	import SEO from '$lib/components/SEO.svelte';
	import AppBackground from '$lib/components/common/AppBackground.svelte';

	const { t } = useTranslation();
</script>

<SEO
	title={t('liveHistory.publicWatchedEmptyTitle')}
	path="/jkt48/live/history/watched"
	description={t('liveHistory.publicWatchedEmptyDesc')}
/>

<AppBackground hideDecorationsOnMobile={true} />
<div class="h-full w-full overflow-y-auto py-8 px-4 sm:px-6 lg:px-8 pb-28">
	<div class="max-w-7xl mx-auto w-full h-full flex items-center justify-center pt-20">
		<EmptyState
			icon={History}
			title={t('liveHistory.publicWatchedEmptyTitle')}
			description={t('liveHistory.publicWatchedEmptyDesc')}
			className="max-w-md mx-auto"
		>
			<div class="mt-8 flex flex-col sm:flex-row gap-4 w-full sm:w-auto">
				<a
					href="/login"
					class="flex-1 sm:flex-none flex items-center justify-center gap-2 px-6 py-3 bg-slate-900 dark:bg-white text-white dark:text-zinc-950 font-bold rounded-xl hover:bg-slate-800 dark:hover:bg-slate-100 transition-colors"
				>
					<LogIn size={18} />
					<span>{t('liveHistory.loginToWatch')}</span>
				</a>
				<a
					href="/register"
					class="flex-1 sm:flex-none flex items-center justify-center gap-2 px-6 py-3 bg-red-600 text-white font-bold rounded-xl hover:bg-red-700 transition-colors"
				>
					<UserPlus size={18} />
					<span>{t('liveHistory.registerToWatch')}</span>
				</a>
			</div>
		</EmptyState>
	</div>
</div>
