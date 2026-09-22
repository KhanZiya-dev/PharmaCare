"use client";

import Link from "next/link";
import { Pill, Menu, X, MessageCircle } from "lucide-react";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { motion } from "framer-motion";

export function Navbar() {
  const pathname = usePathname();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const isActive = (path: string) => {
    if (path === "/") return pathname === "/";
    return pathname?.startsWith(path);
  };

  return (
    <nav className="sticky top-0 w-full z-50 bg-transparent py-2">
      <div className="max-w-7xl mx-auto px-[clamp(1rem,5vw,2rem)] pt-2">
        <div className="flex justify-between items-center h-[clamp(3.5rem,8vw,4.5rem)]">
          {/* Logo */}
          <div className="flex-shrink-0 flex items-center">
            <Link href="/" className="flex items-center gap-2 group bg-white/80 backdrop-blur-md px-4 py-2 rounded-full shadow-sm border border-white/40">
              <Pill className="h-[clamp(1.5rem,4vw,2rem)] w-[clamp(1.5rem,4vw,2rem)] text-primary group-hover:scale-110 transition-transform" />
              <span className="font-serif text-[clamp(1.25rem,4vw,1.75rem)] font-bold text-primary tracking-tight">
                PharmaCare
              </span>
            </Link>
          </div>

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
                  className={`relative px-5 py-2.5 rounded-full transition-colors font-bold text-sm z-10 ${
                    active ? "text-white" : "text-slate-600 hover:text-primary hover:bg-slate-50"
                  }`}
                >
                  {active && (
                    <motion.div
                      layoutId="capsule"
                      className="absolute inset-0 bg-gradient-to-r from-teal-500 from-50% to-indigo-400 to-50% rounded-full shadow-md shadow-teal-500/20 -z-10"
                      transition={{ type: "spring", bounce: 0.1, duration: 0.4 }}
                    />
                  )}
                  {item.label}
                </Link>
              );
            })}
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden flex items-center bg-white/80 backdrop-blur-md rounded-full shadow-sm border border-white/40 p-1">
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
          </div>
        </div>
      </div>

      {/* Mobile Menu */}
      {isMobileMenuOpen && (
        <div className="md:hidden border-t border-accent bg-white/95 backdrop-blur-md absolute w-full shadow-lg">
          <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3">
            <Link
              href="/"
              onClick={() => setIsMobileMenuOpen(false)}
              className={`block px-3 py-2 rounded-md text-base font-medium ${
                isActive("/") ? "bg-primary/10 text-primary" : "text-foreground hover:text-primary hover:bg-accent/50"
              }`}
            >
              Home
            </Link>
            <Link
              href="/medicines"
              onClick={() => setIsMobileMenuOpen(false)}
              className={`block px-3 py-2 rounded-md text-base font-medium ${
                isActive("/medicines") ? "bg-primary/10 text-primary" : "text-foreground hover:text-primary hover:bg-accent/50"
              }`}
            >
              Medicines
            </Link>
            <Link
              href="/lab-tests"
              onClick={() => setIsMobileMenuOpen(false)}
              className={`block px-3 py-2 rounded-md text-base font-medium ${
                isActive("/lab-tests") ? "bg-primary/10 text-primary" : "text-foreground hover:text-primary hover:bg-accent/50"
              }`}
            >
              Lab Tests
            </Link>
            <Link
              href="/trends"
              onClick={() => setIsMobileMenuOpen(false)}
              className={`block px-3 py-2 rounded-md text-base font-medium ${
                isActive("/trends") ? "bg-primary/10 text-primary" : "text-foreground hover:text-primary hover:bg-accent/50"
              }`}
            >
              Price Trends
            </Link>
          </div>
        </div>
      )}
    </nav>
  );
}
