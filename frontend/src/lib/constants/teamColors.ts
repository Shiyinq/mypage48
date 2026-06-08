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
	}
};

export function getTeamColors(memberType?: string): TeamColors {
	const type = memberType?.toUpperCase();
	return type && type in TEAM_COLORS ? TEAM_COLORS[type] : DEFAULT_COLORS;
}
