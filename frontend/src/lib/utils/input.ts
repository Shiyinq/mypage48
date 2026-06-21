/**
 * Prevents non-numeric characters (like minus, plus, exponents) from being typed into number inputs
 */
export function preventNonNumericInput(e: KeyboardEvent) {
	if (['-', '+', 'e', 'E', '.', ','].includes(e.key)) {
		e.preventDefault();
	}
}

/**
 * Enforces a minimum value for number inputs, maintaining the original type (string or number).
 * Useful for oninput handlers in Svelte where bind:value can hold numbers or strings.
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function enforceMin(value: any, min: number): any {
	if (value === undefined || value === null || value === '') return value;

	if (Number(value) < min) {
		return typeof value === 'string' ? String(min) : min;
	}

	return value;
}
