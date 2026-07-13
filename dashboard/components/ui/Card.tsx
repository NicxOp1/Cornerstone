import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils/cn";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  padded?: boolean;
}

export function Card({ className, padded = true, ...props }: CardProps) {
  return (
    <div
      className={cn(
        "rounded-[28px] border border-line/80 bg-card shadow-panel",
        padded && "p-5 md:p-6",
        className
      )}
      {...props}
    />
  );
}
