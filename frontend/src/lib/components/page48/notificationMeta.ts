import { AtSign, Heart, MessageCircle, Quote, Repeat2, UserCheck, UserPlus } from 'lucide-svelte';
import type { Page48NotificationTab, Page48NotificationType } from '$lib/api/page48';

/** The icon shown next to a notification, by the action that produced it. */
export const NOTIFICATION_ICONS: Record<Page48NotificationType, typeof Heart> = {
	like: Heart,
	reply: MessageCircle,
	repost: Repeat2,
	quote: Quote,
	mention: AtSign,
	follow: UserPlus,
	followRequest: UserPlus,
	followAccepted: UserCheck
};

/** The sentence a notification carries, shared by the list and the overview. */
export const NOTIFICATION_ACTION_KEYS: Record<Page48NotificationType, string> = {
	like: 'page48.notifications.likedPost',
	reply: 'page48.notifications.repliedPost',
	repost: 'page48.notifications.repostedPost',
	quote: 'page48.notifications.quotedPost',
	mention: 'page48.notifications.mentionedYou',
	follow: 'page48.notifications.followedYou',
	followRequest: 'page48.notifications.followRequested',
	followAccepted: 'page48.notifications.followAccepted'
};

/** The icon for a whole tab, borrowed from the type that leads it. */
export const NOTIFICATION_TAB_ICONS: Record<Page48NotificationTab, typeof Heart> = {
	replies: MessageCircle,
	mentions: AtSign,
	likes: Heart,
	reposts: Repeat2,
	follows: UserPlus
};
