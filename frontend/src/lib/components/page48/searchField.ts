/**
 * Shared look for the Page48 search fields.
 *
 * The sidebar widget and the results page draw the field from these tokens, so
 * the input cannot look different depending on where it is used. `type="text"`
 * with `enterkeyhint="search"` is deliberate: `type="search"` makes browsers add
 * their own clear button, which changes the field as soon as it has text.
 */
export const SEARCH_FIELD_CLASS =
	'w-full rounded-full border border-gray-200 bg-white/80 py-2.5 pl-10 pr-3.5 text-[14px] text-gray-900 outline-none transition-colors placeholder:text-gray-400 focus:border-red-400 dark:border-zinc-800 dark:bg-zinc-900/70 dark:text-gray-100 dark:placeholder:text-gray-500';

export const SEARCH_FIELD_ICON_CLASS =
	'pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400';

export const SEARCH_FIELD_INPUT_TYPE = 'text';
