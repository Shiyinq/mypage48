import { Globe, UserCheck, Users, UsersRound, AtSign, Lock } from 'lucide-svelte';
import type { Page48ReplySetting } from '$lib/api/page48';

/**
 * Icon shown for each "who can reply" setting, shared by the composer's toolbar
 * button and the picker panel so both stay in sync.
 */
export const REPLY_AUDIENCE_ICONS: Record<Page48ReplySetting, typeof Globe> = {
	everyone: Globe,
	following: UserCheck,
	followers: Users,
	following_and_followers: UsersRound,
	only_me: Lock,
	mentioned: AtSign
};
