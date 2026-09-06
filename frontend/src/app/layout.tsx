import type { Metadata } from "next";
import { Inter, DM_Serif_Display } from "next/font/google";
import { Footer } from "@/components/Footer";
import { MessageCircle } from "lucide-react";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const dmSerifDisplay = DM_Serif_Display({
  variable: "--font-dm-serif",
  weight: "400",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "PharmaCare — Smart Prices, Better Health",
  description:
    "Compare medicine and lab test prices across top Indian e-pharmacies. View 30-day price history, spot fake discounts, and find the best deals.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${dmSerifDisplay.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col font-sans">
        {children}
        <Footer />

        {/* Global Sticky WhatsApp FAB */}
        <a
          href="https://wa.me/1234567890"
          target="_blank"
          rel="noopener noreferrer"
          className="fixed bottom-6 right-6 z-50 bg-[#25D366] hover:bg-[#1DA851] text-white p-4 rounded-full shadow-lg hover:shadow-xl transition-all hover:-translate-y-1 group"
          aria-label="WhatsApp Support"
        >
          <MessageCircle className="h-6 w-6" />
          {/* Tooltip */}
          <span className="absolute right-full mr-3 top-1/2 -translate-y-1/2 bg-gray-900 text-white text-xs font-medium px-3 py-1.5 rounded-lg whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
            Need help? Chat with us
          </span>
        </a>
      </body>
    </html>
  );
}
