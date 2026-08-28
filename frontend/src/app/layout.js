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
    icon: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" fill="none"><path d="M15 70 L30 70 L40 45 L70 45 L80 70 L95 70" stroke="%232563eb" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/><circle cx="30" cy="70" r="7" fill="%232563eb" stroke="%232563eb" stroke-width="5"/><circle cx="80" cy="70" r="7" fill="%232563eb" stroke="%232563eb" stroke-width="5"/><path d="M25 40 L45 20 L60 30 L85 10" stroke="%230ea5e9" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/><path d="M70 10 L85 10 L85 25" stroke="%230ea5e9" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  },
};

import { Toaster } from 'react-hot-toast';
import { ThemeProvider } from '../components/ThemeProvider';

export default function RootLayout({ children }) {
  return (
    <html
      lang="tr"
      suppressHydrationWarning
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 transition-colors duration-200">
        <ThemeProvider attribute="class" defaultTheme="light" storageKey="degerinde-theme" disableTransitionOnChange>
          {children}
          <Toaster position="bottom-center" />
        </ThemeProvider>
      </body>
    </html>
  );
}
