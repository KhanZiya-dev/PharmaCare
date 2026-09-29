"use client";

import { useState } from "react";
import { Share2, Check } from "lucide-react";

interface ShareButtonProps {
  title: string;
  path: string;
}

export function ShareButton({ title, path }: ShareButtonProps) {
  const [shared, setShared] = useState(false);

  const handleShare = async () => {
    const url = `${window.location.origin}${path}`;
    const shareData = {
      title: title,
      text: `Compare prices for ${title} on PharmaCare`,
      url: url,
    };

    try {
      if (navigator.share) {
        await navigator.share(shareData);
      } else {
        await navigator.clipboard.writeText(url);
        setShared(true);
        setTimeout(() => setShared(false), 2000);
      }
    } catch (err) {
      console.log('Error sharing', err);
    }
  };

  return (
    <button
      onClick={handleShare}
      className="p-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-600 rounded-full transition-colors flex items-center justify-center shrink-0 border border-indigo-100"
      title="Share page"
    >
      {shared ? <Check className="w-5 h-5 text-green-600" /> : <Share2 className="w-5 h-5" />}
    </button>
  );
}
