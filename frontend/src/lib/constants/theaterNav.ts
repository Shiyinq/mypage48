import { AudioLines, Users, Newspaper, Calendar, History, ArrowUpDown, Tv } from 'lucide-svelte';

export const theaterNavItems = [
	{
		labelKey: 'theater.subNav.theater',
		href: '/theater',
		icon: AudioLines,
		exact: true,
		theme: 'purple',
		color: 'text-purple-500'
	},
	{
		labelKey: 'theater.subNav.members',
		href: '/theater/members',
		icon: Users,
		theme: 'pink',
		color: 'text-pink-500'
	},
	{
		labelKey: 'theater.subNav.news',
		labelDefault: 'News',
		href: '/theater/news',
		icon: Newspaper,
		theme: 'red',
		color: 'text-red-500'
	},
	{
		labelKey: 'theater.subNav.events',
		href: '/theater/events',
		icon: Calendar,
		exact: true,
		theme: 'blue',
		color: 'text-blue-500'
	},
	{
		labelKey: 'theater.subNav.calendar',
		labelDefault: 'Calendar',
		href: '/theater/events/calendar',
		icon: Calendar,
		theme: 'blue',
		color: 'text-blue-600'
	},
	{
		labelKey: 'theater.subNav.history',
		labelDefault: 'History',
		href: '/theater/events/history',
		icon: History,
		theme: 'orange',
		color: 'text-orange-500'
	},
	{
		labelKey: 'theater.subNav.sorter',
		labelDefault: 'Sorter',
		href: '/theater/sorter',
		icon: ArrowUpDown,
		theme: 'rose',
		color: 'text-rose-500'
	},
	{
		labelKey: 'theater.subNav.live',
		labelDefault: 'Live',
		href: '/theater/live',
		icon: Tv,
		theme: 'red',
		color: 'text-red-600'
	}
];
