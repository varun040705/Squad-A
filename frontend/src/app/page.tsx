'use client';

import React, { useState } from 'react';
import { TelemetryForm } from '@/features/inspection/components/TelemetryForm';
import { InspectionCard } from '@/features/inspection/components/InspectionCard';
import { TelemetryPayload, InspectionResponse } from '@/features/inspection/types';

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<InspectionResponse | null>(null);

  const handleProcessTelemetry = async (payload: TelemetryPayload) => {
    setLoading(true);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/inspection/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error('API Request Failed');

      const data: InspectionResponse = await res.json();
      setResult(data);
    } catch (error) {
      console.error('Error connecting to backend:', error);
      alert('Failed to connect to backend server. Ensure FastAPI is running on port 8000.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 p-8 flex flex-col items-center justify-center">
      <div className="w-full max-w-2xl space-y-6">
        <h1 className="text-2xl font-bold text-center">UPV Visual Inspection Test Deck</h1>

        <TelemetryForm onSubmit={handleProcessTelemetry} isSubmitting={loading} />

        {result && <InspectionCard data={result} />}
      </div>
    </main>
  );
}
