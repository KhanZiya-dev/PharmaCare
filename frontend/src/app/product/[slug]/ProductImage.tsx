"use client";

import { useState } from "react";
import { Pill } from "lucide-react";

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

interface ProductImageProps {
  imageUrl?: string;
  name: string;
}

export function ProductImage({ imageUrl, name }: ProductImageProps) {
  const [imgError, setImgError] = useState(false);
  const hasValidImage = isValidImageUrl(imageUrl) && !imgError;

  if (hasValidImage) {
    return (
      <img
        src={imageUrl!}
        alt={name}
        className="w-32 h-32 object-contain bg-gray-50 rounded-xl border border-accent p-2"
        onError={() => setImgError(true)}
        loading="lazy"
      />
    );
  }

  return (
    <div className="w-32 h-32 bg-gray-50 rounded-xl border border-accent flex flex-col items-center justify-center gap-1">
      <Pill className="h-8 w-8 text-gray-300" />
      <span className="text-gray-400 text-xs">No Image</span>
    </div>
  );
}
