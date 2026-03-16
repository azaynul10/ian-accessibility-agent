"use client";

import { useCallback, useRef } from "react";

// ─── Types ───────────────────────────────────────────────
export type StreamingCallbacks = {
  onPressStart: () => void | Promise<void>;
  onPressEnd: () => void | Promise<void>;
};

export type ButtonState = "idle" | "listening" | "processing";

interface HoldToSpeakButtonProps extends StreamingCallbacks {
  state: ButtonState;
}

// ─── Component ───────────────────────────────────────────
export default function HoldToSpeakButton({
  state,
  onPressStart,
  onPressEnd,
}: HoldToSpeakButtonProps) {
  const isPressed = useRef(false);
  const btnRef = useRef<HTMLButtonElement>(null);

  const handleEnd = useCallback(() => {
    if (!isPressed.current) return;
    isPressed.current = false;
    onPressEnd();
  }, [onPressEnd]);

  const handlePointerDown = useCallback(
    (e: React.PointerEvent) => {
      if (isPressed.current || state === "processing") return;
      // Lock the pointer to THIS element so pointerleave won't fire even if the
      // button re-renders, changes size / transform, or the finger drifts slightly.
      (e.target as HTMLElement).setPointerCapture(e.pointerId);
      isPressed.current = true;
      onPressStart();
    },
    [onPressStart, state],
  );

  const handlePointerUp = useCallback(
    (e: React.PointerEvent) => {
      (e.target as HTMLElement).releasePointerCapture(e.pointerId);
      handleEnd();
    },
    [handleEnd],
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === " " || e.key === "Enter") {
        e.preventDefault();
        if (!isPressed.current) {
          isPressed.current = true;
          onPressStart();
        }
      }
    },
    [onPressStart],
  );

  const handleKeyUp = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === " " || e.key === "Enter") {
        e.preventDefault();
        handleEnd();
      }
    },
    [handleEnd],
  );

  const isListening = state === "listening";
  const isProcessing = state === "processing";

  return (
    <div className="brutalist-card flex flex-col items-center px-5 py-8 md:py-10">
      {/* Ripple container */}
      <div className="relative flex items-center justify-center">
        {isListening && (
          <>
            <span className="animate-ripple absolute h-52 w-52 rounded-3xl border-2 border-neon opacity-30 md:h-60 md:w-60" />
            <span
              className="animate-ripple absolute h-52 w-52 rounded-3xl border-2 border-neon opacity-15 md:h-60 md:w-60"
              style={{ animationDelay: "0.5s" }}
            />
          </>
        )}

        {/* Main button — large rounded rectangle */}
        <button
          ref={btnRef}
          id="hold-to-speak-btn"
          type="button"
          aria-label={
            isListening
              ? "Release to stop speaking"
              : isProcessing
                ? "Processing your request"
                : "Hold to speak"
          }
          disabled={isProcessing}
          draggable={false}
          onDragStart={(e) => e.preventDefault()}
          onContextMenu={(e) => e.preventDefault()}
          onPointerDown={handlePointerDown}
          onPointerUp={handlePointerUp}
          onPointerCancel={handleEnd}
          onKeyDown={handleKeyDown}
          onKeyUp={handleKeyUp}
          className={`
                        relative z-10 flex h-44 w-full max-w-xs cursor-pointer select-none touch-none
                        flex-col items-center justify-center gap-3 rounded-2xl
                        border-[3px] transition-all duration-300
                        focus:outline-none focus-visible:ring-4 focus-visible:ring-neon/50
                        md:h-52 md:max-w-sm
                        ${isListening
              ? "animate-pulse-neon border-neon bg-neon/90 text-bg scale-[1.02]"
              : isProcessing
                ? "border-accent-cyan bg-accent-cyan/10 cursor-wait"
                : "border-neon bg-neon text-bg hover:bg-neon/90 active:scale-95"
            }
                    `}
        >
          {/* Icon */}
          {isProcessing ? (
            <svg
              className="animate-spin-slow h-12 w-12 text-accent-cyan md:h-16 md:w-16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
            </svg>
          ) : (
            <svg
              className={`h-12 w-12 md:h-16 md:w-16 ${isListening ? "text-bg" : "text-bg"
                }`}
              viewBox="0 0 24 24"
              fill="currentColor"
            >
              <path d="M12 14a3 3 0 0 0 3-3V5a3 3 0 0 0-6 0v6a3 3 0 0 0 3 3Z" />
              <path d="M19 11a1 1 0 0 0-2 0 5 5 0 0 1-10 0 1 1 0 0 0-2 0 7 7 0 0 0 6 6.92V21H8a1 1 0 0 0 0 2h8a1 1 0 0 0 0-2h-3v-3.08A7 7 0 0 0 19 11Z" />
            </svg>
          )}

          {/* Label */}
          <span
            className={`font-display text-sm font-bold uppercase tracking-wider md:text-base ${isListening
                ? "text-bg"
                : isProcessing
                  ? "text-accent-cyan"
                  : "text-bg"
              }`}
          >
            {isListening
              ? "Listening…"
              : isProcessing
                ? "Processing…"
                : "Hold to Speak"}
          </span>
        </button>
      </div>

      {/* Status text below button */}
      <p
        className={`mt-4 text-[11px] font-bold uppercase tracking-widest ${isListening
            ? "text-neon animate-status-pulse"
            : isProcessing
              ? "text-accent-cyan animate-status-pulse"
              : "text-text-secondary"
          }`}
      >
        {isListening
          ? "System Listening…"
          : isProcessing
            ? "Processing Request…"
            : "Press & Hold to Begin"}
      </p>
    </div>
  );
}
