import { Restaurant } from '@/types/restaurant'
import { MapPin, Star, ExternalLink, Clock, Phone } from 'lucide-react'


const SOURCE_LABEL: Record<string, string> = {
  google: 'Google',
  hotpepper: 'ホットペッパー',
}

export default function RestaurantCard({ restaurant: r }: { restaurant: Restaurant }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden hover:shadow-md transition-shadow">
      {r.photo_url && (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={r.photo_url} alt={r.name} className="w-full h-36 object-cover" />
      )}
      {!r.photo_url && (
        <div className="w-full h-36 bg-gray-100 flex items-center justify-center text-gray-300 text-4xl">
          🍽
        </div>
      )}
      <div className="p-3">
        <div className="flex items-start justify-between gap-2 mb-1">
          <h3 className="font-semibold text-gray-800 text-sm leading-snug">{r.name}</h3>
          <span className="text-xs bg-orange-50 text-orange-600 px-2 py-0.5 rounded-full shrink-0">
            {SOURCE_LABEL[r.source] ?? r.source}
          </span>
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
            className="flex items-center gap-1 mb-1 hover:underline w-fit"
          >
            <Star size={12} className="text-yellow-400 fill-yellow-400" />
            <span className="text-sm font-medium text-gray-700">{r.rating.toFixed(1)}</span>
            {r.review_count && (
              <span className="text-xs text-gray-400">({r.review_count.toLocaleString()}件)</span>
            )}
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

        {r.opening_hours_today && (
          <div className="flex items-start gap-1 mt-1 text-xs text-gray-500">
            <Clock size={10} className="mt-0.5 shrink-0" />
            <span>{r.opening_hours_today}</span>
          </div>
        )}
        {r.open_now !== undefined && (
          <span className={`text-xs mt-1 inline-block ${r.open_now ? 'text-green-600' : 'text-red-400'}`}>
            {r.open_now ? '● 営業中' : '● 営業時間外'}
          </span>
        )}

        <div className="mt-2 flex items-center gap-3 flex-wrap">
          {r.url && (
            <a
              href={r.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 text-xs text-orange-500 hover:underline"
            >
              <ExternalLink size={10} />
              詳細を見る
            </a>
          )}
          {r.phone && (
            <a
              href={`tel:${r.phone.replace(/[^\d+]/g, '')}`}
              className="flex items-center gap-1 text-xs text-blue-500 hover:underline"
            >
              <Phone size={10} />
              {r.phone}
            </a>
          )}
        </div>
      </div>
    </div>
  )
}
