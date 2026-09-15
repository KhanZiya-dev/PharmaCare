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
    <div className="md:hidden fixed bottom-6 left-1/2 -translate-x-1/2 z-50 w-[90%] max-w-[400px]">
      <div className="flex items-center justify-between bg-white/90 backdrop-blur-xl p-1.5 rounded-full shadow-[0_8px_30px_rgb(0,0,0,0.12)] border border-gray-200">
        {navItems.map((item) => {
          const active = isActive(item.href);
          const Icon = item.icon;

          return (
            <Link
              key={item.name}
              href={item.href}
              className={`relative flex-1 flex flex-col items-center justify-center h-14 transition-colors duration-300 rounded-full ${
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
              <Icon className="h-5 w-5 mb-0.5" strokeWidth={active ? 2.5 : 2} />
              <span className="text-[10px] font-medium tracking-wide whitespace-nowrap">
                {item.name}
              </span>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
