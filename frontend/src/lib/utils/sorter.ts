/**
 * Calculates the total number of element moves in the sorter's merge sort implementation.
 * This is used to provide an accurate progress percentage.
 * 
 * @param n Number of items to sort
 * @returns Total number of moves required to complete the sort
 */
export function calculateTotalMoves(n: number): number {
	if (n <= 1) return 0;
	let moves = 0;
	let currentLists = Array(n).fill(1);
	while (currentLists.length > 1) {
		let nextLists: number[] = [];
		for (let i = 0; i < currentLists.length; i += 2) {
			if (i + 1 < currentLists.length) {
				let mergedSize = currentLists[i] + currentLists[i + 1];
				moves += mergedSize;
				nextLists.push(mergedSize);
			} else {
				nextLists.push(currentLists[i]);
			}
		}
		currentLists = nextLists;
	}
	return moves;
}
