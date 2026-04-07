export const MEMBER_FRAMES = {
	ITEM: '/images/bg-member-item-frame-transparent.png',
	TRAINEE: '/images/bg-member-trainee-frame-transparent.png'
} as const;

/**
 * Returns the appropriate member frame based on member type
 */
export function getMemberFrame(memberType?: string): string {
	return memberType?.toLowerCase() === 'trainee' ? MEMBER_FRAMES.TRAINEE : MEMBER_FRAMES.ITEM;
}
