'use client'

import { useState } from 'react'
import { SearchParams } from '@/types/restaurant'
import { Search, LocateFixed, MapPin, SlidersHorizontal } from 'lucide-react'

type Props = {
  params: SearchParams
  onChange: (updater: (p: SearchParams) => SearchParams) => void
  onSearch: () => void
  onOpenFilters: () => void
  activeFilterCount: number
  loading: boolean
}

export default function SearchBar({ params, onChange, onSearch, onOpenFilters, activeFilterCount, loading }: Props) {
  const [locating, setLocating] = useState(false)
  const [locError, setLocError] = useState<string | null>(null)

  const set = (key: keyof SearchParams, value: unknown) =>
    onChange(p => ({ ...p, [key]: value }))

  const getCurrentLocation = () => {
    if (!navigator.geolocation) {
      setLocError('このブラウザは位置情報に対応していません')
      return
    }
    setLocating(true)
    setLocError(null)
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        onChange(p => ({
          ...p,
          current_lat: pos.coords.latitude,
          current_lng: pos.coords.longitude,
          place: '',
        }))
        setLocating(false)
      },
      () => {
        setLocError('位置情報を取得できませんでした')
        setLocating(false)
      }
    )
  }

  const clearLocation = () => onChange(p => ({ ...p, current_lat: undefined, current_lng: undefined }))

  const hasLocation = params.place.trim() !== '' || params.current_lat != null

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4 flex flex-col gap-2">
      <div className="flex flex-col sm:flex-row gap-2">
        <input
          className="flex-1 border border-gray-200 rounded-lg px-3 py-2.5 text-gray-900 bg-white focus:outline-none focus:ring-2 focus:ring-orange-300 text-[16px]"
          placeholder="例：焼き鳥、デート"
          value={params.keyword}
          onChange={e => set('keyword', e.target.value)}
        />

        {params.current_lat ? (
          <div className="flex items-center gap-2 flex-1">
            <div className="flex items-center gap-1.5 text-xs text-green-700 bg-green-50 border border-green-200 rounded-lg px-3 py-2.5 flex-1 min-w-0">
              <MapPin size={12} className="shrink-0" />
              <span className="truncate">現在地を使用中</span>
            </div>
            <button
              onClick={clearLocation}
              className="text-gray-400 hover:text-gray-600 px-1 shrink-0"
              title="解除"
            >✕</button>
          </div>
        ) : (
          <div className="flex-1 flex items-center gap-2">
            <input
              className="flex-1 min-w-0 border border-gray-200 rounded-lg px-3 py-2.5 text-gray-900 bg-white focus:outline-none focus:ring-2 focus:ring-orange-300 text-[16px]"
              placeholder="例：渋谷、新宿、銀座"
              value={params.place}
              onChange={e => set('place', e.target.value)}
            />
            <button
              onClick={getCurrentLocation}
              disabled={locating}
              className="flex items-center gap-1.5 text-sm font-semibold text-white bg-orange-500 hover:bg-orange-600 disabled:opacity-50 transition-colors whitespace-nowrap shrink-0 rounded-lg px-3 py-2.5"
            >
              <LocateFixed size={16} className={locating ? 'animate-spin' : ''} />
              {locating ? '取得中' : '現在地'}
            </button>
          </div>
        )}

        <button
          onClick={onOpenFilters}
          className="relative flex items-center justify-center gap-1.5 border border-gray-200 rounded-lg px-3 py-2.5 text-gray-600 hover:bg-gray-50 transition-colors shrink-0"
          title="絞り込み"
        >
          <SlidersHorizontal size={16} />
          <span className="text-sm">絞り込み</span>
          {activeFilterCount > 0 && (
            <span className="absolute -top-1.5 -right-1.5 bg-orange-500 text-white text-[10px] leading-none rounded-full w-4 h-4 flex items-center justify-center">
              {activeFilterCount}
            </span>
          )}
        </button>

        <button
          onClick={onSearch}
          disabled={loading || !hasLocation}
          title={hasLocation ? undefined : '駅名・エリアを入力するか、現在地を使ってください'}
          className="bg-orange-500 hover:bg-orange-600 disabled:opacity-50 text-white rounded-lg px-5 py-2.5 text-sm font-semibold flex items-center justify-center gap-2 transition-colors shrink-0"
        >
          <Search size={16} />
          検索
        </button>
      </div>
      {locError && <p className="text-xs text-red-500">{locError}</p>}
      {!hasLocation && (
        <p className="text-xs text-gray-400">駅名・エリアを入力するか、現在地を使うと検索できます</p>
      )}
    </div>
  )
}
