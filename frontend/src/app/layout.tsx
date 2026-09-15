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

      </body>
    </html>
  );
}
