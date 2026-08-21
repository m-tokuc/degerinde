import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata = {
  title: "Değerinde | Yapay Zeka Destekli Araç Değerleme",
  description: "Gelişmiş yapay zeka algoritmaları ile saniyeler içinde aracınızın güncel piyasa değerini, fiyat aralığını ve donanım etkilerini öğrenin.",
  icons: {
    icon: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100" height="100" rx="20" fill="%232563eb"/><path d="M30 50 L45 65 L70 35" stroke="white" stroke-width="10" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  },
};

import { Toaster } from 'react-hot-toast';

export default function RootLayout({ children }) {
  return (
    <html
      lang="tr"
      suppressHydrationWarning
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-slate-50">
        {children}
        <Toaster position="bottom-center" />
      </body>
    </html>
  );
}
