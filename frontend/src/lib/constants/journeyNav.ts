import { Image as ImageIcon, Crown, BookOpen, Trophy, History } from 'lucide-svelte';

export const journeyNavItems = [
	{
		labelKey: 'nav.memories',
		href: '/memories',
		icon: ImageIcon,
		theme: 'pink',
		color: 'text-pink-500'
	},
	{
		labelKey: 'nav.top2shot',
		href: '/top-2shot',
		icon: Crown,
		theme: 'indigo',
		color: 'text-indigo-500'
	},
	{
		labelKey: 'nav.journal',
		href: '/journal',
		icon: BookOpen,
		theme: 'green',
		color: 'text-green-500'
	},
	{
		labelKey: 'nav.achievements',
		href: '/achievements',
		icon: Trophy,
		theme: 'amber',
		color: 'text-amber-500'
	},
	{
		labelKey: 'nav.history',
		href: '/history',
		icon: History,
		theme: 'red',
		color: 'text-red-500'
	}
];
