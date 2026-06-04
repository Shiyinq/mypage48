export type FilterType = 'this_week' | 'this_month' | 'this_year' | 'custom' | 'all_time';

export interface DateRange {
	start: string;
	end: string;
}

class LiveHistoryFilterStore {
	filterType: FilterType = $state('this_week');
	customRange: DateRange = $state({ start: '', end: '' });

	constructor() {
		// Default is this week, so we don't need to do anything here since getters handle it
	}

	get dateRange(): DateRange | null {
		const now = new Date();

		const formatDate = (date: Date) => {
			const y = date.getFullYear();
			const m = String(date.getMonth() + 1).padStart(2, '0');
			const d = String(date.getDate()).padStart(2, '0');
			return `${y}-${m}-${d}`;
		};

		switch (this.filterType) {
			case 'this_week': {
				const day = now.getDay();
				const diffToMonday = now.getDate() - day + (day === 0 ? -6 : 1);
				const start = new Date(now.setDate(diffToMonday));
				const end = new Date(start);
				end.setDate(end.getDate() + 6);
				return { start: formatDate(start), end: formatDate(end) };
			}
			case 'this_month': {
				const start = new Date(now.getFullYear(), now.getMonth(), 1);
				const end = new Date(now.getFullYear(), now.getMonth() + 1, 0);
				return { start: formatDate(start), end: formatDate(end) };
			}
			case 'this_year': {
				const start = new Date(now.getFullYear(), 0, 1);
				const end = new Date(now.getFullYear(), 11, 31);
				return { start: formatDate(start), end: formatDate(end) };
			}
			case 'custom':
				if (this.customRange.start && this.customRange.end) {
					return this.customRange;
				}
				return null;
			case 'all_time':
			default:
				return null;
		}
	}

	setFilterType(type: FilterType) {
		this.filterType = type;
		if (type !== 'custom') {
			this.customRange = { start: '', end: '' };
		}
	}

	setCustomRange(start: string, end: string) {
		this.customRange = { start, end };
		this.filterType = 'custom';
	}
}

export const liveHistoryFilterStore = new LiveHistoryFilterStore();
