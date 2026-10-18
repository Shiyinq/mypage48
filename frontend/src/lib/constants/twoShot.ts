export const TWO_SHOT_TYPES = ['Roulette', 'Birthday', 'Graduate', 'Chekicha'] as const;

export type TwoShotType = (typeof TWO_SHOT_TYPES)[number];

export const TWO_SHOT_DEFAULT_PRICE: Record<TwoShotType, number> = {
	Roulette: 100000,
	Birthday: 250000,
	Graduate: 100000,
	Chekicha: 100000
};
