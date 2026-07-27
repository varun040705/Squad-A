import './globals.css';
import React from 'react';

export const metadata = {
  title: 'UPV Visual Inspection',
  description: 'Telemetry Analysis and SOP Inspection System',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-slate-950 text-slate-100 min-h-screen antialiased">
        {children}
      </body>
    </html>
  );
}
