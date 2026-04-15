<script lang="ts">
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { formatDate } from '$lib/i18n';
	import { Calendar } from 'lucide-svelte';

	interface Props {
		firstDate: string | undefined;
		lastDate: string | undefined;
	}

	let { firstDate, lastDate }: Props = $props();

	const { t } = useTranslation();
</script>

<div class="bg-white dark:bg-zinc-900 border border-gray-100 dark:border-zinc-800 rounded-3xl p-6">
	<h3 class="font-bold text-gray-900 dark:text-white mb-6 flex items-center gap-2">
		<Calendar class="w-5 h-5 text-purple-600" />
		{t('theater.setlists.timeline')}
	</h3>

	<div
		class="relative pl-6 space-y-8 border-l-2 border-dashed border-gray-200 dark:border-zinc-700 ml-2"
	>
		<!-- First -->
		<div class="relative">
			<div
				class="absolute -left-[31px] w-4 h-4 rounded-full bg-green-100 dark:bg-green-900/30 border-2 border-green-500"
			></div>
			<p class="text-xs font-bold text-green-600 dark:text-green-400 uppercase tracking-wider mb-1">
				{t('theater.setlists.firstShow')}
			</p>
			<p class="font-bold text-gray-900 dark:text-white">
				{firstDate
					? formatDate(firstDate, { day: 'numeric', month: 'long', year: 'numeric' })
					: '-'}
			</p>
		</div>

		<!-- Last -->
		<div class="relative">
			<div
				class="absolute -left-[31px] w-4 h-4 rounded-full bg-blue-100 dark:bg-blue-900/30 border-2 border-blue-500"
			></div>
			<p class="text-xs font-bold text-blue-600 dark:text-blue-400 uppercase tracking-wider mb-1">
				{t('theater.setlists.latestShow')}
			</p>
			<p class="font-bold text-gray-900 dark:text-white">
				{lastDate ? formatDate(lastDate, { day: 'numeric', month: 'long', year: 'numeric' }) : '-'}
			</p>
		</div>
	</div>
</div>
