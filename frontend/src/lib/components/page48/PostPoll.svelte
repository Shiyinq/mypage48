<script lang="ts">
	import { Check } from 'lucide-svelte';
	import type { Page48Post } from '$lib/api/page48';
	import { isAuthenticated } from '$lib/stores/authStatus.svelte';
	import { formatPollRemaining, pollPercentage, voteOnPoll } from '$lib/utils/page48';
	import { parseUTCDate } from '$lib/utils/time';
	import { useTranslation } from '$lib/i18n/useTranslation';

	interface Props {
		post: Page48Post;
		/** Read-only previews (e.g. inside the composer) keep the poll non-votable. */
		interactive?: boolean;
	}

	let { post, interactive = true }: Props = $props();

	const { t } = useTranslation();

	// Public visitors can look but not vote (options stay disabled), and they get the
	// running result since they can never vote. Signed-in users see the result once
	// they voted or once the poll ended.
	let now = $state(Date.now());
	let pollExpired = $derived(
		!!post.poll && (post.poll.isExpired || parseUTCDate(post.poll.endsAt).getTime() <= now)
	);
	let pollRemaining = $derived(post.poll ? formatPollRemaining(post.poll.endsAt, now) : '');
	let canVote = $derived(
		interactive && isAuthenticated.value && !!post.poll && !pollExpired && !post.poll.myOptionId
	);
	// A read-only preview has no way to vote, so it shows the running result straight away.
	let showPollResults = $derived(
		!!post.poll && (!interactive || pollExpired || !isAuthenticated.value || !!post.poll.myOptionId)
	);

	$effect(() => {
		if (!post.poll || pollExpired) return;
		// Only the countdown label needs to move, once every 10s is plenty.
		const timer = setInterval(() => (now = Date.now()), 10_000);
		return () => clearInterval(timer);
	});

	function handleVote(optionId: string) {
		if (!canVote) return;
		void voteOnPoll(post, optionId);
	}
</script>

{#if post.poll}
	<div class="relative z-[1] mt-3 flex flex-col gap-1.5">
		{#each post.poll.options as option (option.id)}
			{@const percentage = pollPercentage(option.votes, post.poll.totalVotes)}
			{@const mine = option.id === post.poll.myOptionId}
			<button
				type="button"
				class={`relative isolate w-full overflow-hidden rounded-xl border px-3 py-2 text-left transition-colors ${mine ? 'border-red-400 dark:border-red-500' : 'border-gray-200 dark:border-zinc-700'} ${canVote ? 'cursor-pointer hover:border-red-400 hover:bg-red-50/70 dark:hover:bg-red-950/20' : 'cursor-default'}`}
				onclick={() => handleVote(option.id)}
				aria-disabled={!canVote}
				aria-label={t('page48.poll.voteFor', { option: option.text })}
			>
				{#if showPollResults}
					<span
						class={`absolute inset-y-0 left-0 -z-10 ${mine ? 'bg-red-500/20 dark:bg-red-500/25' : 'bg-gray-200/60 dark:bg-zinc-700/60'}`}
						style={`width:${percentage}%`}
					></span>
				{/if}
				<span class="flex items-center justify-between gap-3">
					<span class="truncate text-[14px] font-medium text-gray-900 dark:text-gray-100">
						{option.text}
					</span>
					{#if showPollResults}
						<span class="flex shrink-0 items-center gap-1.5">
							{#if mine}<Check size={14} class="text-red-500" />{/if}
							<span
								class={`text-[13px] font-semibold tabular-nums ${mine ? 'text-red-500' : 'text-gray-500 dark:text-gray-400'}`}
							>
								{percentage}%
							</span>
						</span>
					{/if}
				</span>
			</button>
		{/each}

		<p class="px-1 text-[13px] text-gray-500 dark:text-gray-400">
			{#if pollExpired}
				{t('page48.poll.ended')}
			{:else}
				{t('page48.poll.endsIn', { time: pollRemaining })}
			{/if}
			· {t('page48.poll.votes', { count: post.poll.totalVotes })}
		</p>
	</div>
{/if}
