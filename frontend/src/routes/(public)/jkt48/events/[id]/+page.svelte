<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import type { Member } from '$lib/apis/members';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import { OptimizedImage } from '$lib/components/common';
	import { ErrorState } from '$lib/components';
	import { formatDate } from '$lib/i18n';
	import {
		Calendar,
		Clock,
		Users,
		Cake,
		GraduationCap,
		MoveLeft,
		ChevronDown,
		ExternalLink
	} from 'lucide-svelte';
	import { getMemberFrame } from '$lib/constants';
	import { getTeamColors, getTeamIcon } from '$lib/constants/teamColors';
	import { eventsStore } from '$lib/stores/events.svelte';
	import { membersStore } from '$lib/stores/theater.svelte';
	import DOMPurify from 'isomorphic-dompurify';
	import { proxyExternalImageUrls } from '$lib/utils/media';
	import { MemberDetailModal } from '$lib/components/profile';

	const { t } = useTranslation();

	let eventId = $derived($page.params.id || '');
	let event = $derived(eventsStore.detailCache[eventId]);

	let showMemberDetail = $state(false);
	let selectedMember = $state<Member | null>(null);

	onMount(() => {
		membersStore.load();
	});

	let fullEventMembers = $derived(
		(event?.members || []).map((member) => {
			return (membersStore.list.find((m) => m.id === member.id || m.name === member.name) ||
				member) as Member;
		})
	);

	function openMemberDetail(member: unknown) {
		const m = member as Member;
		const fullMember =
			membersStore.list.find(
				(listMember) => listMember.id === m.id || listMember.name === m.name
			) || m;
		selectedMember = fullMember;
		showMemberDetail = true;
	}

	function closeMemberDetail() {
		showMemberDetail = false;
	}

	let heroImageUrl = $derived.by(() => {
		if (!event) return null;
		if (event.imageUrl) return event.imageUrl;
		if (event.type === 'EXCLUSIVE' && event.raw_data?.detail?.thumbnail_image) {
			return `/proxy/image?url=${encodeURIComponent(event.raw_data.detail.thumbnail_image)}`;
		}
		return null;
	});

	let isError = $state(false);

	$effect(() => {
		if (eventId && !event) {
			isError = false;
			eventsStore.loadDetail(eventId).catch(() => {
				isError = true;
			});
		}
	});

	let contentBody = $derived(
		event?.raw_data?.detail?.content_body
			? DOMPurify.sanitize(proxyExternalImageUrls(event.raw_data.detail.content_body))
			: ''
	);

	let hasSales = $derived(
		event?.raw_data?.detail?.sales_period && event.raw_data.detail.sales_period.length > 0
	);
</script>

