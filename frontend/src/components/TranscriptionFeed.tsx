"use client";

import { useEffect, useRef } from "react";

// ─── Types ───────────────────────────────────────────────
export interface TranscriptionMessage {
    id: string;
    role: "user" | "agent";
    text: string;
}

interface TranscriptionFeedProps {
    messages: TranscriptionMessage[];
}

// ─── Component ───────────────────────────────────────────
export default function TranscriptionFeed({
    messages,
}: TranscriptionFeedProps) {
    // THE FIX: Use a ref on the scrolling container, NOT the bottom element
    const scrollContainerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        // THE FIX: Safely scroll ONLY the inside of this specific div.
        // This prevents the entire webpage from jumping and dragging the mic button away!
        if (scrollContainerRef.current) {
            scrollContainerRef.current.scrollTop = scrollContainerRef.current.scrollHeight;
        }
    }, [messages]);

    return (
        <div className="brutalist-card flex flex-1 flex-col overflow-hidden max-h-[400px]">
            {/* Header */}
            <div className="flex items-center gap-2 border-b-[3px] border-neon px-4 py-3 shrink-0">
                <div className="h-2 w-2 rounded-full bg-neon animate-status-pulse" />
                <h2 className="font-display text-base font-bold uppercase tracking-tight text-neon md:text-lg">
                    Live Transcription Feed
                </h2>
            </div>

            {/* Messages */}
            {/* THE FIX: Attach the ref to this overflow container */}
            <div 
                ref={scrollContainerRef} 
                className="flex-1 overflow-y-auto p-4 space-y-4 scroll-smooth"
            >
                {messages.length === 0 && (
                    <p className="text-center text-sm text-text-secondary italic py-8">
                        Hold the microphone button and speak to begin…
                    </p>
                )}

                {messages.map((msg) => (
                    <div
                        key={msg.id}
                        className="animate-float-in flex items-start gap-3"
                    >
                        {/* Role icon */}
                        <div
                            className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border-2 text-xs font-bold ${msg.role === "user"
                                    ? "border-neon bg-neon/10 text-neon"
                                    : "border-accent-cyan bg-accent-cyan/10 text-accent-cyan"
                                }`}
                        >
                            {msg.role === "user" ? "👤" : "🤖"}
                        </div>

                        {/* Content */}
                        <div className="flex-1 min-w-0">
                            <span
                                className={`block text-[10px] font-bold uppercase tracking-widest mb-1 ${msg.role === "user"
                                        ? "text-neon/70"
                                        : "text-accent-cyan/70"
                                    }`}
                            >
                                {msg.role === "user" ? "User" : "Agent"}
                            </span>
                            <p className="font-display text-base font-bold leading-snug text-text-primary md:text-lg">
                                {msg.text}
                            </p>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
