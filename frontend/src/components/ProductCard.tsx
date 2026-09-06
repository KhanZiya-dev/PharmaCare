import Link from "next/link";
import { TrendingDown } from "lucide-react";

interface ProductCardProps {
  name: string;
  slug: string;
  category: string;
  composition?: string;
  image_url?: string;
}

export function ProductCard({ name, slug, category, composition, image_url }: ProductCardProps) {
  return (
    <Link
      href={`/product/${slug}`}
      className="group bg-white rounded-2xl border border-accent shadow-sm hover:shadow-lg transition-all hover:-translate-y-1 overflow-hidden flex flex-col"
    >
      {/* Image */}
      <div className="h-40 bg-gray-50 flex items-center justify-center border-b border-accent p-4">
        {image_url ? (
          <img src={image_url} alt={name} className="max-h-full max-w-full object-contain" />
        ) : (
          <div className="text-gray-300 text-sm font-medium">No Image</div>
        )}
      </div>

      {/* Details */}
      <div className="p-4 flex-1 flex flex-col">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-[10px] font-bold uppercase tracking-wider text-teal-700 bg-teal-50 px-2 py-0.5 rounded-full">
            {category}
          </span>
        </div>
        <h3 className="font-bold text-foreground text-sm group-hover:text-primary transition-colors mb-1 line-clamp-2">
          {name}
        </h3>
        {composition && (
          <p className="text-xs text-gray-400 line-clamp-1 mb-3">{composition}</p>
        )}
        <div className="mt-auto pt-3 border-t border-accent/50 flex items-center justify-between">
          <span className="text-xs text-gray-500 font-medium flex items-center gap-1">
            <TrendingDown className="h-3 w-3 text-secondary" />
            Compare prices
          </span>
          <span className="text-xs font-bold text-primary group-hover:underline">View →</span>
        </div>
      </div>
    </Link>
  );
}
