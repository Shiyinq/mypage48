let _isInitialDataLoaded = $state(false);
export const isInitialDataLoaded = {
	get value() {
		return _isInitialDataLoaded;
	},
	set value(v: boolean) {
		_isInitialDataLoaded = v;
	},
	set: (v: boolean) => {
		_isInitialDataLoaded = v;
	}
};
