'use client'

import { useState } from 'react'
import { SearchParams, Restaurant } from '@/types/restaurant'
import SearchFilter from '@/components/SearchFilter'
import RestaurantCard from '@/components/RestaurantCard'
import { UtensilsCrossed } from 'lucide-react'

export default function Home() {
  const [restaurants, setRestaurants] = useState<Restaurant[]>([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSearch = async (params: SearchParams) => {
    setLoading(true)
    setSearched(true)
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
      setRestaurants(data.restaurants ?? [])
    } catch (e) {
      setError('バックエンドに接続できませんでした。サーバーが起動しているか確認してください。')
      setRestaurants([])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center gap-2">
          <UtensilsCrossed className="text-orange-500" size={24} />
          <h1 className="text-xl font-bold text-gray-800">Googleグルメサーチ</h1>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-4 py-6">
        <div className="flex flex-col md:flex-row gap-6">
          <aside className="w-full md:w-64 md:shrink-0">
            <SearchFilter onSearch={handleSearch} loading={loading} />
          </aside>

          <main className="flex-1">
            {!searched && (
              <div className="text-center py-24 text-gray-400">
                <UtensilsCrossed size={48} className="mx-auto mb-4 opacity-30" />
                <p className="text-lg">条件を入力して検索してください</p>
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
      </div>
    </div>
  )
}
