import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Hunar Hiring Assistant",
  description: "Voice-AI-powered screening and candidate reachout",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="min-h-screen flex flex-col">
          <header className="border-b border-border">
            <div className="max-w-5xl mx-auto flex items-center justify-between px-4 py-3">
              <Link href="/" className="font-semibold">Hunar Hiring Assistant</Link>
              <nav className="flex gap-4 text-sm">
                <Link href="/screenings" className="hover:underline">Screenings</Link>
                <Link href="/reachout" className="hover:underline">People Search &amp; Reachout</Link>
              </nav>
            </div>
          </header>
          <main className="flex-1 max-w-5xl mx-auto w-full px-4 py-8">{children}</main>
        </div>
      </body>
    </html>
  );
}
