"use client";

import Link from "next/link";
import { Pill, Menu, X, MessageCircle, Home, FlaskConical, TrendingUp, Search } from "lucide-react";
import { usePathname } from "next/navigation";
import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { SearchAutocomplete } from "./SearchAutocomplete";
import { ThemeToggle } from "./ThemeToggle";

export function Navbar() {
  const pathname = usePathname();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [isSearchExpanded, setIsSearchExpanded] = useState(false);
  const [activePath, setActivePath] = useState(pathname || "/");

  useEffect(() => {
    setActivePath(pathname || "/");
  }, [pathname]);

  useEffect(() => {
    if (isSearchExpanded) {
      document.body.classList.add('header-search-expanded');
    } else {
      document.body.classList.remove('header-search-expanded');
    }
    return () => document.body.classList.remove('header-search-expanded');
  }, [isSearchExpanded]);

  useEffect(() => {
    // Watch the hero search bar on the home page using IntersectionObserver
    const heroSearchBar = document.getElementById('hero-search-bar');
    
    if (heroSearchBar) {
      // Home page: show navbar search when hero search bar scrolls out of view
      const observer = new IntersectionObserver(
        ([entry]) => {
          setScrolled(!entry.isIntersecting);
        },
        { threshold: 0, rootMargin: '-80px 0px 0px 0px' }
      );
      observer.observe(heroSearchBar);
      return () => observer.disconnect();
    } else {
      // Other pages: use scroll position as fallback
      let ticking = false;
      let lastKnownScrolled = false;
      
      const handleScroll = () => {
        if (!ticking) {
          window.requestAnimationFrame(() => {
            const isScrolled = window.scrollY > 300;
            if (isScrolled !== lastKnownScrolled) {
              lastKnownScrolled = isScrolled;
              setScrolled(isScrolled);
            }
            ticking = false;
          });
          ticking = true;
        }
      };
      window.addEventListener("scroll", handleScroll, { passive: true });
      return () => window.removeEventListener("scroll", handleScroll);
    }
  }, [pathname]);

  const isActive = (path: string) => {
    if (path === "/") return activePath === "/";
    return activePath?.startsWith(path);
  };

  return (
    <nav className="sticky top-0 w-full z-50 py-2">

      
      <div className="max-w-7xl mx-auto px-[clamp(1rem,5vw,2rem)] pt-2 relative">
        <div className="flex justify-between items-center h-[clamp(3.5rem,8vw,4.5rem)]">
          {/* Logo */}
          <div className="flex-shrink-0 flex items-center">
            <Link href="/" className="flex items-center gap-2 group bg-[#ffffff] dark:bg-[#111111] px-4 py-2 rounded-full shadow-sm border border-[#f3f4f6] dark:border-[#333333]" onClick={() => setActivePath("/")}>
              <Pill className="h-[clamp(1.5rem,4vw,2rem)] w-[clamp(1.5rem,4vw,2rem)] text-[#00236f] dark:text-[#ffffff] group-hover:scale-110 transition-transform" />
              <span className="font-serif text-[clamp(1.25rem,4vw,1.75rem)] font-bold text-[#00236f] dark:text-[#ffffff] tracking-tight">
                PharmaCare
              </span>
            </Link>
          </div>

          {/* Desktop Right Side: Nav Pill + Expandable Search Icon */}
          <div className="hidden md:flex items-center space-x-2">
            
            {/* Expandable Search Icon Pill (Water Drop Splitting Effect) */}
            <AnimatePresence>
              {(scrolled || isSearchExpanded) && !pathname?.startsWith('/trends') && (
                <motion.div
                  initial={{ opacity: 0, x: 20, scale: 0.9 }}
                  animate={{ opacity: 1, x: 0, scale: 1 }}
                  exit={{ opacity: 0, x: 20, scale: 0.9 }}
                  transition={{ type: "tween", ease: "circOut", duration: 0.25 }}
                  className="relative z-10 origin-left"
                >
                  <motion.div 
                    layout
                    className={`bg-white rounded-full shadow-lg border border-gray-100 flex items-center overflow-hidden cursor-pointer transition-all duration-300 ${
                      isSearchExpanded ? 'w-[450px] p-1.5' : 'w-12 h-12 justify-center hover:bg-white hover:scale-105'
                    }`}
                    onClick={() => {
                      if (!isSearchExpanded) setIsSearchExpanded(true);
                    }}
                  >
                    {!isSearchExpanded ? (
                      <Search className="w-5 h-5 text-slate-600" />
                    ) : (
                      <div className="flex w-full items-center gap-2">
                        <div className="flex-1">
                          <SearchAutocomplete compact hideCameraIcon={pathname?.startsWith('/lab-tests')} />
                        </div>
                        <button 
                          className="p-2 text-slate-400 hover:text-slate-600 rounded-full hover:bg-slate-100 transition-colors mr-1 shrink-0"
                          onClick={(e) => {
                            e.stopPropagation();
                            setIsSearchExpanded(false);
                          }}
                        >
                          <X className="w-5 h-5" />
                        </button>
                      </div>
                    )}
                  </motion.div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Desktop Nav - Floating Pill Container */}
            <motion.div layout layoutRoot className="hidden md:flex items-center space-x-2 bg-white p-2 rounded-full shadow-lg border border-gray-100 dark:border-gray-200 relative z-20">
              {[
                { path: "/", label: "Home", icon: <Home className="h-5 w-5" /> },
                { path: "/medicines", label: "Medicines", icon: <Pill className="h-5 w-5" /> },
                { path: "/lab-tests", label: "Lab Tests", icon: <FlaskConical className="h-5 w-5" /> },
                { path: "/trends", label: "Trends", icon: <TrendingUp className="h-5 w-5" /> }
              ].map((item) => {
                const active = isActive(item.path);
                return (
                  <Link
                    key={item.path}
                    href={item.path}
                    onClick={(e) => {
                      if (active) {
                        e.preventDefault();
                      } else {
                        setActivePath(item.path);
                      }
                    }}
                    className={`relative flex items-center justify-center rounded-full transition-colors duration-200 z-10 ${
                      active 
                        ? "text-[#ffffff] px-6 py-3" 
                        : "text-gray-600 hover:text-primary hover:bg-gray-100 dark:hover:bg-gray-200 px-4 py-3"
                    }`}
                  >
                    {active && (
                      <motion.div
                        layoutId="capsule"
                        className="absolute inset-0 bg-gradient-to-r from-[#00796B] to-[#002169] rounded-full shadow-md shadow-[#00796B]/20 -z-10"
                        transition={{ type: "tween", ease: "easeOut", duration: 0.25 }}
                      />
                    )}
                    <span className="relative z-10 flex-shrink-0">{item.icon}</span>
                    <div 
                      className={`overflow-hidden transition-all duration-300 ease-in-out flex items-center ${
                        active ? "max-w-[120px] opacity-100 ml-2.5" : "max-w-0 opacity-0 ml-0"
                      }`}
                    >
                      <span className="font-bold text-[15px] whitespace-nowrap">
                        {item.label}
                      </span>
                    </div>
                  </Link>
                );
              })}
            </motion.div>
            
            {/* Theme Toggle Desktop */}
            <div className="hidden md:flex bg-white p-1 rounded-full shadow-lg border border-gray-100 dark:border-gray-200 relative z-20">
              <ThemeToggle />
            </div>
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden flex items-center bg-white rounded-full shadow-sm border border-gray-100 dark:border-gray-200 p-1 relative gap-1">
            <ThemeToggle />
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="inline-flex items-center justify-center p-2 rounded-full text-gray-700 hover:text-primary hover:bg-gray-100 dark:hover:bg-gray-200 focus:outline-none transition-colors"
            >
              <span className="sr-only">Open main menu</span>
              {isMobileMenuOpen ? (
                <X className="block h-6 w-6" aria-hidden="true" />
              ) : (
                <Menu className="block h-6 w-6" aria-hidden="true" />
              )}
            </button>

            {/* Mobile Menu Dropdown */}
            <AnimatePresence>
              {isMobileMenuOpen && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95, y: -5 }}
                  animate={{ opacity: 1, scale: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.95, y: -5 }}
                  transition={{ type: "tween", ease: "easeOut", duration: 0.2 }}
                  className="absolute top-full right-0 mt-3 w-48 bg-white/98 rounded-2xl shadow-xl border border-accent overflow-hidden z-50 origin-top-right"
                >
                  <div className="p-2 space-y-1">
                    {[
                      { path: "/", label: "Home" },
                      { path: "/medicines", label: "Medicines" },
                      { path: "/lab-tests", label: "Lab Tests" },
                      { path: "/trends", label: "Price Trends" }
                    ].map((item) => {
                      const active = isActive(item.path);
                      return (
                        <Link
                          key={item.path}
                          href={item.path}
                          onClick={() => {
                            setIsMobileMenuOpen(false);
                            setActivePath(item.path);
                          }}
                          className={`block px-4 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                            active ? "bg-primary/10 text-primary" : "text-gray-600 hover:text-primary hover:bg-gray-100 dark:hover:bg-gray-200"
                          }`}
                        >
                          {item.label}
                        </Link>
                      );
                    })}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </nav>
  );
}
