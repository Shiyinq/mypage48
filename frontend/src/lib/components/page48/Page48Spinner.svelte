<script lang="ts">
	interface Props {
		/** Ring size; defaults to the 24px ring used by the feeds. */
		class?: string;
	}

	let { class: className = 'h-6 w-6' }: Props = $props();
</script>

<!-- The loading ring for Page48 lists, so every list shows the same spinner while
     it fetches the next page. -->
<div
	class={`animate-spin rounded-full border-2 border-red-200 border-t-red-600 ${className}`}
></div>
