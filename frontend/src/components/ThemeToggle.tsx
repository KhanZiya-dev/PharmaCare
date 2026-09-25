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
    const targetTheme = isDark ? "light" : "dark";
    
    if ((document as any).startViewTransition) {
      document.documentElement.classList.add(`vt-going-${targetTheme}`);
      const transition = (document as any).startViewTransition(() => {
        setTheme(targetTheme);
      });
      transition.finished.finally(() => {
        document.documentElement.classList.remove(`vt-going-${targetTheme}`);
      });
    } else {
      setTheme(targetTheme);
    }
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
