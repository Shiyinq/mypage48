<script lang="ts">
	import { onMount } from 'svelte';
	import { Tag } from 'lucide-svelte';

	let version = $state('v-dev');

	const REPO = 'Shiyinq/mypage48';
	const CACHE_KEY = 'app_version_cache';
	const CACHE_TTL = 30 * 60 * 1000;

	onMount(async () => {
		const cached = localStorage.getItem(CACHE_KEY);
		if (cached) {
			const { tag, timestamp } = JSON.parse(cached);
			const isExpired = Date.now() - timestamp > CACHE_TTL;

			if (!isExpired) {
				version = tag;
				return;
			}
		}

		try {
			const res = await fetch(`https://api.github.com/repos/${REPO}/releases/latest`);
			if (res.ok) {
				const data = await res.json();
				version = data.tag_name;
				localStorage.setItem(
					CACHE_KEY,
					JSON.stringify({
						tag: version,
						timestamp: Date.now()
					})
				);
			} else if (cached) {
				const { tag } = JSON.parse(cached);
				version = tag;
			}
		} catch (e) {
			console.error('Failed to fetch version from GitHub', e);
			if (cached) {
				const { tag } = JSON.parse(cached);
				version = tag;
			}
		}
	});
</script>

<div
	class="flex flex-col items-center justify-center gap-1 text-[10px] text-slate-400 dark:text-zinc-500 font-medium"
>
	<a
		href="https://github.com/{REPO}/releases"
		target="_blank"
		class="inline-flex items-center gap-1.5 hover:text-red-600 dark:hover:text-red-400 transition-colors group"
	>
		<Tag size={12} class="group-hover:rotate-12 transition-transform" />
		<span>mypage48 {version}</span>
	</a>
</div>
