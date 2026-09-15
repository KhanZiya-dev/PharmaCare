"use client";

import Link from "next/link";
import { Pill, Menu, X, MessageCircle } from "lucide-react";
import { usePathname } from "next/navigation";
import { useState } from "react";

export function Navbar() {
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
              href="/" 
              className={`px-4 py-2 rounded-full transition-all font-medium ${isActive("/") ? "bg-primary/10 text-primary" : "text-foreground hover:bg-accent/50 hover:text-primary"}`}
            >
              Home
            </Link>
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



        </div>
      </div>
    </nav>
  );
}
