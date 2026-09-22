"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Home, Pill, Microscope, TrendingDown } from "lucide-react";
import { motion } from "framer-motion";
import { useState, useRef } from "react";

const navItems = [
  { name: "Home", href: "/", icon: Home },
  { name: "Medicines", href: "/medicines", icon: Pill },
  { name: "Lab Tests", href: "/lab-tests", icon: Microscope },
  { name: "Trends", href: "/trends", icon: TrendingDown },
];

export function MobileTabBar() {
  const pathname = usePathname();
  const router = useRouter();
  const containerRef = useRef<HTMLDivElement>(null);
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  const isActive = (path: string) => {
    if (path === "/") return pathname === "/";
    return pathname?.startsWith(path);
  };

  const activeIndex = navItems.findIndex((item) => isActive(item.href));
  const displayIndex = hoveredIndex !== null ? hoveredIndex : (activeIndex !== -1 ? activeIndex : 0);

  const handleTouchMove = (e: React.TouchEvent<HTMLDivElement>) => {
    if (!containerRef.current) return;
    const touch = e.touches[0];
    const rect = containerRef.current.getBoundingClientRect();
    
    // Calculate relative X
    const x = touch.clientX - rect.left;
    const itemWidth = rect.width / navItems.length;
    
    let index = Math.floor(x / itemWidth);
    index = Math.max(0, Math.min(index, navItems.length - 1));
    
    if (index !== hoveredIndex) {
      setHoveredIndex(index);
    }
  };

  const handleTouchEnd = () => {
    if (hoveredIndex !== null) {
      router.push(navItems[hoveredIndex].href);
      setHoveredIndex(null);
    }
  };

  return (
    <div className="md:hidden fixed z-50 w-[96%] max-w-[400px] left-1/2 -translate-x-1/2" style={{ bottom: "max(1.5rem, env(safe-area-inset-bottom))" }}>
      <div 
        ref={containerRef}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
        onTouchCancel={() => setHoveredIndex(null)}
        className="flex items-center bg-white/90 backdrop-blur-xl p-1.5 rounded-full shadow-[0_8px_30px_rgb(0,0,0,0.12)] border border-gray-200 touch-none select-none"
      >
        {navItems.map((item, i) => {
          const isHighlighted = i === displayIndex;
          const Icon = item.icon;

          return (
            <Link
              key={item.name}
              href={item.href}
              draggable={false}
              className={`relative flex-1 flex flex-col items-center justify-center h-14 rounded-full transition-colors duration-300 ${
                isHighlighted ? "text-primary" : "text-gray-400 hover:text-gray-600"
              }`}
            >
              {isHighlighted && (
                <motion.div
                  layoutId="mobile-tab-bubble"
                  className="absolute inset-0 bg-primary/10 rounded-full -z-10"
                  transition={{ type: "spring", stiffness: 300, damping: 25 }}
                />
              )}
              <Icon className="h-5 w-5 mb-0.5" strokeWidth={isHighlighted ? 2.5 : 2} />
              <span className="text-[10px] font-medium tracking-tight">
                {item.name}
              </span>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
