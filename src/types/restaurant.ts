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
  source: 'google' | 'hotpepper'
  open_now?: boolean
}

export type BlogPost = {
  title: string
  url: string
  summary: string
  published?: string
  source_name: string
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
  sources: string[]
}
