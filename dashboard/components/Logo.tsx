import { cn } from "@/lib/utils/cn";

interface LogoProps {
  /**
   * "onLight" (fondo claro: topbar/login) pinta el wordmark en navy.
   * "onDark" (fondo navy: sidebar) lo pinta en amarillo para contraste.
   */
  tone?: "onLight" | "onDark";
  className?: string;
}

const NAVY = "#2A2A8C";
const YELLOW = "#F5E000";

/**
 * Wordmark de Cornerstone Services reproducido en SVG con la paleta de marca.
 * Para usar el logo raster exacto en su lugar, dejar el PNG en
 * `public/cornerstone-logo.png` y reemplazar este SVG por un <Image>.
 */
export function Logo({ tone = "onLight", className }: LogoProps) {
  const wordFill = tone === "onDark" ? YELLOW : NAVY;
  const wordStroke = tone === "onDark" ? "#1E1B4B" : YELLOW;

  return (
    <svg
      viewBox="0 0 960 300"
      role="img"
      aria-label="Cornerstone Services"
      className={cn("h-9 w-auto", className)}
    >
      {/* Swoosh superior */}
      <path
        fill={YELLOW}
        d="M470 44 C 650 4, 838 14, 924 96 C 828 44, 652 46, 502 70 C 490 62, 478 52, 470 44 Z"
      />
      {/* Swoosh inferior (barrido principal) */}
      <path
        fill={YELLOW}
        d="M36 206 C 300 250, 664 250, 918 156 C 712 224, 344 224, 128 190 C 84 184, 52 192, 36 206 Z"
      />
      {/* Wordmark */}
      <text
        x="480"
        y="168"
        textAnchor="middle"
        fontFamily="'Arial Black', 'Arial Narrow', Impact, sans-serif"
        fontWeight="900"
        fontSize="118"
        letterSpacing="-4"
        fill={wordFill}
        stroke={wordStroke}
        strokeWidth="3"
        paintOrder="stroke"
      >
        CORNERSTONE
      </text>
      {/* Barra + SERVICES + LLC */}
      <rect x="352" y="242" width="212" height="12" fill={YELLOW} />
      <text
        x="584"
        y="262"
        fontFamily="'Arial Black', 'Arial Narrow', Impact, sans-serif"
        fontWeight="900"
        fontSize="44"
        letterSpacing="6"
        fill={wordFill}
        stroke={wordStroke}
        strokeWidth="1.5"
        paintOrder="stroke"
      >
        SERVICES
      </text>
      <text
        x="892"
        y="258"
        fontFamily="'Arial Black', sans-serif"
        fontWeight="900"
        fontSize="18"
        fill={wordFill}
      >
        LLC
      </text>
    </svg>
  );
}
