import { Heart, Star, Flame, Sprout, Crown } from 'lucide-svelte';

export interface TeamColors {
	ring: string;
	glow: string;
	badgeBg: string;
	badgeBorder: string;
	badgeDot: string;
	badgeText: string;
}

const DEFAULT_COLORS: TeamColors = {
	ring: '#22c55e',
	glow: '#22c55e',
	badgeBg: '#22c55e',
	badgeBorder: '#22c55e',
	badgeDot: '#22c55e',
	badgeText: '#22c55e'
};

const TEAM_COLORS: Record<string, TeamColors> = {
	LOVE: {
		ring: '#DE1578',
		glow: '#DE1578',
		badgeBg: '#DE1578',
		badgeBorder: '#DE1578',
		badgeDot: '#DE1578',
		badgeText: '#DE1578'
	},
	DREAM: {
		ring: '#1A9D9C',
		glow: '#1A9D9C',
		badgeBg: '#1A9D9C',
		badgeBorder: '#1A9D9C',
		badgeDot: '#1A9D9C',
		badgeText: '#1A9D9C'
	},
	PASSION: {
		ring: '#F18921',
		glow: '#F18921',
		badgeBg: '#F18921',
		badgeBorder: '#F18921',
		badgeDot: '#F18921',
		badgeText: '#F18921'
	},
	TRAINEE: {
		ring: '#c08081',
		glow: '#c08081',
		badgeBg: '#c08081',
		badgeBorder: '#c08081',
		badgeDot: '#c08081',
		badgeText: '#c08081'
	},
	JKT48_VIRTUAL: {
		ring: '#2563eb',
		glow: '#2563eb',
		badgeBg: '#2563eb',
		badgeBorder: '#2563eb',
		badgeDot: '#2563eb',
		badgeText: '#2563eb'
	},
	JKT48: {
		ring: '#dc2626',
		glow: '#dc2626',
		badgeBg: '#dc2626',
		badgeBorder: '#dc2626',
		badgeDot: '#dc2626',
		badgeText: '#dc2626'
	},
	EVENT: {
		ring: '#8b5cf6',
		glow: '#8b5cf6',
		badgeBg: '#8b5cf6',
		badgeBorder: '#8b5cf6',
		badgeDot: '#8b5cf6',
		badgeText: '#8b5cf6'
	},
	SHOW: {
		ring: '#3b82f6',
		glow: '#3b82f6',
		badgeBg: '#3b82f6',
		badgeBorder: '#3b82f6',
		badgeDot: '#3b82f6',
		badgeText: '#3b82f6'
	},
	GENERAL: {
		ring: '#6b7280',
		glow: '#6b7280',
		badgeBg: '#6b7280',
		badgeBorder: '#6b7280',
		badgeDot: '#6b7280',
		badgeText: '#6b7280'
	},
	BIRTHDAY: {
		ring: '#f43f5e',
		glow: '#f43f5e',
		badgeBg: '#f43f5e',
		badgeBorder: '#f43f5e',
		badgeDot: '#f43f5e',
		badgeText: '#f43f5e'
	},
	EXCLUSIVE: {
		ring: '#d97706',
		glow: '#d97706',
		badgeBg: '#d97706',
		badgeBorder: '#d97706',
		badgeDot: '#d97706',
		badgeText: '#d97706'
	}
};

export function getTeamColors(memberType?: string): TeamColors {
	const type = memberType?.toUpperCase();
	return type && type in TEAM_COLORS ? TEAM_COLORS[type] : DEFAULT_COLORS;
}

export function getTeamIcon(label: string) {
	if (!label) return null;
	const l = label.toUpperCase();
	if (l === 'LOVE') return Heart;
	if (l === 'DREAM') return Star;
	if (l === 'PASSION' || l === 'SESSION') return Flame;
	if (l === 'TRAINEE') return Sprout;
	if (l === 'EXCLUSIVE') return Crown;
	return null;
}
