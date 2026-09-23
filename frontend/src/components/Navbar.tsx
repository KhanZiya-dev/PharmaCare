"use client";

import Link from "next/link";
import { Pill, Menu, X, MessageCircle } from "lucide-react";
import { usePathname } from "next/navigation";
import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { SearchAutocomplete } from "./SearchAutocomplete";

export function Navbar() {
  const pathname = usePathname();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [activePath, setActivePath] = useState(pathname || "/");

  useEffect(() => {
    setActivePath(pathname || "/");
  }, [pathname]);

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
      {/* Pure Blur fading from 30% opacity at top to 0% at bottom */}
      <div className="absolute top-0 left-0 right-0 h-[120px] backdrop-blur-md [mask-image:linear-gradient(to_bottom,rgba(0,0,0,0.3)_0%,transparent_100%)] -z-10 pointer-events-none transform-gpu will-change-transform" />
      
      <div className="max-w-7xl mx-auto px-[clamp(1rem,5vw,2rem)] pt-2 relative">
        <div className="flex justify-between items-center h-[clamp(3.5rem,8vw,4.5rem)]">
          {/* Logo */}
          <div className="flex-shrink-0 flex items-center">
            <Link href="/" className="flex items-center gap-2 group bg-white/80 backdrop-blur-md px-4 py-2 rounded-full shadow-sm border border-white/40" onClick={() => setActivePath("/")}>
              <Pill className="h-[clamp(1.5rem,4vw,2rem)] w-[clamp(1.5rem,4vw,2rem)] text-primary group-hover:scale-110 transition-transform" />
              <span className="font-serif text-[clamp(1.25rem,4vw,1.75rem)] font-bold text-primary tracking-tight">
                PharmaCare
              </span>
            </Link>
          </div>

          {/* Scroll Search Bar */}
          <AnimatePresence>
            {scrolled && !pathname?.startsWith('/trends') && (
              <motion.div
                initial={{ opacity: 0, y: -20, scale: 0.9, filter: 'blur(8px)' }}
                animate={{ opacity: 1, y: 0, scale: 1, filter: 'blur(0px)' }}
                exit={{ opacity: 0, y: -12, scale: 0.95, filter: 'blur(4px)' }}
                transition={{ type: "spring", stiffness: 400, damping: 25, mass: 0.8 }}
                className="hidden lg:block flex-1 max-w-md mx-8"
              >
                <SearchAutocomplete compact hideCameraIcon={pathname?.startsWith('/lab-tests')} />
              </motion.div>
            )}
          </AnimatePresence>

          {/* Desktop Nav - Floating Pill Container */}
          <div className="hidden md:flex items-center space-x-1 bg-white/80 backdrop-blur-md p-1.5 rounded-full shadow-lg border border-white/50 relative">
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
                  onClick={(e) => {
                    if (active) {
                      e.preventDefault();
                    } else {
                      setActivePath(item.path);
                    }
                  }}
                  className={`relative px-5 py-2.5 rounded-full transition-colors font-bold text-sm z-10 ${
                    active ? "text-white" : "text-slate-600 hover:text-primary hover:bg-slate-50"
                  }`}
                >
                  {active && (
                    <motion.div
                      layoutId="capsule"
                      className="absolute inset-0 bg-gradient-to-r from-[#00796B] to-[#002169] rounded-full shadow-md shadow-[#00796B]/20 -z-10"
                      transition={{ type: "spring", bounce: 0.2, duration: 0.5 }}
                    />
                  )}
                  <span className="relative z-10">{item.label}</span>
                </Link>
              );
            })}
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden flex items-center bg-white/80 backdrop-blur-md rounded-full shadow-sm border border-white/40 p-1 relative">
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="inline-flex items-center justify-center p-2 rounded-full text-slate-700 hover:text-primary hover:bg-slate-100 focus:outline-none transition-colors"
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
                  initial={{ opacity: 0, scale: 0.9, y: -10 }}
                  animate={{ opacity: 1, scale: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.9, y: -10 }}
                  transition={{ type: "spring", stiffness: 300, damping: 25 }}
                  className="absolute top-full right-0 mt-3 w-48 bg-white/95 backdrop-blur-xl rounded-2xl shadow-xl border border-accent overflow-hidden z-50 origin-top-right"
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
                            active ? "bg-primary/10 text-primary" : "text-slate-600 hover:text-primary hover:bg-slate-50"
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
