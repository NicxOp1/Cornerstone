import { cn } from "@/lib/utils/cn";

interface LogoProps {
  className?: string;
  variant?: "full" | "mark";
}

function MarkSvg({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 96 96"
      role="img"
      aria-label="Cornerstone mark"
      className={cn("h-10 w-10", className)}
    >
      <defs>
        <linearGradient id="cornerstone-mark-bg" x1="18" x2="78" y1="10" y2="84" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#FFF06A" />
          <stop offset="100%" stopColor="#F5E000" />
        </linearGradient>
      </defs>
      <rect x="8" y="8" width="80" height="80" rx="24" fill="url(#cornerstone-mark-bg)" />
      <path
        d="M31 24h11.6l8 12 8.2-12H70v48H58V44.6l-7.4 10.9h-.4l-7.2-10.7V72H31V24Z"
        fill="#2A2A8C"
      />
    </svg>
  );
}

export function Logo({ className, variant = "full" }: LogoProps) {
  if (variant === "mark") {
    return <MarkSvg className={className} />;
  }

  return (
    <div
      role="img"
      aria-label="Cornerstone Services"
      className={cn("inline-flex items-center", className)}
    >
      <img
        src="/cornerstone-logo.png"
        alt=""
        aria-hidden="true"
        className="h-full w-auto object-contain drop-shadow-[0_10px_28px_rgba(0,0,0,0.28)]"
      />
    </div>
  );
}
