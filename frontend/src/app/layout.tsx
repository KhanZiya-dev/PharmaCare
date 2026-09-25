import type { Metadata } from "next";
import { Inter, DM_Serif_Display } from "next/font/google";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { MessageCircle } from "lucide-react";
import { Toaster } from "sonner";
import NextTopLoader from 'nextjs-toploader';
import { ThemeProvider } from "@/components/ThemeProvider";
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
      suppressHydrationWarning
    >
      <body className="min-h-full flex flex-col font-sans">
        <ThemeProvider>
          <NextTopLoader color="#00796B" showSpinner={false} height={3} shadow="0 0 10px #00796B,0 0 5px #00796B" />
          <Navbar />
          {children}
          <Footer />
          <Toaster position="bottom-center" toastOptions={{ style: { background: '#333', color: '#fff', border: 'none' } }} />
        </ThemeProvider>
      </body>
    </html>
  );
}
