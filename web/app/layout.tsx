import type { Metadata } from "next";
import type { ReactNode } from "react";
import { Outfit, Plus_Jakarta_Sans } from "next/font/google";

import "./globals.css";

const outfit = Outfit({
  subsets: ["latin", "latin-ext"],
  variable: "--font-heading",
  weight: ["700", "800"],
});

const plusJakarta = Plus_Jakarta_Sans({
  subsets: ["latin", "latin-ext"],
  variable: "--font-body",
});

export const metadata: Metadata = {
  title: "Nền tảng quản lý bảo hiểm",
  description: "Không gian vận hành nghiệp vụ bảo hiểm",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <html lang="vi">
      <body
        className={`${outfit.variable} ${plusJakarta.variable} font-sans antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
