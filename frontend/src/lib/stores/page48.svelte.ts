export const page48NavbarStore = $state<{
	pageType:
		| 'feed'
		| 'post-detail'
		| 'user-profile'
		| 'bookmarks'
		| 'search'
		| 'trending'
		| 'members';
}>({
	pageType: 'feed'
});
