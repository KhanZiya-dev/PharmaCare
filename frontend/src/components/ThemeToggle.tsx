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
    
    document.documentElement.classList.add('theme-transition');
    setTheme(theme === "dark" ? "light" : "dark");
    
    setTimeout(() => {
      document.documentElement.classList.remove('theme-transition');
    }, 300);
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
