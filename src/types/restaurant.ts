export type Restaurant = {
  id: string
  name: string
  address: string
  station?: string
  genre: string[]
  rating?: number
  review_count?: number
  budget_min?: number
  budget_max?: number
  lat?: number
  lng?: number
  photo_url?: string
  url?: string
  source: 'google'
  distance_m?: number
}

export type SearchParams = {
  keyword: string
  place: string        // エリア・駅名を統合
  genre: string
  budget_max?: number
  rating_min?: number
  radius?: number
  current_lat?: number
  current_lng?: number
}
