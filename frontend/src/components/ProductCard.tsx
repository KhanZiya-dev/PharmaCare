"use client";

import { useState } from "react";
import Link from "next/link";
import { TrendingDown, Pill, Activity, Store } from "lucide-react";

interface ProductCardProps {
  name: string;
  slug: string;
  category: string;
  composition?: string;
  image_url?: string;
}

function isValidImageUrl(url?: string): boolean {
  if (!url || typeof url !== "string") return false;
  const trimmed = url.trim();
  if (!trimmed) return false;
  try {
    const parsed = new URL(trimmed);
    return parsed.protocol === "http:" || parsed.protocol === "https:";
  } catch {
    return false;
  }
}

export function ProductCard({ name, slug, category, composition, image_url }: ProductCardProps) {
  const [imgError, setImgError] = useState(false);
  const hasValidImage = isValidImageUrl(image_url) && !imgError;

  // Mock data for UI to look like a price tracker
  const mockPlatformsCount = Math.floor(Math.random() * 3) + 2; // 2 to 4 platforms
  const mockLowestPrice = Math.floor(Math.random() * 200) + 50; // 50 to 250
  const mockDrop = Math.floor(Math.random() * 15) + 5; // 5 to 19%

  return (
    <Link
      href={`/product/${slug}`}
      className="group bg-white rounded-2xl border border-accent shadow-sm hover:shadow-lg hover:border-indigo-200 transition-all hover:-translate-y-1 overflow-hidden flex flex-col p-4 relative"
    >
      {/* Top Section: Identity */}
      <div className="flex gap-4 items-start mb-4">
        {/* Thumbnail */}
        <div className="w-16 h-16 bg-gray-50 rounded-xl flex items-center justify-center border border-gray-100 shrink-0 p-1">
          {hasValidImage ? (
            <img
              src={image_url!}
              alt={name}
              className="max-h-full max-w-full object-contain mix-blend-multiply"
              onError={() => setImgError(true)}
              loading="lazy"
            />
          ) : (
            <Pill className="h-6 w-6 text-gray-300" />
          )}
        </div>
        
        {/* Name & Composition */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-bold uppercase tracking-wider text-teal-700 bg-teal-50 px-2 py-0.5 rounded-full">
              {category}
            </span>
          </div>
          <h3 className="font-bold text-foreground text-sm group-hover:text-primary transition-colors line-clamp-2 leading-snug">
            {name}
          </h3>
          {composition && (
            <p className="text-[11px] text-gray-500 line-clamp-1 mt-1 truncate">{composition}</p>
          )}
        </div>
      </div>

      {/* Middle Section: Price Tracking Data */}
      <div className="bg-gray-50 rounded-xl p-3 flex flex-col gap-2 mb-4 border border-gray-100">
        <div className="flex justify-between items-center">
          <span className="text-xs text-gray-500 font-medium flex items-center gap-1.5">
            <Store className="w-3.5 h-3.5" />
            {mockPlatformsCount} Platforms
          </span>
          <span className="text-xs font-bold text-green-600 bg-green-50 px-2 py-0.5 rounded-md flex items-center gap-1">
            <TrendingDown className="w-3 h-3" />
            {mockDrop}% Drop
          </span>
        </div>
        
        <div className="flex justify-between items-end mt-1">
          <span className="text-xs text-gray-400">Lowest Price</span>
          <span className="text-lg font-bold text-gray-900 tracking-tight">₹{mockLowestPrice}</span>
        </div>
      </div>

      {/* Bottom Section: CTA */}
      <div className="mt-auto flex items-center justify-between">
        <div className="flex items-center gap-1 text-[11px] font-medium text-gray-400">
          <Activity className="w-3.5 h-3.5 text-blue-400" />
          Live Tracking
        </div>
        <span className="text-xs font-bold text-primary group-hover:bg-primary group-hover:text-white px-3 py-1.5 rounded-lg transition-colors">
          Compare Prices &rarr;
        </span>
      </div>
    </Link>
  );
}
