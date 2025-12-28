import type { LayoutServerLoad } from './$types';

export const load: LayoutServerLoad = async ({ cookies }) => {
    // Get locale from cookie, default to 'id' if not present
    const locale = cookies.get('mypage48_locale') || 'id';

    return {
        locale
    };
};
