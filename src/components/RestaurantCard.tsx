import { Restaurant } from '@/types/restaurant'
import Image from 'next/image'
import { MapPin, Star, ExternalLink } from 'lucide-react'

type Props = {
  restaurant: Restaurant
}

const GENRE_VISUALS = [
  { keywords: ['焼肉', 'ステーキ', '韓国料理'], label: '焼肉', src: '/genre-images/yakiniku.png' },
  { keywords: ['居酒屋', '焼き鳥'], label: '居酒屋', src: '/genre-images/izakaya.png' },
  { keywords: ['カフェ', 'デザート', 'ベーカリー'], label: 'カフェ', src: '/genre-images/cafe.png' },
  { keywords: ['ラーメン', '麺料理'], label: 'ラーメン', src: '/genre-images/ramen.png' },
  { keywords: ['寿司', '海鮮'], label: '寿司', src: '/genre-images/sushi.png' },
  { keywords: ['イタリアン', 'ピザ'], label: 'イタリアン', src: '/genre-images/italian.png' },
  { keywords: ['中華'], label: '中華', src: '/genre-images/chinese.png' },
  { keywords: ['和食', 'しゃぶしゃぶ', 'すき焼き', '天ぷら', 'とんかつ'], label: '和食', src: '/genre-images/washoku.png' },
  { keywords: ['バー'], label: 'バー', src: '/genre-images/bar.png' },
]

const getGenreVisual = (genres: string[]) => {
  const joined = genres.join(' ')
  return GENRE_VISUALS.find(v =>
    v.keywords.some(keyword => joined.includes(keyword))
  ) ?? { label: 'レストラン', src: '/genre-images/restaurant.png' }
}

export default function RestaurantCard({ restaurant: r }: Props) {
  const visual = getGenreVisual(r.genre)

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden hover:shadow-md transition-shadow">
      <div className="relative w-full h-36 bg-orange-50">
        <Image
          src={visual.src}
          alt=""
          fill
          sizes="(max-width: 768px) 100vw, 50vw"
          loading="lazy"
          decoding="async"
          className="object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/35 via-black/10 to-transparent" />
        <div className="absolute left-3 bottom-3">
          <span className="inline-flex items-center rounded-full bg-white/90 px-2.5 py-1 text-xs font-semibold text-gray-700 shadow-sm">
            {visual.label}
          </span>
        </div>
      </div>
      <div className="p-3">
        <div className="mb-1">
          <h3 className="font-semibold text-gray-800 text-sm leading-snug">{r.name}</h3>
        </div>

        {r.rating && (() => {
          // place_id を抽出して口コミページに直接リンク
          const placeId = r.id.startsWith('google_') ? r.id.replace('google_', '') : null
          const reviewUrl = placeId
            ? `https://search.google.com/local/reviews?placeid=${placeId}`
            : r.url ?? '#'
          return (
          <a
            href={reviewUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="mb-2 inline-flex items-center gap-2 rounded-lg border border-yellow-200 bg-yellow-50 px-2.5 py-1.5 text-sm text-gray-700 transition-colors hover:bg-yellow-100"
          >
            <Star size={12} className="text-yellow-400 fill-yellow-400" />
            <span className="font-medium">口コミを見る</span>
            <span className="font-semibold text-gray-800">{r.rating.toFixed(1)}</span>
            {r.review_count && (
              <span className="text-xs text-gray-500">({r.review_count.toLocaleString()}件)</span>
            )}
            <ExternalLink size={12} className="text-gray-500" />
          </a>
          )
        })()}

        {r.genre.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-2">
            {r.genre.filter(Boolean).map(g => (
              <span key={g} className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">{g}</span>
            ))}
          </div>
        )}

        <div className="flex items-center gap-1 text-xs text-gray-400">
          <MapPin size={10} />
          <span className="truncate">{r.station ?? r.address}</span>
          {r.distance_m != null && (
            <span className="ml-auto shrink-0 text-orange-500 font-medium">
              {r.distance_m < 1000
                ? `${r.distance_m}m`
                : `${(r.distance_m / 1000).toFixed(1)}km`}
            </span>
          )}
        </div>

        {r.url && (
          <div className="mt-3">
            <a
              href={r.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex w-full items-center justify-between rounded-lg border border-orange-200 bg-orange-50 px-3 py-2 text-sm font-medium text-orange-700 transition-colors hover:bg-orange-100"
            >
              <span>店舗詳細を見る</span>
              <ExternalLink size={14} />
            </a>
          </div>
        )}
      </div>
    </div>
  )
}
