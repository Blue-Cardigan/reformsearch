export interface SearchResult {
  title: string;
  link: string;
  snippet: string;
  search_time: string;
  relevance_score: number;
}

export interface CategoryResults {
  basic_info: SearchResult[];
  social_media: SearchResult[];
  business_interests: SearchResult[];
  controversy: SearchResult[];
}

export interface Summary {
  total_results: number;
  potential_interests: string[];
  controversy_count: number;
  has_social_media: boolean;
}

export interface CouncillorData {
  categories: CategoryResults;
  summary: Summary;
}

export interface CouncillorResults {
  [key: string]: CouncillorData;
}