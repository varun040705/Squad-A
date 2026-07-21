import { SurfaceResistivityDashboard } from '@/features/surface-resistivity/components/SurfaceResistivityDashboard';

export default function Home() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <main className="flex-1 w-full">
        <SurfaceResistivityDashboard />
      </main>
      <footer className="border-t border-slate-900 py-6 text-center text-xs text-slate-500 bg-slate-950">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row justify-between items-center gap-2">
          <span>OX1 Structural Health Monitoring System · Squad A</span>
          <span className="font-mono">Developed in React 19 / Next.js 16</span>
        </div>
      </footer>
    </div>
  );
}

