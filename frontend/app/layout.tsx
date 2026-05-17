import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "The Whiteboard",
  description: "Football analytics",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body
        className={`${inter.className} bg-[#1a1a2e] text-gray-100 min-h-screen`}
      >
        <header className="border-b border-gray-800 px-6 py-4">
          <h1 className="text-xl font-bold tracking-tight">The Whiteboard</h1>
        </header>
        <main className="max-w-5xl mx-auto px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
