import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Cornerstone - Dashboard de Harmony",
  description: "Metricas y llamadas del agente de voz Harmony para Cornerstone Services."
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
