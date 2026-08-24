"use client";

import Link from "next/link";
import { Pill, Menu, X, MessageCircle } from "lucide-react";
import { useState } from "react";

export function Navbar() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

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
          <div className="hidden md:flex items-center space-x-8">
            <Link href="/medicines" className="text-foreground hover:text-primary transition-colors font-medium">
              Medicines
            </Link>
            <Link href="/lab-tests" className="text-foreground hover:text-primary transition-colors font-medium">
              Lab Tests
            </Link>
            <Link href="/trends" className="text-foreground hover:text-primary transition-colors font-medium">
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
              className="block px-3 py-2 text-base font-medium text-foreground hover:text-primary hover:bg-accent/30 rounded-md"
            >
              Medicines
            </Link>
            <Link
              href="/lab-tests"
              className="block px-3 py-2 text-base font-medium text-foreground hover:text-primary hover:bg-accent/30 rounded-md"
            >
              Lab Tests
            </Link>
            <Link
              href="/trends"
              className="block px-3 py-2 text-base font-medium text-foreground hover:text-primary hover:bg-accent/30 rounded-md"
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