{#if isError}
	<div class="max-w-4xl mx-auto pt-10 pb-20 px-4 sm:px-6 md:px-0">
		<ErrorState
			title={t('theater.events.notFound') || '404 Not Found'}
			description={t('theater.events.notFoundDesc') ||
				'Maaf, event yang Anda cari tidak ditemukan atau telah dihapus.'}
			onRetry={() => (window.location.href = '/jkt48/events')}
		/>
	</div>
{:else if event}
	<SEO
		title={event.title}
		path={`/jkt48/events/${event.id}`}
		description={event.title}
		image={heroImageUrl || undefined}
		keywords={`${event.title}, JKT48 Event`}
	/>

	<div class="max-w-4xl mx-auto space-y-6 sm:space-y-8 animate-fade-in pb-20 mt-4 sm:mt-8">
		<!-- Header / Back -->
		<div class="mb-4">
			<a
				href="/jkt48/events"
				class="inline-flex items-center gap-2 text-sm font-bold text-slate-400 hover:text-red-500 transition-colors group"
			>
				<MoveLeft class="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
				{t('common.back') || 'Back'}
			</a>
		</div>

		{#snippet heroContent({ isDarkText = false }: { isDarkText?: boolean })}
			<div class="flex flex-wrap items-center gap-3 mb-4">
				{#if event.type && event.type !== event.label}
					{@const typeColors = getTeamColors(event.type)}
					{@const TypeIcon = getTeamIcon(event.type)}
					<span
						class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest shadow-sm"
						style="background-color: {typeColors.badgeBg}20; color: {typeColors.badgeText}; border: 1px solid {typeColors.badgeBorder}40;"
					>
						{#if TypeIcon}<TypeIcon class="w-3.5 h-3.5" strokeWidth={3} />{/if}
						{event.type}
					</span>
				{/if}
				{#if event.label}
					{@const Icon = getTeamIcon(event.label)}
					{@const colors = getTeamColors(event.label)}
					<span
						class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest shadow-sm"
						style="background-color: {colors.badgeBg}20; color: {colors.badgeText}; border: 1px solid {colors.badgeBorder}40;"
					>
						{#if Icon}<Icon class="w-3.5 h-3.5" strokeWidth={3} />{/if}
						{event.label}
					</span>
				{/if}
			</div>

			<h1
				class="text-3xl md:text-5xl font-black leading-tight uppercase tracking-tight mb-6 {isDarkText
					? 'text-slate-900 dark:text-white'
					: 'text-white drop-shadow-md'}"
			>
				{event.title}
			</h1>

			<!-- Date & Time Row -->
			<div
				class="flex flex-wrap items-center gap-3 md:gap-4 py-4 {isDarkText
					? 'border-y border-slate-200 dark:border-white/10'
					: 'border-t border-white/20'}"
			>
				<div
					class="flex items-center gap-2 font-medium {isDarkText
						? 'text-slate-600 dark:text-slate-300'
						: 'text-white'}"
				>
					<Calendar class="w-4 h-4 {isDarkText ? 'text-red-500' : 'text-white/80'}" />
					<span>
						{formatDate(event.date, {
							weekday: 'long',
							day: 'numeric',
							month: 'long',
							year: 'numeric'
						})}
					</span>
				</div>
				{#if event.raw_data?.detail?.start_time || event.raw_data?.short?.start_time}
					<div
						class="flex items-center gap-2 font-medium {isDarkText
							? 'text-slate-600 dark:text-slate-300'
							: 'text-white'}"
					>
						<Clock class="w-4 h-4 {isDarkText ? 'text-red-500' : 'text-white/80'}" />
						<span>
							{event.raw_data?.detail?.start_time?.slice(0, 5) ||
								event.raw_data?.short?.start_time?.slice(0, 5)}
							{#if event.raw_data?.detail?.end_time || event.raw_data?.short?.end_time}
								- {event.raw_data?.detail?.end_time?.slice(0, 5) ||
									event.raw_data?.short?.end_time?.slice(0, 5)}
							{/if}
							WIB
						</span>
					</div>
				{/if}
			</div>
		{/snippet}

		<!-- Hero Image -->
		{#if heroImageUrl}
			<div
				class="relative w-full aspect-[4/5] sm:aspect-[16/10] md:aspect-video rounded-[2rem] overflow-hidden shadow-2xl bg-slate-100 dark:bg-zinc-800 border border-white/20 dark:border-zinc-700"
			>
				<OptimizedImage
					src={heroImageUrl}
					srcMedium={event.imageUrl_medium}
					srcSmall={event.imageUrl_small}
					blurHash={event.blurHash}
					alt={event.title}
					class="w-full h-full object-cover"
				/>

				<div
					class="absolute inset-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent pointer-events-none z-10"
				></div>
				<div
					class="absolute bottom-0 left-0 right-0 p-6 sm:p-8 md:p-10 z-20 pointer-events-none text-left"
				>
					{@render heroContent({ isDarkText: false })}
				</div>
			</div>
		{:else}
			<div class="pt-2 pb-4">
				{@render heroContent({ isDarkText: true })}
			</div>
		{/if}

		<!-- Content Body -->
		{#if contentBody}
			<div
				class="bg-white/80 dark:bg-zinc-900/80 backdrop-blur-xl border border-white/50 dark:border-zinc-800 rounded-[2rem] p-5 sm:p-8 shadow-sm"
			>
				<h2 class="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-3 mb-6">
					<div class="h-6 w-1.5 bg-red-500 rounded-full"></div>
					{t('theater.events.eventInfo') || 'Event Info'}
				</h2>
				<div
					class="prose prose-sm sm:prose-base dark:prose-invert max-w-none text-slate-700 dark:text-slate-300"
				>
					<!-- eslint-disable-next-line svelte/no-at-html-tags -->
					{@html contentBody}
				</div>
			</div>
		{/if}

		<!-- Exclusive Sessions -->
		{#if event.type === 'EXCLUSIVE' && event.raw_data?.detail?.session && event.raw_data.detail.session.length > 0}
			<div
				class="bg-white/80 dark:bg-zinc-900/80 backdrop-blur-xl border border-white/50 dark:border-zinc-800 rounded-[2rem] p-5 sm:p-8 shadow-sm"
			>
				<div class="flex items-center justify-between mb-6">
					<h2 class="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-3">
						<div class="h-6 w-1.5 bg-red-500 rounded-full"></div>
						{t('theater.events.sessionsAndQuotas')}
					</h2>
					{#if event.raw_data.detail.total_quota !== undefined}
						<div
							class="flex items-center gap-3 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 px-4 py-2 rounded-full text-sm font-bold w-fit"
						>
							{#if event.raw_data.detail.total_quota !== undefined}
								<span
									>{t('theater.events.quota') || 'Quota'} {event.raw_data.detail.total_quota}</span
								>
							{/if}
						</div>
					{/if}
				</div>

				<div class="space-y-4">
					{#each event.raw_data.detail.session as session, i}
						<details
							class="group bg-slate-50 dark:bg-zinc-800/50 rounded-2xl border border-slate-100 dark:border-zinc-700/50 overflow-hidden shadow-sm"
							open={i === 0}
						>
							<summary
								class="p-4 sm:p-5 flex items-center justify-between cursor-pointer list-none select-none hover:bg-slate-100 dark:hover:bg-zinc-700/50 transition-colors [&::-webkit-details-marker]:hidden"
							>
								<div>
									<h4 class="font-bold text-slate-900 dark:text-white">
										{session.label.replace('Sesi', t('theater.events.sessionName') || 'Session')}
									</h4>
									<p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5 font-medium">
										{formatDate(session.date, { day: 'numeric', month: 'short' })} • {session.start_time.substring(
											0,
											5
										)} - {session.end_time.substring(0, 5)}
									</p>
								</div>
								<div
									class="w-8 h-8 flex items-center justify-center rounded-full bg-white dark:bg-zinc-900 shadow-sm border border-slate-100 dark:border-zinc-700 group-open:-rotate-180 transition-transform duration-300 text-slate-500 shrink-0"
								>
									<ChevronDown class="w-4 h-4" />
								</div>
							</summary>

							<div
								class="p-4 sm:p-5 border-t border-slate-100 dark:border-zinc-700/50 bg-white dark:bg-zinc-900/30"
							>
								<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
									{#if session.session_detail && session.session_detail.length > 0}
										{#each session.session_detail as detail}
											<div
												class="flex items-center justify-between p-3 rounded-xl border border-slate-100 dark:border-zinc-800 bg-slate-50/50 dark:bg-zinc-800/20 shadow-sm hover:shadow-md transition-shadow"
											>
												<div class="min-w-0 pr-2">
													<div
														class="text-[11px] font-bold text-slate-500 dark:text-slate-400 mb-0.5 uppercase tracking-wide"
													>
														{detail.label.replace('Jalur', t('theater.events.lane') || 'Lane')}
													</div>
													<div class="font-bold text-sm text-slate-900 dark:text-white truncate">
														{detail.jkt48_member_name}
													</div>
												</div>
												<div class="text-right flex flex-col items-end shrink-0">
													{#if detail.available_quota > 0}
														<span
															class="px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 text-[10px] font-bold rounded uppercase tracking-wider"
														>
															{detail.available_quota}
															{t('theater.events.available') || 'Avail'}
														</span>
													{:else}
														<span
															class="px-2 py-1 bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 text-[10px] font-bold rounded uppercase tracking-wider"
														>
															{t('theater.events.soldOut') || 'Sold Out'}
														</span>
													{/if}
													<div
														class="text-[10px] text-slate-500 dark:text-slate-400 mt-1.5 font-medium"
													>
														{detail.tickets_sold}
														{t('theater.events.sold') || 'Sold'}
													</div>
												</div>
											</div>
										{/each}
									{/if}
								</div>
							</div>
						</details>
					{/each}
				</div>
			</div>
		{/if}

		<!-- Ticket Information -->
		{#if hasSales}
			{@const salesCount = event.raw_data.detail.sales_period.length}
			<div
				class="bg-white/80 dark:bg-zinc-900/80 backdrop-blur-xl border border-white/50 dark:border-zinc-800 rounded-[2rem] p-5 sm:p-8 shadow-sm"
			>
				<div class="flex items-center justify-between mb-6">
					<h2 class="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-3">
						<div class="h-6 w-1.5 bg-red-500 rounded-full"></div>
						{t('theater.events.ticketInfo')}
					</h2>
					{#if event.type === 'EXCLUSIVE' && event.raw_data?.detail?.default_price !== undefined}
						<div
							class="flex items-center gap-3 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 px-4 py-2 rounded-full text-sm font-bold w-fit shrink-0"
						>
							<span>Rp {event.raw_data.detail.default_price.toLocaleString('id-ID')}</span>
						</div>
					{/if}
				</div>

				<div
					class="grid gap-4 items-stretch {salesCount === 1
						? 'grid-cols-1'
						: salesCount === 2
							? 'grid-cols-1 md:grid-cols-2'
							: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3'}"
				>
					{#each event.raw_data.detail.sales_period as sale}
						<div
							class="bg-slate-50 dark:bg-zinc-800/50 rounded-2xl p-5 border border-slate-100 dark:border-zinc-700/50 shadow-sm flex flex-col h-full"
						>
							<div class="flex justify-between items-start mb-4">
								<div>
									<h4 class="font-bold text-base text-slate-900 dark:text-white">
										{sale.label}
									</h4>
									<p
										class="text-xs text-slate-500 dark:text-slate-400 mt-1 uppercase tracking-wider font-semibold"
									>
										{sale.sales_method}
									</p>
								</div>
								<span
									class="px-3 py-1 bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 text-[10px] font-black rounded-full uppercase tracking-wider shrink-0"
								>
									{sale.sales_method === 'RAFFLE'
										? t('theater.events.raffle') || 'Raffle'
										: t('theater.events.firstCome') || 'First Come'}
								</span>
							</div>

							<div
								class="bg-white dark:bg-zinc-900/50 rounded-xl p-3 text-sm flex items-start gap-3 mb-4 shadow-sm border border-slate-100 dark:border-zinc-700/50"
							>
								<Calendar class="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
								<div class="flex flex-col gap-0.5 text-xs text-slate-600 dark:text-slate-300">
									<span class="text-slate-400 dark:text-slate-500 font-medium"
										>{t('theater.events.salesPeriod') || 'Sales Period'}</span
									>
									<span class="font-medium">
										{formatDate(sale.start_date, {
											day: 'numeric',
											month: 'short',
											hour: '2-digit',
											minute: '2-digit'
										})} - {formatDate(sale.end_date, {
											day: 'numeric',
											month: 'short',
											hour: '2-digit',
											minute: '2-digit'
										})}
									</span>
								</div>
							</div>

							{#if event.type !== 'EXCLUSIVE'}
								{#if sale.pricing && sale.pricing.length > 0}
									<div class="space-y-2.5 pt-1 mt-auto">
										{#each sale.pricing as price}
											<div
												class="flex justify-between items-center py-2 border-t border-slate-100 dark:border-zinc-700/50 first:border-0"
											>
												<span class="text-xs font-bold text-slate-600 dark:text-slate-400"
													>{price.label}</span
												>
												<div class="text-right">
													<div class="text-sm font-black text-slate-900 dark:text-white">
														Rp {price.price.toLocaleString('id-ID')}
													</div>
													<div class="text-[10px] text-slate-500 font-medium mt-0.5">
														{t('theater.events.quota') || 'Quota'}
														{price.quota}
													</div>
												</div>
											</div>
										{/each}
									</div>
								{:else if sale.price_details && sale.price_details.length > 0}
									<div class="space-y-2.5 pt-1 mt-auto">
										{#each sale.price_details as price}
											<div
												class="flex justify-between items-center py-2 border-t border-slate-100 dark:border-zinc-700/50 first:border-0"
											>
												<span class="text-xs font-bold text-slate-600 dark:text-slate-400"
													>{price.label}</span
												>
												<div class="text-right">
													<div class="text-sm font-black text-slate-900 dark:text-white">
														Rp {price.price.toLocaleString('id-ID')}
													</div>
													{#if price.quota}
														<div class="text-[10px] text-slate-500 font-medium mt-0.5">
															{t('theater.events.quota') || 'Quota'}
															{price.quota}
														</div>
													{/if}
												</div>
											</div>
										{/each}
									</div>
								{/if}
							{/if}
						</div>
					{/each}
				</div>
			</div>
		{/if}

		<!-- Members -->
		{#if (event.members && event.members.length > 0) || event.setlistId}
			<div
				class="bg-white/80 dark:bg-zinc-900/80 backdrop-blur-xl border border-white/50 dark:border-zinc-800 rounded-[2rem] p-6 sm:p-8 shadow-sm"
			>
				<div class="flex items-center justify-between mb-6">
					<h2 class="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-3">
						<div class="h-6 w-1.5 bg-red-500 rounded-full"></div>
						{t('theater.events.performingMembers')}
					</h2>
					<div
						class="flex items-center gap-1.5 sm:gap-2 text-xs sm:text-sm font-medium text-slate-500 bg-slate-100 dark:bg-zinc-800 px-3 py-1.5 rounded-full shrink-0 whitespace-nowrap"
					>
						<Users class="w-3.5 h-3.5 sm:w-4 sm:h-4" />
						{event.members && event.members.length > 0 ? event.members.length : '?'}
						{t('theater.events.members')}
					</div>
				</div>

				<div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
					{#if event.members && event.members.length > 0}
						{#each event.members as member}
							{@const isSeitansai = event.seitansaiMembers?.includes(member.name)}
							{@const isGrad = event.graduationMembers?.includes(member.name)}
							<button
								type="button"
								onclick={() => openMemberDetail(member)}
								class="group relative bg-slate-50 dark:bg-zinc-800 rounded-2xl overflow-hidden shadow-sm block text-left hover:shadow-xl transition-all duration-300 hover:-translate-y-1 border border-slate-100 dark:border-zinc-700/50 w-full cursor-pointer"
							>
								{#if isSeitansai}
									<div
										class="absolute top-2 left-2 z-20 bg-pink-500 text-white p-1.5 rounded-full shadow-lg shadow-pink-500/30"
									>
										<Cake class="w-3.5 h-3.5" />
									</div>
								{/if}
								{#if isGrad}
									<div
										class="absolute top-2 right-2 z-20 bg-indigo-500 text-white p-1.5 rounded-full shadow-lg shadow-indigo-500/30"
									>
										<GraduationCap class="w-3.5 h-3.5" />
									</div>
								{/if}
								<div
									class="relative aspect-[3/4] overflow-hidden bg-slate-200 dark:bg-zinc-700 rounded-t-2xl"
								>
									{#if member.img}
										<OptimizedImage
											src={member.img}
											srcMedium={member.img_medium}
											srcSmall={member.img_small}
											blurHash={member.blurHash}
											alt={member.name}
											class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
											sizes="(max-width: 640px) 50vw, (max-width: 768px) 33vw, 25vw"
										/>
									{:else}
										<div
											class="w-full h-full bg-gradient-to-br from-pink-100 to-purple-100 dark:from-pink-900/30 dark:to-purple-900/30 flex items-center justify-center"
										>
											<span class="text-4xl font-bold text-pink-400">
												{member.nickname?.charAt(0) || member.name?.charAt(0)}
											</span>
										</div>
									{/if}

									<img
										src={getMemberFrame(member.member_type || 'JKT48')}
										alt="member frame"
										class="absolute inset-0 w-full h-full object-fill pointer-events-none z-10"
									/>
									<div
										class="absolute inset-0 bg-gradient-to-t from-black/95 via-black/20 to-transparent z-20"
									></div>

									<div class="absolute bottom-0 left-0 right-0 p-3 flex flex-col justify-end z-30">
										<h3 class="font-bold text-white text-base leading-tight drop-shadow-sm">
											{member.nickname || member.name}
										</h3>
										<p class="text-[10px] text-slate-300 font-bold uppercase tracking-wider mt-0.5">
											{member.member_type || 'JKT48'}
										</p>
									</div>
								</div>
							</button>
						{/each}
					{:else}
						{#each Array(16) as _, _i}
							<div
								class="group relative bg-slate-50 dark:bg-zinc-800 rounded-2xl overflow-hidden shadow-sm block text-left opacity-80 border border-slate-100 dark:border-zinc-700/50"
							>
								<div
									class="relative aspect-[3/4] overflow-hidden bg-slate-200 dark:bg-zinc-700/50 rounded-t-2xl"
								>
									<div
										class="w-full h-full bg-gradient-to-br from-slate-200 to-slate-300 dark:from-zinc-800 dark:to-zinc-900 flex items-center justify-center"
									>
										<Users class="w-12 h-12 text-slate-400 dark:text-zinc-600" />
									</div>
									<img
										src={getMemberFrame('JKT48')}
										alt="member frame"
										class="absolute inset-0 w-full h-full object-fill pointer-events-none z-10 grayscale opacity-40"
									/>
									<div
										class="absolute inset-0 bg-gradient-to-t from-black/80 via-black/10 to-transparent z-20"
									></div>
									<div class="absolute bottom-0 left-0 right-0 p-3 flex flex-col justify-end z-30">
										<h3 class="font-bold text-white/70 text-base leading-tight drop-shadow-sm">
											???
										</h3>
										<p class="text-[10px] text-slate-400 font-bold uppercase tracking-wider mt-0.5">
											TBA
										</p>
									</div>
								</div>
							</div>
						{/each}
					{/if}
				</div>
			</div>
		{/if}

		<!-- Action Card -->
		<div
			class="bg-gradient-to-br from-red-500 to-rose-600 rounded-[2rem] p-5 sm:p-8 text-white shadow-xl shadow-red-500/20 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6 sm:gap-8"
		>
			<div class="text-left flex-1">
				<h3 class="font-bold text-xl mb-3 sm:mb-2">{t('theater.events.interested')}</h3>
				<p class="text-sm sm:text-base text-red-100">
					{t('theater.events.interestedDesc')}
				</p>
			</div>
			<a
				href={`https://jkt48.com${event.url}`}
				target="_blank"
				class="w-full sm:w-auto shrink-0 inline-flex items-center justify-center gap-2 bg-white text-red-600 font-bold py-3 sm:py-4 px-6 sm:px-8 rounded-xl hover:bg-red-50 transition-colors shadow-sm"
			>
				<span>{t('theater.events.viewOnJkt48')}</span>
				<ExternalLink class="w-4 h-4" />
			</a>
		</div>
	</div>
{:else}
	<!-- Loading state -->
	<div class="max-w-4xl mx-auto space-y-8 animate-fade-in pb-20 px-4 sm:px-6 md:px-0">
		<div class="w-32 h-6 bg-slate-200 dark:bg-zinc-800 rounded-full animate-pulse"></div>
		<div class="w-3/4 h-12 bg-slate-200 dark:bg-zinc-800 rounded-2xl animate-pulse"></div>
		<div
			class="w-full aspect-video rounded-[2rem] bg-slate-200 dark:bg-zinc-800 animate-pulse"
		></div>
	</div>
{/if}

<!-- Member Detail Modal -->
<MemberDetailModal
	show={showMemberDetail}
	member={selectedMember}
	members={fullEventMembers}
	loading={false}
	onClose={closeMemberDetail}
/>
