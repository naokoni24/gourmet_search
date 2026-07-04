'use client'

import { useEffect, useState } from 'react'
import { SearchParams, Restaurant } from '@/types/restaurant'
import SearchBar from '@/components/SearchBar'
import FilterModal from '@/components/FilterModal'
import RestaurantCard from '@/components/RestaurantCard'
import GoogleIcon from '@/components/GoogleIcon'
import { UtensilsCrossed } from 'lucide-react'

const DEFAULT_PARAMS: SearchParams = {
  keyword: '',
  place: '',
  genre: '',
  radius: 500,
}

// 店舗詳細・口コミは外部サイトへ新規タブで遷移するため、元のタブに戻った時に
// 検索結果が消えていないよう、直近の検索結果をタブ内に保存しておく
const LAST_SEARCH_KEY = 'gourmet-search:last-search'

type SavedSearch = {
  params: SearchParams
  searchedParams: SearchParams
  restaurants: Restaurant[]
}

export default function Home() {
  const [params, setParams] = useState<SearchParams>(DEFAULT_PARAMS)
  const [filterOpen, setFilterOpen] = useState(false)
  const [restaurants, setRestaurants] = useState<Restaurant[]>([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [searchedParams, setSearchedParams] = useState<SearchParams | null>(null)

  useEffect(() => {
    try {
      const saved = sessionStorage.getItem(LAST_SEARCH_KEY)
      if (!saved) return
      const data: SavedSearch = JSON.parse(saved)
      setParams(data.params)
      setSearchedParams(data.searchedParams)
      setRestaurants(data.restaurants)
      setSearched(true)
    } catch {
      // 壊れた保存データは無視して通常通り初期表示にする
    }
  }, [])

  const activeFilterCount = [
    params.genre,
    params.budget_max,
    params.rating_min,
    params.radius && params.radius !== 500 ? params.radius : undefined,
  ].filter(v => v !== undefined && v !== '').length

  const getSearchConditionLabels = (p: SearchParams) => {
    const labels: string[] = []
    const keyword = p.keyword.trim()
    const place = p.place.trim()

    if (keyword) labels.push(`キーワード: ${keyword}`)
    if (p.current_lat != null && p.current_lng != null) {
      labels.push('場所: 現在地')
    } else if (place) {
      labels.push(`場所: ${place}`)
    }
    if (p.genre) labels.push(`ジャンル: ${p.genre}`)
    labels.push(`距離: ${p.radius ?? 500}m以内`)
    if (p.budget_max) labels.push(`予算: ${p.budget_max.toLocaleString()}円以内`)
    if (p.rating_min) labels.push(`評価: ★${p.rating_min.toFixed(1)}以上`)

    return labels.length ? labels : ['条件指定なし']
  }

  const handleSearch = async () => {
    setLoading(true)
    setSearched(true)
    setSearchedParams({ ...params })
    setError(null)
    try {
      const query = new URLSearchParams({
        keyword: params.keyword,
        place: params.place,
        genre: params.genre,
        ...(params.budget_max ? { budget_max: String(params.budget_max) } : {}),
        ...(params.rating_min ? { rating_min: String(params.rating_min) } : {}),
        ...(params.radius ? { radius: String(params.radius) } : {}),
        ...(params.current_lat != null ? { current_lat: String(params.current_lat) } : {}),
        ...(params.current_lng != null ? { current_lng: String(params.current_lng) } : {}),
      })
      const res = await fetch(`/api/search?${query}`)
      if (!res.ok) throw new Error(`Server error: ${res.status}`)
      const data = await res.json()
      const results: Restaurant[] = data.restaurants ?? []
      setRestaurants(results)
      try {
        const saved: SavedSearch = { params, searchedParams: { ...params }, restaurants: results }
        sessionStorage.setItem(LAST_SEARCH_KEY, JSON.stringify(saved))
      } catch {
        // sessionStorageが使えない環境では保存をスキップ
      }
    } catch {
      setError('バックエンドに接続できませんでした。サーバーが起動しているか確認してください。')
      setRestaurants([])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-3 flex items-center gap-2">
          <UtensilsCrossed className="text-orange-500" size={24} />
          <h1 className="text-xl font-bold text-gray-800">Googleグルメサーチ</h1>
          <GoogleIcon size={20} />
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-4 py-6 flex flex-col gap-6">
        <SearchBar
          params={params}
          onChange={setParams}
          onSearch={handleSearch}
          onOpenFilters={() => setFilterOpen(true)}
          activeFilterCount={activeFilterCount}
          loading={loading}
        />

        <main>
          {!searched && (
            <div className="text-center py-24 text-gray-400">
              <UtensilsCrossed size={48} className="mx-auto mb-4 opacity-30" />
              <p className="text-lg">条件を入力して検索してください</p>
            </div>
          )}

          {searched && searchedParams && (
            <div className="mb-4 bg-white border border-gray-200 rounded-lg p-3">
              <div className="text-xs font-semibold text-gray-500 mb-2">検索条件</div>
              <div className="flex flex-wrap gap-2">
                {getSearchConditionLabels(searchedParams).map(label => (
                  <span
                    key={label}
                    className="bg-orange-50 text-orange-700 border border-orange-100 rounded-full px-3 py-1 text-xs"
                  >
                    {label}
                  </span>
                ))}
              </div>
            </div>
          )}

          {loading && (
            <div className="text-center py-24 text-gray-400">
              <div className="inline-block w-8 h-8 border-4 border-orange-400 border-t-transparent rounded-full animate-spin mb-4" />
              <p>検索中...</p>
            </div>
          )}

          {!loading && error && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-600 text-sm">
              ⚠️ {error}
            </div>
          )}

          {!loading && searched && !error && (
            restaurants.length === 0 ? (
              <p className="text-center py-16 text-gray-400">見つかりませんでした</p>
            ) : (
              <section>
                <h2 className="text-sm font-semibold text-gray-500 mb-3">
                  店舗 {restaurants.length}件
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {restaurants.map(r => (
                    <RestaurantCard key={r.id} restaurant={r} />
                  ))}
                </div>
              </section>
            )
          )}
        </main>
      </div>

      <FilterModal
        open={filterOpen}
        params={params}
        onChange={setParams}
        onClose={() => setFilterOpen(false)}
        onApply={() => {
          setFilterOpen(false)
          handleSearch()
        }}
      />
    </div>
  )
}
