"use client";

import { useTheme } from "next-themes";
import { Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  const toggleTheme = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
    const isDark = theme === "dark";
    const nextTheme = isDark ? "light" : "dark";

    if (!document.startViewTransition) {
      setTheme(nextTheme);
      return;
    }

    const x = e.clientX;
    const y = e.clientY;
    const endRadius = Math.hypot(
      Math.max(x, innerWidth - x),
      Math.max(y, innerHeight - y)
    );

    document.documentElement.style.setProperty('--x', `${x}px`);
    document.documentElement.style.setProperty('--y', `${y}px`);
    document.documentElement.style.setProperty('--r', `${endRadius}px`);

    document.startViewTransition(() => {
      setTheme(nextTheme);
    });
  };

  if (!mounted) return <div className="w-9 h-9" />;

  return (
    <button
      onClick={toggleTheme}
      className="p-2.5 rounded-full transition-all duration-300 flex items-center justify-center text-gray-600 hover:text-primary hover:bg-gray-100 dark:hover:bg-gray-200 focus:outline-none"
      aria-label="Toggle Dark Mode"
    >
      {theme === "dark" ? <Sun className="w-[22px] h-[22px]" strokeWidth={1.5} /> : <Moon className="w-[22px] h-[22px]" strokeWidth={1.5} />}
    </button>
  );
}
