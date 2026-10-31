"use client";

import { useEffect, useState, useRef, ReactNode } from "react";

interface StickyMobileSearchProps {
  children: ReactNode;
  className?: string;
  topOffsetClass?: string; // Tailwind class, e.g. "top-[4.75rem]"
  thresholdPx?: number;    // Pixel offset from viewport top where it sticks
}

export function StickyMobileSearch({
  children,
  className = "",
  topOffsetClass = "top-[4.75rem]",
  thresholdPx = 76,
}: StickyMobileSearchProps) {
  const [isSticky, setIsSticky] = useState(false);
  const sentinelRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const [measuredHeight, setMeasuredHeight] = useState<number>(56);

  useEffect(() => {
    // Measure initial height so placeholder prevents any layout shift
    if (contentRef.current) {
      const h = contentRef.current.offsetHeight;
      if (h > 0) setMeasuredHeight(h);
    }

    let ticking = false;

    const checkSticky = () => {
      if (!ticking) {
        window.requestAnimationFrame(() => {
          if (window.innerWidth >= 768) {
            setIsSticky(false);
            ticking = false;
            return;
          }

          if (sentinelRef.current) {
            const rect = sentinelRef.current.getBoundingClientRect();
            // Sentinel stays in normal document flow.
            // When it scrolls up to or past the sticky top threshold, stick!
            setIsSticky(rect.top <= thresholdPx);
          }
          ticking = false;
        });
        ticking = true;
      }
    };

    window.addEventListener("scroll", checkSticky, { passive: true });
    window.addEventListener("resize", checkSticky, { passive: true });
    checkSticky();

    return () => {
      window.removeEventListener("scroll", checkSticky);
      window.removeEventListener("resize", checkSticky);
    };
  }, [thresholdPx]);

  return (
    <div className={`relative ${className}`}>
      {/* Invisible sentinel in normal document flow */}
      <div ref={sentinelRef} className="h-0 w-full pointer-events-none" aria-hidden="true" />

      {/* In-flow placeholder on mobile to preserve layout height when sticky */}
      {isSticky && (
        <div
          className="md:hidden w-full shrink-0"
          style={{ height: `${measuredHeight}px` }}
          aria-hidden="true"
        />
      )}

      {/* The Search Bar element */}
      <div
        ref={contentRef}
        className={
          isSticky
            ? `fixed ${topOffsetClass} left-0 right-0 z-40 max-w-7xl mx-auto px-[clamp(1rem,5vw,2rem)] pointer-events-none md:static md:p-0 md:max-w-none`
            : "w-full"
        }
      >
        <div className={isSticky ? "w-full drop-shadow-md pointer-events-auto transition-shadow" : "w-full"}>
          {children}
        </div>
      </div>
    </div>
  );
}
