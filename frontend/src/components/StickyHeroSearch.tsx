"use client";

import { useRef, useState, useEffect } from "react";
import { SearchAutocomplete } from "./SearchAutocomplete";

export function StickyHeroSearch() {
  const sentinelRef = useRef<HTMLDivElement>(null);
  const [isSticky, setIsSticky] = useState(false);

  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsSticky(!entry.isIntersecting);
      },
      { threshold: 0, rootMargin: '-100px 0px 0px 0px' }
    );
    observer.observe(sentinel);
    return () => observer.disconnect();
  }, []);

  return (
    <>
      {/* Invisible sentinel — when this scrolls above the navbar, search becomes sticky */}
      <div ref={sentinelRef} className="h-0 w-full" aria-hidden="true" />

      <div
        id="hero-search-bar"
        className={`sticky top-[5rem] z-40 w-full transition-all duration-500 ease-in-out ${
          isSticky
            ? "max-w-md mx-auto py-2 px-4"
            : "max-w-xl mx-auto lg:mx-0"
        }`}
      >
        <div className={`transition-all duration-500 ease-in-out ${
          isSticky 
            ? "shadow-lg rounded-full ring-1 ring-black/5" 
            : "opacity-0 animate-[fadeUp_1s_ease-out_0.6s_forwards]"
        }`}>
          <SearchAutocomplete compact={isSticky} />
        </div>
      </div>
    </>
  );
}
