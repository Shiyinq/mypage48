export interface News {
	news_id: number;
	title: string;
	category: string;
	link: string;
	background_image?: string;
	blurHash?: string;
	is_published: boolean;
	valid_date_from: string;
	content_body: string;
	short_description?: string;
}

export interface NewsPaginationResponse {
	data: News[];
	meta: {
		page: number;
		limit_per_page: number;
		total_page: number;
		count_per_page: number;
		count_total: number;
	};
}
