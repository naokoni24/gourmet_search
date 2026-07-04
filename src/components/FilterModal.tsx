'use client'

import { SearchParams } from '@/types/restaurant'
import { X } from 'lucide-react'

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

type Props = {
  open: boolean
  params: SearchParams
  onChange: (updater: (p: SearchParams) => SearchParams) => void
  onClose: () => void
  onApply: () => void
}

export default function FilterModal({ open, params, onChange, onClose, onApply }: Props) {
  if (!open) return null

  const set = (key: keyof SearchParams, value: unknown) =>
    onChange(p => ({ ...p, [key]: value }))

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative bg-white rounded-t-2xl sm:rounded-2xl w-full sm:w-96 max-h-[85vh] overflow-y-auto p-5 flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-gray-700">絞り込み</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X size={20} />
          </button>
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
            <span>{params.current_lat ? '現在地からの距離' : '駅・エリアからの距離'}</span>
            <span className="font-medium text-orange-500">{params.radius ? `${params.radius}m以内` : '500m以内'}</span>
          </label>
          <input
            type="range"
            min={100}
            max={2000}
            step={100}
            value={params.radius ?? 500}
            onChange={e => set('radius', Number(e.target.value))}
            className="w-full accent-orange-500"
          />
          <div className="relative text-xs text-gray-400 mt-0.5 h-4">
            <span className="absolute left-0">100m</span>
            <span className="absolute" style={{ left: '21%', transform: 'translateX(-50%)' }}>500m</span>
            <span className="absolute" style={{ left: '47%', transform: 'translateX(-50%)' }}>1km</span>
            <span className="absolute right-0">2km</span>
          </div>
        </div>

        <div>
          <label className="text-xs text-gray-500 mb-1 block">予算（上限）</label>
          <select
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-gray-900 bg-white focus:outline-none focus:ring-2 focus:ring-orange-300 text-[16px]"
            value={params.budget_max ?? ''}
            onChange={e => set('budget_max', e.target.value ? Number(e.target.value) : undefined)}
          >
            {BUDGETS.map(b => <option key={b.label} value={b.value ?? ''}>{b.label}</option>)}
          </select>
        </div>

        <div>
          <label className="text-xs text-gray-500 mb-1 block">最低評価</label>
          <select
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-gray-900 bg-white focus:outline-none focus:ring-2 focus:ring-orange-300 text-[16px]"
            value={params.rating_min ?? ''}
            onChange={e => set('rating_min', e.target.value ? Number(e.target.value) : undefined)}
          >
            {RATINGS.map(r => <option key={r.label} value={r.value ?? ''}>{r.label}</option>)}
          </select>
        </div>

        <div className="flex gap-2 pt-2">
          <button
            onClick={onClose}
            className="flex-1 border border-gray-200 text-gray-600 rounded-lg py-2.5 text-sm font-semibold hover:bg-gray-50 transition-colors"
          >
            キャンセル
          </button>
          <button
            onClick={onApply}
            className="flex-1 bg-orange-500 hover:bg-orange-600 text-white rounded-lg py-2.5 text-sm font-semibold transition-colors"
          >
            適用して検索
          </button>
        </div>
      </div>
    </div>
  )
}
