'use client'

import { useState } from 'react'
import { SearchParams } from '@/types/restaurant'
import { Search, LocateFixed, MapPin, ChevronDown, ChevronUp } from 'lucide-react'

const GENRES = ['', '和食', '洋食', 'イタリアン', '中華', 'ラーメン', '居酒屋', '焼肉', 'カフェ', 'バー', '韓国料理']
const BUDGETS = [
  { label: '指定なし', value: undefined },
  { label: '〜1,000円', value: 1000 },
  { label: '〜2,000円', value: 2000 },
  { label: '〜3,000円', value: 3000 },
  { label: '〜5,000円', value: 5000 },
  { label: '〜10,000円', value: 10000 },
]
const RATINGS = [
  { label: '指定なし', value: undefined },
  { label: '★3.0以上', value: 3.0 },
  { label: '★3.5以上', value: 3.5 },
  { label: '★4.0以上', value: 4.0 },
  { label: '★4.5以上', value: 4.5 },
]

type Props = { onSearch: (p: SearchParams) => void; loading: boolean }

export default function SearchFilter({ onSearch, loading }: Props) {
  const [params, setParams] = useState<SearchParams>({
    keyword: '',
    area: '',
    station: '',
    genre: '',
    radius: 500,
    open_now: false,
  })

  const [locating, setLocating] = useState(false)
  const [locError, setLocError] = useState<string | null>(null)
  const [open, setOpen] = useState(true)

  const set = (key: keyof SearchParams, value: unknown) =>
    setParams(p => ({ ...p, [key]: value }))

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') onSearch(params)
  }

  const getCurrentLocation = () => {
    if (!navigator.geolocation) {
      setLocError('このブラウザは位置情報に対応していません')
      return
    }
    setLocating(true)
    setLocError(null)
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setParams(p => ({
          ...p,
          current_lat: pos.coords.latitude,
          current_lng: pos.coords.longitude,
          station: '',  // 駅指定をクリア
          area: '',
        }))
        setLocating(false)
      },
      () => {
        setLocError('位置情報を取得できませんでした')
        setLocating(false)
      }
    )
  }

  const clearLocation = () => {
    setParams(p => ({ ...p, current_lat: undefined, current_lng: undefined }))
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4 flex flex-col gap-4">
      <button
        className="flex items-center justify-between w-full md:cursor-default"
        onClick={() => setOpen(o => !o)}
      >
        <h2 className="font-semibold text-gray-700">絞り込み</h2>
        <span className="md:hidden text-gray-400">
          {open ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
        </span>
      </button>

      <div className={`flex flex-col gap-4 ${open ? '' : 'hidden md:flex'}`}>

      <div>
        <label className="text-xs text-gray-500 mb-1 block">キーワード</label>
        <input
          className="w-full border border-gray-200 rounded-lg px-3 py-2 text-gray-900 bg-white focus:outline-none focus:ring-2 focus:ring-orange-300 text-[16px]"
          placeholder="例：焼き鳥、デート"
          value={params.keyword}
          onChange={e => set('keyword', e.target.value)}
          onKeyDown={handleKeyDown}
        />
      </div>

      <div>
        <label className="text-xs text-gray-500 mb-1 block">エリア</label>
        <input
          className="w-full border border-gray-200 rounded-lg px-3 py-2 text-gray-900 bg-white focus:outline-none focus:ring-2 focus:ring-orange-300 text-[16px]"
          placeholder="例：渋谷、銀座"
          value={params.area}
          onChange={e => set('area', e.target.value)}
          onKeyDown={handleKeyDown}
        />
      </div>

      <div>
        <div className="flex items-center justify-between mb-1">
          <label className="text-xs text-gray-500">駅 / 現在地</label>
          {!params.current_lat && (
            <button
              onClick={getCurrentLocation}
              disabled={locating}
              className="flex items-center gap-1 text-xs text-orange-500 hover:text-orange-600 disabled:opacity-50 transition-colors"
            >
              <LocateFixed size={11} className={locating ? 'animate-spin' : ''} />
              {locating ? '取得中...' : '現在地を使う'}
            </button>
          )}
        </div>
        {params.current_lat ? (
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5 text-xs text-green-700 bg-green-50 border border-green-200 rounded-lg px-3 py-2 flex-1 min-w-0">
              <MapPin size={12} className="shrink-0" />
              <span className="truncate">現在地を使用中</span>
            </div>
            <button
              onClick={clearLocation}
              className="text-gray-400 hover:text-gray-600 px-1 py-2 shrink-0"
              title="解除"
            >✕</button>
          </div>
        ) : (
          <input
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-gray-900 bg-white focus:outline-none focus:ring-2 focus:ring-orange-300 text-[16px]"
            placeholder="例：新宿、渋谷"
            value={params.station}
            onChange={e => set('station', e.target.value)}
            onKeyDown={handleKeyDown}
          />
        )}
        {locError && <p className="text-xs text-red-500 mt-1">{locError}</p>}
      </div>

      <div>
        <label className="text-xs text-gray-500 mb-1 block">ジャンル</label>
        <select
          className="w-full border border-gray-200 rounded-lg px-3 py-2 text-gray-900 bg-white focus:outline-none focus:ring-2 focus:ring-orange-300 text-[16px]"
          value={params.genre}
          onChange={e => set('genre', e.target.value)}
        >
          {GENRES.map(g => <option key={g} value={g}>{g || '指定なし'}</option>)}
        </select>
      </div>

      <div>
        <label className="text-xs text-gray-500 mb-1 flex justify-between">
          <span>{params.current_lat ? '現在地からの距離' : '駅からの距離'}</span>
          <span className="font-medium text-orange-500">{params.radius ? `${params.radius}m以内` : '指定なし'}</span>
        </label>
        <input
          type="range"
          min={0}
          max={2000}
          step={100}
          value={params.radius ?? 0}
          onChange={e => set('radius', Number(e.target.value) || undefined)}
          className="w-full accent-orange-500"
        />
        <div className="relative text-xs text-gray-400 mt-0.5 h-4">
          <span className="absolute left-0">指定なし</span>
          <span className="absolute" style={{ left: '25%', transform: 'translateX(-50%)' }}>500m</span>
          <span className="absolute" style={{ left: '50%', transform: 'translateX(-50%)' }}>1km</span>
          <span className="absolute right-0">2km</span>
        </div>
      </div>

      <div>
        <label className="text-xs text-gray-500 mb-1 block">予算（上限）</label>
        <select
          className="w-full border border-gray-200 rounded-lg px-3 py-2 text-gray-900 bg-white focus:outline-none focus:ring-2 focus:ring-orange-300 text-[16px]"
          onChange={e => set('budget_max', e.target.value ? Number(e.target.value) : undefined)}
        >
          {BUDGETS.map(b => <option key={b.label} value={b.value ?? ''}>{b.label}</option>)}
        </select>
      </div>

      <div>
        <label className="text-xs text-gray-500 mb-1 block">最低評価</label>
        <select
          className="w-full border border-gray-200 rounded-lg px-3 py-2 text-gray-900 bg-white focus:outline-none focus:ring-2 focus:ring-orange-300 text-[16px]"
          onChange={e => set('rating_min', e.target.value ? Number(e.target.value) : undefined)}
        >
          {RATINGS.map(r => <option key={r.label} value={r.value ?? ''}>{r.label}</option>)}
        </select>
      </div>

      <div>
        <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
          <input
            type="checkbox"
            checked={params.open_now}
            onChange={e => set('open_now', e.target.checked)}
            className="accent-orange-500"
          />
          今すぐ営業中のみ
        </label>
      </div>

      <button
        onClick={() => { onSearch(params); setOpen(false) }}
        disabled={loading}
        className="w-full bg-orange-500 hover:bg-orange-600 disabled:opacity-50 text-white rounded-lg py-2.5 text-sm font-semibold flex items-center justify-center gap-2 transition-colors"
      >
        <Search size={16} />
        検索する
      </button>
      </div>
    </div>
  )
}
