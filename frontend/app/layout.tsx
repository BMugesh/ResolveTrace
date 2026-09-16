import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ResolveTrace — Historical Support Playbook",
  description: "Operationalizing Historical Support Decision Pathways for SpotifyCares",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body className="min-h-screen bg-[#070a13] text-slate-100 flex flex-col selection:bg-[#1DB954]/30 selection:text-[#1DB954]" suppressHydrationWarning>
        <main className="flex-1 w-full">
          {children}
        </main>
        <footer className="border-t border-white/[0.06] py-6 text-center text-xs text-slate-500 font-mono">
          ResolveTrace — Customer Support Decision Pathway Mining &amp; Safety Gating • SpotifyCares Corpus
        </footer>
      </body>
    </html>
  );
}
