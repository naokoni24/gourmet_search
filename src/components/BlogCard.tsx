import { BlogPost } from '@/types/restaurant'
import { ExternalLink, BookOpen } from 'lucide-react'

export default function BlogCard({ post }: { post: BlogPost }) {
  return (
    <a
      href={post.url}
      target="_blank"
      rel="noopener noreferrer"
      className="bg-white rounded-xl border border-gray-200 p-4 hover:shadow-md transition-shadow flex gap-3"
    >
      <BookOpen size={18} className="text-orange-400 shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs text-gray-400">{post.source_name}</span>
          {post.published && (
            <span className="text-xs text-gray-300">{post.published.slice(0, 10)}</span>
          )}
        </div>
        <p className="text-sm font-medium text-gray-800 mb-1 line-clamp-2">{post.title}</p>
        <p className="text-xs text-gray-500 line-clamp-2">{post.summary}</p>
      </div>
      <ExternalLink size={14} className="text-gray-300 shrink-0 mt-0.5" />
    </a>
  )
}
