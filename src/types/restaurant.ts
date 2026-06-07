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
  phone?: string
  open_now?: boolean
  distance_m?: number
  opening_hours_today?: string
}

export type SearchParams = {
  keyword: string
  area: string
  station: string
  genre: string
  budget_max?: number
  rating_min?: number
  radius?: number
  current_lat?: number   // 現在地
  current_lng?: number
  open_now: boolean
}
