export interface LevelInfo {
	current: string;
	xp: number;
	nextLevelXp: number;
	nextRankTitle: string;
}

const milestones = [
	{ xp: 0, title: 'Newcomer' },
	{ xp: 1, title: 'First Step' },
	{ xp: 10, title: 'Regular Visitor' },
	{ xp: 50, title: 'Dedicated Fan' },
	{ xp: 100, title: 'Century Club' },
	{ xp: 150, title: 'Theater Icon' },
	{ xp: 200, title: 'Legendary Wota' },
	{ xp: 300, title: 'Theater Kami' },
	{ xp: 500, title: 'Absolute Legend' }
];

export function calculateLevel(totalShows: number): LevelInfo {
	const xp = totalShows;
	let currentRank = milestones[0];
	let nextRank = milestones[1];

	for (let i = 0; i < milestones.length; i++) {
		if (xp >= milestones[i].xp) {
			currentRank = milestones[i];
			nextRank = milestones[i + 1] || { xp: 1000, title: 'Beyond Legend' };
		}
	}

	return {
		current: currentRank.title,
		xp: xp,
		nextLevelXp: nextRank.xp,
		nextRankTitle: nextRank.title
	};
}
