<script lang="ts">
	import { Ticket, Github, Youtube, Send } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import VersionDisplay from '$lib/components/common/VersionDisplay.svelte';

	const { t } = useTranslation();
</script>

<footer class="py-20 mt-32 relative z-10 pointer-events-none">
	<div class="text-center space-y-8 pointer-events-auto">
		<div class="flex items-center justify-center gap-3">
			<div
				class="w-10 h-10 rounded-full bg-red-600 flex items-center justify-center text-white shadow-xl shadow-red-500/20 ring-4 ring-white dark:ring-zinc-800"
			>
				<Ticket class="w-5 h-5" />
			</div>
			<span class="font-black text-2xl tracking-tighter text-slate-900 dark:text-white">
				MyPage<span class="text-red-600">48</span>
			</span>
		</div>

		<div
			class="flex items-center justify-center gap-2 text-[10px] sm:text-xs text-slate-400 dark:text-slate-500 uppercase tracking-widest font-bold"
		>
			<span>{t('landing.footer.copyright', { heart: '❤️' })}</span>
		</div>

		<div class="flex items-center justify-center gap-3">
			<a
				href="https://www.youtube.com/@MyPage48"
				target="_blank"
				class="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-red-50 dark:bg-red-950/30 text-red-600 dark:text-red-400 text-xs font-bold hover:bg-red-100 dark:hover:bg-red-900/40 transition-colors"
			>
				<Youtube size={14} />
				YouTube
			</a>
			<a
				href="https://t.me/MyPage48"
				target="_blank"
				class="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-50 dark:bg-blue-950/30 text-blue-500 dark:text-blue-400 text-xs font-bold hover:bg-blue-100 dark:hover:bg-blue-900/40 transition-colors"
			>
				<Send size={14} />
				Telegram
			</a>
		</div>

		<div class="flex items-center justify-center gap-6 flex-wrap px-6">
			<a
				href="/about"
				class="text-xs text-slate-500 dark:text-slate-400 hover:text-red-600 dark:hover:text-red-400 transition-colors"
			>
				{t('landing.footer.about')}
			</a>
			<a
				href="/privacy"
				class="text-xs text-slate-500 dark:text-slate-400 hover:text-red-600 dark:hover:text-red-400 transition-colors"
			>
				{t('landing.footer.privacy')}
			</a>
			<a
				href="/terms"
				class="text-xs text-slate-500 dark:text-slate-400 hover:text-red-600 dark:hover:text-red-400 transition-colors"
			>
				{t('landing.footer.terms')}
			</a>
			<a
				href="/cookies"
				class="text-xs text-slate-500 dark:text-slate-400 hover:text-red-600 dark:hover:text-red-400 transition-colors"
			>
				{t('landing.footer.cookies')}
			</a>
		</div>

		<p class="text-[9px] text-slate-300 max-w-md mx-auto px-6">
			{t('landing.footer.disclaimer')}
		</p>

		<div class="flex flex-col items-center gap-2">
			<a
				href="https://github.com/shiyinq/mypage48"
				target="_blank"
				class="inline-flex items-center gap-1.5 text-[10px] text-slate-400 dark:text-slate-500 hover:text-slate-600 dark:hover:text-slate-300 transition-colors font-semibold"
			>
				<Github size={12} />
				{t('landing.footer.openSource')}
			</a>
			<VersionDisplay />
		</div>
	</div>
</footer>
