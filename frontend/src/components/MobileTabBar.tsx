"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, Pill, FlaskConical, TrendingDown } from "lucide-react";
import { motion } from "framer-motion";

const navItems = [
  { name: "Home", href: "/", icon: Home },
  { name: "Medicines", href: "/medicines", icon: Pill },
  { name: "Lab Tests", href: "/lab-tests", icon: FlaskConical },
  { name: "Trends", href: "/trends", icon: TrendingDown },
];

export function MobileTabBar() {
  const pathname = usePathname();

  const isActive = (path: string) => {
    if (path === "/") return pathname === "/";
    return pathname?.startsWith(path);
  };

  return (
    <div className="md:hidden fixed bottom-6 left-1/2 -translate-x-1/2 z-50">
      <div className="flex items-center gap-1 bg-white/90 backdrop-blur-xl p-1.5 rounded-full shadow-[0_8px_30px_rgb(0,0,0,0.08)] border border-gray-100">
        {navItems.map((item) => {
          const active = isActive(item.href);
          const Icon = item.icon;

          return (
            <Link
              key={item.name}
              href={item.href}
              className={`relative flex flex-col items-center justify-center px-4 py-2 min-w-[72px] transition-colors duration-300 ${
                active ? "text-primary" : "text-gray-400 hover:text-gray-600"
              }`}
            >
              {active && (
                <motion.div
                  layoutId="mobile-tab-bubble"
                  className="absolute inset-0 bg-primary/10 rounded-full -z-10"
                  transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                />
              )}
              <Icon className="h-5 w-5 mb-1" strokeWidth={active ? 2.5 : 2} />
              <span className="text-[10px] font-medium tracking-wide">
                {item.name}
              </span>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
