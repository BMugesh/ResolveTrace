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
    <html lang="en" className="dark">
      <body className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
        <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-9 h-9 rounded-full bg-[#1DB954] flex items-center justify-center font-bold text-black text-xl shadow-lg shadow-green-500/20">
                ♫
              </div>
              <div>
                <span className="font-bold text-lg text-white tracking-tight">ResolveTrace</span>
                <span className="ml-2 px-2 py-0.5 text-xs font-semibold rounded bg-[#1DB954]/20 text-[#1DB954] border border-[#1DB954]/30">SpotifyCares</span>
              </div>
            </div>
            <div className="flex items-center space-x-4 text-xs text-slate-400">
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                <span>FastAPI Engine: 8000</span>
              </span>
              <a
                href="https://github.com/BMugesh/ResolveTrace"
                target="_blank"
                rel="noreferrer"
                className="hover:text-white transition-colors"
              >
                GitHub Repo ↗
              </a>
            </div>
          </div>
        </header>
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>
        <footer className="border-t border-slate-800/80 py-6 text-center text-xs text-slate-500">
          ResolveTrace — Customer Support Decision Pathway Mining & Safety Gating • SpotifyCares Corpus
        </footer>
      </body>
    </html>
  );
}
