"use client";

import Link from "next/link";
import { Pill, Menu, X, MessageCircle } from "lucide-react";
import { usePathname } from "next/navigation";
import { useState } from "react";

export function Navbar() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const pathname = usePathname();

  const isActive = (path: string) => {
    if (path === "/") return pathname === "/";
    return pathname?.startsWith(path);
  };

  return (
    <nav className="sticky top-0 z-50 w-full backdrop-blur-md bg-white/80 border-b border-accent">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex-shrink-0 flex items-center">
            <Link href="/" className="flex items-center gap-2 group">
              <Pill className="h-8 w-8 text-primary group-hover:scale-110 transition-transform" />
              <span className="font-serif text-2xl font-bold text-primary tracking-tight">
                PharmaCare
              </span>
            </Link>
          </div>

          {/* Desktop Nav */}
          <div className="hidden md:flex items-center space-x-2">
            <Link 
              href="/medicines" 
              className={`px-4 py-2 rounded-full transition-all font-medium ${isActive("/medicines") ? "bg-primary/10 text-primary" : "text-foreground hover:bg-accent/50 hover:text-primary"}`}
            >
              Medicines
            </Link>
            <Link 
              href="/lab-tests" 
              className={`px-4 py-2 rounded-full transition-all font-medium ${isActive("/lab-tests") ? "bg-primary/10 text-primary" : "text-foreground hover:bg-accent/50 hover:text-primary"}`}
            >
              Lab Tests
            </Link>
            <Link 
              href="/trends" 
              className={`px-4 py-2 rounded-full transition-all font-medium ${isActive("/trends") ? "bg-primary/10 text-primary" : "text-foreground hover:bg-accent/50 hover:text-primary"}`}
            >
              Price Trends
            </Link>
          </div>

          {/* WhatsApp Support Button */}
          <div className="hidden md:flex items-center">
            <a
              href="https://wa.me/1234567890"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 bg-[#25D366] hover:bg-[#1DA851] text-white px-4 py-2 rounded-full font-medium transition-all shadow-sm hover:shadow-md hover:-translate-y-0.5"
            >
              <MessageCircle className="h-5 w-5" />
              <span>Support</span>
            </a>
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden flex items-center">
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="text-foreground hover:text-primary focus:outline-none"
            >
              {isMenuOpen ? (
                <X className="h-6 w-6" />
              ) : (
                <Menu className="h-6 w-6" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu */}
      {isMenuOpen && (
        <div className="md:hidden bg-white border-t border-accent absolute w-full">
          <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3 shadow-lg">
            <Link
              href="/medicines"
              className={`block px-3 py-2 text-base font-medium rounded-md ${isActive("/medicines") ? "text-primary bg-accent/50" : "text-foreground hover:text-primary hover:bg-accent/30"}`}
              onClick={() => setIsMenuOpen(false)}
            >
              Medicines
            </Link>
            <Link
              href="/lab-tests"
              className={`block px-3 py-2 text-base font-medium rounded-md ${isActive("/lab-tests") ? "text-primary bg-accent/50" : "text-foreground hover:text-primary hover:bg-accent/30"}`}
              onClick={() => setIsMenuOpen(false)}
            >
              Lab Tests
            </Link>
            <Link
              href="/trends"
              className={`block px-3 py-2 text-base font-medium rounded-md ${isActive("/trends") ? "text-primary bg-accent/50" : "text-foreground hover:text-primary hover:bg-accent/30"}`}
              onClick={() => setIsMenuOpen(false)}
            >
              Price Trends
            </Link>
            <a
              href="https://wa.me/1234567890"
              target="_blank"
              rel="noopener noreferrer"
              className="mt-4 flex w-full items-center justify-center gap-2 bg-[#25D366] text-white px-4 py-2 rounded-full font-medium"
            >
              <MessageCircle className="h-5 w-5" />
              <span>WhatsApp Support</span>
            </a>
          </div>
        </div>
      )}
    </nav>
  );
}
