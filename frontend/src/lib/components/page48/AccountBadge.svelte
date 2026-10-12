<script lang="ts">
	import { portal } from '$lib/actions/portal';
	import type { Page48AccountType } from '$lib/api/page48';
	import { useTranslation } from '$lib/i18n/useTranslation';

	interface Props {
		/** null/undefined renders nothing so regular accounts stay plain. */
		type?: Page48AccountType | null;
		size?: number;
		class?: string;
		/**
		 * Only the profile header makes the badge interactive (help cursor + tooltip).
		 * In post/comment/list rows it stays a plain, non-hoverable mark.
		 */
		interactive?: boolean;
	}

	let { type = null, size = 16, class: className = '', interactive = false }: Props = $props();

	const { t } = useTranslation();

	let trigger = $state<SVGSVGElement>();
	let visible = $state(false);
	let placeAbove = $state(true);
	let anchor = $state({ x: 0, top: 0, bottom: 0 });

	let label = $derived(
		type === 'page48_admin'
			? t('common.accountAdmin')
			: type === 'official_account'
				? t('common.accountOfficial')
				: ''
	);

	/** Longer explanation shown in the custom tooltip (never the native title). */
	let info = $derived(
		type === 'page48_admin'
			? t('common.accountAdminInfo')
			: type === 'official_account'
				? t('common.accountOfficialInfo')
				: ''
	);

	/**
	 * The badge sits in tight rows (headers, hover cards), so the tooltip is portalled
	 * to <body> and fixed-positioned: it can never be clipped by a `truncate`/
	 * `overflow-hidden` ancestor.
	 */
	function show() {
		if (!interactive || !type || !trigger) return;
		const rect = trigger.getBoundingClientRect();
		anchor = { x: rect.left + rect.width / 2, top: rect.top, bottom: rect.bottom };
		// Flip below when there is not enough room above the badge.
		placeAbove = rect.top > 80;
		visible = true;
	}

	function hide() {
		visible = false;
	}
</script>

{#if type === 'page48_admin'}
	<!-- Gold shield: Page48 staff/admin -->
	<svg
		bind:this={trigger}
		viewBox="0 0 24 24"
		width={size}
		height={size}
		class={`shrink-0 align-[-0.125em] text-amber-400 ${interactive ? 'cursor-help' : ''} ${className}`}
		role="img"
		aria-label={label}
		onmouseenter={interactive ? show : undefined}
		onmouseleave={interactive ? hide : undefined}
	>
		<path
			d="M12 2.4 4.4 5.3v5.3c0 4.8 3.2 8.3 7.6 9.6 4.4-1.3 7.6-4.8 7.6-9.6V5.3L12 2.4Z"
			fill="currentColor"
		/>
		<path
			d="m8.6 11.7 2.3 2.3 4.5-4.8"
			fill="none"
			stroke="#fff"
			stroke-width="2.2"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
	</svg>
{:else if type === 'official_account'}
	<!-- Red verified seal: official account -->
	<svg
		bind:this={trigger}
		viewBox="0 0 24 24"
		width={size}
		height={size}
		class={`shrink-0 align-[-0.125em] text-red-600 ${interactive ? 'cursor-help' : ''} ${className}`}
		role="img"
		aria-label={label}
		onmouseenter={interactive ? show : undefined}
		onmouseleave={interactive ? hide : undefined}
	>
		<path
			d="M22.25 12c0-1.43-.88-2.67-2.19-3.34.46-1.39.2-2.9-.81-3.91s-2.52-1.27-3.91-.81c-.66-1.31-1.91-2.19-3.34-2.19s-2.67.88-3.33 2.19c-1.4-.46-2.91-.2-3.92.81s-1.26 2.52-.8 3.91c-1.31.67-2.2 1.91-2.2 3.34s.89 2.67 2.2 3.34c-.46 1.39-.21 2.9.8 3.91s2.52 1.26 3.91.81c.67 1.31 1.91 2.19 3.34 2.19s2.68-.88 3.34-2.19c1.39.45 2.9.2 3.91-.81s1.27-2.52.81-3.91c1.31-.67 2.19-1.91 2.19-3.34z"
			fill="currentColor"
		/>
		<path
			d="m7.9 12.1 2.7 2.7 5.1-5.5"
			fill="none"
			stroke="#fff"
			stroke-width="2.1"
			stroke-linecap="round"
			stroke-linejoin="round"
		/>
	</svg>
{/if}

{#if interactive && visible && type}
	<div
		use:portal
		role="tooltip"
		class="pointer-events-none fixed z-[10040] w-max max-w-[240px] rounded-xl border border-white/10 bg-zinc-900 px-3 py-2 text-left shadow-xl ring-1 ring-black/5"
		style={`left:${anchor.x}px; top:${placeAbove ? anchor.top : anchor.bottom}px; transform: translate(-50%, ${
			placeAbove ? 'calc(-100% - 8px)' : '8px'
		});`}
	>
		<p
			class={`text-[12px] font-bold ${type === 'page48_admin' ? 'text-amber-400' : 'text-red-500'}`}
		>
			{label}
		</p>
		<p class="mt-0.5 text-[11px] leading-snug text-gray-300">{info}</p>
	</div>
{/if}
