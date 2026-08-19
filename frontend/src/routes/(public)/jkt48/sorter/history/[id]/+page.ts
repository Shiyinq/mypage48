export const ssr = false;

export const load = async ({ params }: { params: { id: string } }) => {
	return { id: params.id };
};
