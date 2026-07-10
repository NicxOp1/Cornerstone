"use client";

import { useRef, useState } from "react";
import { cn } from "@/lib/utils/cn";

const BAR_COUNT = 56;

function barHeights(seed: string): number[] {
  let hash = 2166136261;
  for (let i = 0; i < seed.length; i += 1) {
    hash = (hash ^ seed.charCodeAt(i)) >>> 0;
    hash = (hash * 16777619) >>> 0;
  }

  const heights: number[] = [];
  for (let i = 0; i < BAR_COUNT; i += 1) {
    hash = (hash * 1103515245 + 12345) & 0x7fffffff;
    heights.push(0.28 + ((hash % 1000) / 1000) * 0.72);
  }
  return heights;
}

function formatClock(seconds: number): string {
  const safe = Number.isFinite(seconds) ? Math.max(0, Math.floor(seconds)) : 0;
  const minutes = Math.floor(safe / 60);
  return `${minutes}:${String(safe % 60).padStart(2, "0")}`;
}

interface WaveformPlayerProps {
  recordingUrl: string;
  seed: string;
  durationS: number;
}

export function WaveformPlayer({ recordingUrl, seed, durationS }: WaveformPlayerProps) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [audioError, setAudioError] = useState(false);
  const [playing, setPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [current, setCurrent] = useState(0);
  const [speed, setSpeed] = useState(1);
  const bars = barHeights(seed || "harmony");

  if (!recordingUrl || audioError) {
    return (
      <div className="rounded-[24px] border border-dashed border-line bg-muted/40 p-8 text-center text-sm text-ink-soft">
        Recording unavailable for this call.
      </div>
    );
  }

  function toggle() {
    const audio = audioRef.current;
    if (!audio) return;

    if (audio.paused) {
      setAudioError(false);
      void audio.play();
      setPlaying(true);
    } else {
      audio.pause();
      setPlaying(false);
    }
  }

  function onTimeUpdate() {
    const audio = audioRef.current;
    if (!audio) return;
    const total = audio.duration || durationS || 1;
    setProgress(Math.min(1, audio.currentTime / total));
    setCurrent(audio.currentTime);
  }

  function seek(event: React.MouseEvent<HTMLDivElement>) {
    const audio = audioRef.current;
    if (!audio) return;
    const rect = event.currentTarget.getBoundingClientRect();
    const ratio = Math.min(1, Math.max(0, (event.clientX - rect.left) / rect.width));
    audio.currentTime = ratio * (audio.duration || durationS || 0);
  }

  function cycleSpeed() {
    const next = speed === 1 ? 1.5 : speed === 1.5 ? 2 : 1;
    setSpeed(next);
    if (audioRef.current) {
      audioRef.current.playbackRate = next;
    }
  }

  const total = durationS || 0;

  return (
    <div className="flex flex-col gap-4 rounded-[24px] bg-navy p-5 text-white shadow-panel sm:flex-row sm:items-center">
      <button
        type="button"
        onClick={toggle}
        aria-label={playing ? "Pause" : "Play"}
        className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-accent text-accent-ink transition hover:brightness-95"
      >
        {playing ? (
          <svg viewBox="0 0 24 24" className="h-5 w-5" fill="currentColor">
            <rect x="6" y="5" width="4" height="14" rx="1" />
            <rect x="14" y="5" width="4" height="14" rx="1" />
          </svg>
        ) : (
          <svg viewBox="0 0 24 24" className="h-5 w-5" fill="currentColor">
            <path d="M8 5v14l11-7z" />
          </svg>
        )}
      </button>

      <div
        onClick={seek}
        className="flex h-14 flex-1 cursor-pointer items-center gap-[3px]"
        role="presentation"
      >
        {bars.map((height, index) => {
          const played = index / BAR_COUNT <= progress;
          return (
            <span
              key={index}
              className={cn("w-full rounded-full transition-colors", played ? "bg-accent" : "bg-white/25")}
              style={{ height: `${Math.round(height * 100)}%` }}
            />
          );
        })}
      </div>

      <div className="flex items-center gap-4 sm:flex-col sm:items-end">
        <span className="text-sm tabular-nums text-white/80">
          {formatClock(current)} / {formatClock(total)}
        </span>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={cycleSpeed}
            className="rounded-full bg-white/10 px-3 py-1 text-xs font-semibold text-white transition hover:bg-white/20"
          >
            {speed}x
          </button>
          <a
            href={recordingUrl}
            download
            className="rounded-full bg-white/10 px-3 py-1 text-xs font-semibold text-white transition hover:bg-white/20"
          >
            Download
          </a>
        </div>
      </div>

      <audio
        ref={audioRef}
        src={recordingUrl}
        onError={() => {
          setAudioError(true);
          setPlaying(false);
        }}
        onTimeUpdate={onTimeUpdate}
        onEnded={() => setPlaying(false)}
        className="hidden"
      />
    </div>
  );
}
