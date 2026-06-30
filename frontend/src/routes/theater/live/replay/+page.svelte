<script lang="ts">
	import AppBackground from '$lib/components/common/AppBackground.svelte';
	import ReplayList from '$lib/components/live/replay/ReplayList.svelte';
</script>

<AppBackground hideDecorationsOnMobile={true} />
<ReplayList basePath="/theater/live/replay" />
