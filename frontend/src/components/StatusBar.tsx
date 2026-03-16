"use client";

export type AgentStatus =
    | "idle"
    | "listening"
    | "navigating"
    | "awaiting_confirmation";

interface StatusBarProps {
    status: AgentStatus;
}

const STATUS_LABEL: Record<AgentStatus, string> = {
    idle: "SYSTEM READY",
    listening: "SYSTEM LISTENING…",
    navigating: "NAVIGATING…",
    awaiting_confirmation: "AWAITING CONFIRMATION",
};

export default function StatusBar({ status }: StatusBarProps) {
    const label = STATUS_LABEL[status] ?? STATUS_LABEL["idle"];
    const isActive = status !== "idle";

    return (
        <header
            id="status-bar"
            className="brutalist-card px-5 py-4 md:px-6 md:py-5"
        >
            {/* Title */}
            <h1 className="font-display text-2xl md:text-3xl font-bold uppercase leading-tight tracking-tight text-neon">
                Intelligent
                <br />
                Accessibility
                <br />
                Navigator
            </h1>

            {/* Status line */}
            <div className="mt-3 flex items-center gap-2">
                <span
                    className={`h-2 w-2 rounded-full ${isActive ? "bg-neon animate-status-pulse" : "bg-text-secondary"
                        }`}
                />
                <span
                    className={`text-[11px] font-bold uppercase tracking-widest ${isActive ? "text-neon" : "text-text-secondary"
                        }`}
                >
                    {label}
                </span>
            </div>
        </header>
    );
}
