"use client";

import { useState } from "react";
import Link from "next/link";
import { TrendingDown, Pill, Activity, Store, Microscope, AlertCircle } from "lucide-react";

interface ProductCardProps {
  name: string;
  slug: string;
  category: string;
  composition?: string;
  image_url?: string;
  lowestPrice?: number | null;
  platformCount?: number | null;
  discountPct?: number | null;
  requires_rx?: boolean;
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

export function ProductCard({ name, slug, category, composition, image_url, lowestPrice, platformCount, discountPct, requires_rx }: ProductCardProps) {
  const [imgError, setImgError] = useState(false);
  const hasValidImage = isValidImageUrl(image_url) && !imgError;

  return (
    <Link
      href={category === "lab_test" ? `/lab-tests/${slug}` : `/product/${slug}`}
      className="group bg-white rounded-2xl border border-accent shadow-sm hover:shadow-lg hover:border-indigo-200 transition-all hover:-translate-y-1 overflow-hidden flex flex-col p-3 md:p-4 relative"
    >
      {/* Top Section: Identity */}
      <div className="flex gap-3 md:gap-4 items-start mb-3 md:mb-4">
        {/* Thumbnail */}
        <div className="w-14 h-14 md:w-16 md:h-16 bg-[#ffffff] rounded-xl flex items-center justify-center border border-gray-100 shrink-0 p-1 overflow-hidden">
          {hasValidImage ? (
            <img
              src={image_url!}
              alt={name}
              className="max-h-full max-w-full object-contain"
              onError={() => setImgError(true)}
              loading="lazy"
            />
          ) : (
            category === "lab_test" ? (
              <Microscope className="h-5 w-5 md:h-6 md:w-6 text-teal-400" />
            ) : (
              <Pill className="h-5 w-5 md:h-6 md:w-6 text-gray-300" />
            )
          )}
        </div>
        
        {/* Name & Composition */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[9px] md:text-[10px] font-bold uppercase tracking-wider text-teal-700 bg-teal-50 px-2 py-0.5 rounded-full">
              {category}
            </span>
            {requires_rx && (
              <span className="text-[9px] md:text-[10px] font-bold uppercase tracking-wider text-red-700 bg-red-50 px-1.5 py-0.5 rounded-full border border-red-100 flex items-center gap-0.5">
                <AlertCircle className="w-2.5 h-2.5" /> Rx
              </span>
            )}
          </div>
          <h3 className="font-bold text-foreground text-sm md:text-sm group-hover:text-primary transition-colors line-clamp-2 leading-snug">
            {name}
          </h3>
          {composition && (
            <p className="text-[10px] md:text-[11px] text-gray-500 line-clamp-1 mt-0.5 md:mt-1 truncate">{composition}</p>
          )}
        </div>
      </div>

      {/* Middle Section: Price Tracking Data */}
      <div className="bg-gray-50 rounded-xl p-2 md:p-3 flex flex-col gap-1.5 md:gap-2 mb-3 md:mb-4 border border-gray-100">
        <div className="flex justify-between items-center h-4 md:h-5">
          <span className="text-[10px] md:text-[11px] text-gray-500 font-medium">Platforms Tracked</span>
          <div className="flex items-center gap-1">
            <Store className="h-3 w-3 md:h-3.5 md:w-3.5 text-indigo-500" />
            <span className="text-[10px] md:text-[11px] font-bold text-gray-700">{platformCount || 'Various'}</span>
          </div>
        </div>
        <div className="flex justify-between items-center h-4 md:h-5">
          <span className="text-[10px] md:text-[11px] text-gray-500 font-medium">Price Drop</span>
          {discountPct && discountPct > 0 ? (
            <span className="text-[10px] md:text-[11px] font-bold text-green-700 bg-green-100 px-1.5 py-0.5 rounded border border-green-200">
              SAVE {discountPct}%
            </span>
          ) : (
            <span className="text-[10px] md:text-[11px] font-medium text-gray-400">Stable</span>
          )}
        </div>
      </div>

      {/* Bottom Section: CTA */}
      <div className="mt-auto flex items-center justify-between">
        <div className="flex flex-col">
          {lowestPrice ? (
            <>
              <span className="text-[9px] md:text-[10px] text-gray-400 font-medium mb-0.5">Starting from</span>
              <span className="text-sm md:text-base font-black text-gray-900 tracking-tight">
                ₹{lowestPrice}
              </span>
            </>
          ) : null}
        </div>
        <span className="text-xs font-bold text-primary group-hover:bg-primary group-hover:text-white px-3 py-1.5 rounded-lg transition-colors">
          Compare Prices &rarr;
        </span>
      </div>
    </Link>
  );
}
