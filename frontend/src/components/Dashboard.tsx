"use client";

import { useCallback } from "react";
import StatusBar from "./StatusBar";
import HoldToSpeakButton from "./HoldToSpeakButton";
import TranscriptionFeed from "./TranscriptionFeed";
import BrowserView from "./BrowserView";

import { useAgentConnection } from "@/hooks/useAgentConnection";
import { useAudioCapture } from "@/hooks/useAudioCapture";

import type { ButtonState } from "./HoldToSpeakButton";
import type { AgentStatus } from "./StatusBar";

// ─── Helpers ─────────────────────────────────────────────
function buttonStateFrom(status: AgentStatus): ButtonState {
    switch (status) {
        case "listening":
            return "listening";

        default:
            return "idle";
    }
}

// ─── Bottom Nav Item ─────────────────────────────────────
function NavItem({ icon, label }: { icon: React.ReactNode; label: string }) {
    return (
        <button
            type="button"
            className="flex flex-col items-center gap-1 text-text-secondary transition-colors hover:text-neon focus:text-neon focus:outline-none"
        >
            {icon}
            <span className="text-[9px] font-bold uppercase tracking-widest">
                {label}
            </span>
        </button>
    );
}

// ─── Component ───────────────────────────────────────────
export default function Dashboard() {
    const {
        agentStatus,
        messages,
        screenshotBase64,
        disconnect,
        sendAudioChunk,
        sendStartSpeaking,
    } = useAgentConnection();

    const { start: startMic, stop: stopMic } = useAudioCapture(sendAudioChunk);

    const handlePressStart = useCallback(async () => {
        sendStartSpeaking();
        await startMic();
    }, [sendStartSpeaking, startMic]);

    const handlePressEnd = useCallback(() => {
        stopMic();
        disconnect();
    }, [stopMic, disconnect]);

    return (
        <div className="flex h-screen w-screen flex-col bg-bg">
            {/* ── Scrollable content ── */}
            <div className="flex-1 overflow-y-auto p-3 pb-20 space-y-3 md:p-4 md:space-y-4">
                {/* Title / Status */}
                <StatusBar status={agentStatus} />

                {/* Hold-to-Speak Card */}
                <HoldToSpeakButton
                    state={buttonStateFrom(agentStatus)}
                    onPressStart={handlePressStart}
                    onPressEnd={handlePressEnd}
                />

                {/* Transcription Feed */}
                <div className="min-h-[240px]">
                    <TranscriptionFeed messages={messages} />
                </div>

                {/* Live Browser View */}
                <BrowserView base64Image={screenshotBase64} />
            </div>

            {/* ── Bottom Navigation Bar ── */}
            <nav className="fixed inset-x-0 bottom-0 z-50 flex items-center justify-around border-t-[3px] border-neon bg-bg px-2 py-3 md:py-4">
                <NavItem
                    label="Home"
                    icon={
                        <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                            <path d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-4 0a1 1 0 01-1-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 01-1 1" />
                        </svg>
                    }
                />
                <NavItem
                    label="Activity"
                    icon={
                        <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
                        </svg>
                    }
                />
                <NavItem
                    label="Options"
                    icon={
                        <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                            <circle cx="12" cy="12" r="3" />
                            <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 01-2.83 2.83l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z" />
                        </svg>
                    }
                />
                <NavItem
                    label="Support"
                    icon={
                        <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                            <circle cx="12" cy="12" r="10" />
                            <path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3" />
                            <line x1="12" y1="17" x2="12.01" y2="17" />
                        </svg>
                    }
                />
            </nav>
        </div>
    );
}
