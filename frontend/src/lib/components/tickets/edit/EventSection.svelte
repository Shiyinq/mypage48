<script lang="ts">
	import { Ticket as TicketIcon, Calendar, Clock } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SetlistSelector from '$lib/components/SetlistSelector.svelte';

	interface Props {
		title: string;
		date: string;
		time: string;
	}

	let { title = $bindable(), date = $bindable(), time = $bindable() }: Props = $props();

	const { t } = useTranslation();
</script>

<div class="space-y-4">
	<h3
		class="text-xs font-black text-gray-400 dark:text-gray-500 uppercase tracking-widest mb-4 flex items-center gap-2"
	>
		<TicketIcon class="w-4 h-4" />
		{t('forms.eventDetails')}
	</h3>

	<div>
		<label
			class="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-1.5 ml-1"
			for="event-title">{t('forms.showTitle')}</label
		>
		<SetlistSelector
			id="event-title"
			bind:value={title}
			placeholder={t('forms.showTitlePlaceholder')}
		/>
	</div>

	<div class="grid grid-cols-2 gap-4">
		<div>
			<label
				class="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-1.5 ml-1"
				for="event-date">{t('forms.date')}</label
			>
			<div class="relative">
				<div class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
					<Calendar class="w-4 h-4" />
				</div>
				<input
					id="event-date"
					type="date"
					bind:value={date}
					class="w-full pl-9 pr-3 py-3 bg-gray-50 dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-red-500 outline-none text-sm font-medium text-gray-900 dark:text-gray-100"
				/>
			</div>
		</div>
		<div>
			<label
				class="block text-xs font-bold text-gray-500 dark:text-gray-400 mb-1.5 ml-1"
				for="event-time">{t('forms.showTime')}</label
			>
			<div class="relative">
				<div class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
					<Clock class="w-4 h-4" />
				</div>
				<input
					id="event-time"
					type="time"
					bind:value={time}
					class="w-full pl-9 pr-3 py-3 bg-gray-50 dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-red-500 outline-none text-sm font-medium text-gray-900 dark:text-gray-100"
				/>
			</div>
		</div>
	</div>
</div>
