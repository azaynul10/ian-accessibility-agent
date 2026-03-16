"use client";

interface BrowserViewProps {
    /** Base64-encoded screenshot from the Playwright agent. */
    base64Image?: string;
}

export default function BrowserView({ base64Image }: BrowserViewProps) {
    return (
        <div className="brutalist-card flex flex-col overflow-hidden">
            {/* Title bar */}
            <div className="flex items-center justify-between border-b-[3px] border-neon px-4 py-3">
                <h2 className="font-display text-sm font-bold uppercase tracking-tight text-neon md:text-base">
                    Live Browser Automation View
                </h2>
                {/* Traffic lights */}
                <div className="flex gap-1.5">
                    <span className="h-3 w-3 rounded-full bg-danger/80" />
                    <span className="h-3 w-3 rounded-full bg-neon/80" />
                    <span className="h-3 w-3 rounded-full bg-success/80" />
                </div>
            </div>

            {/* Screenshot / Placeholder */}
            <div className="relative min-h-[220px] bg-bg flex-1 md:min-h-[300px]">
                {base64Image ? (
                    <img
                        id="browser-automation-screenshot"
                        src={`data:image/jpeg;base64,${base64Image}`}
                        alt="Live Browser Automation View"
                        className="h-full w-full object-contain"
                    />
                ) : (
                    <div className="flex h-full min-h-[220px] items-center justify-center md:min-h-[300px]">
                        <div className="flex flex-col items-center gap-4 text-center">
                            {/* Monitor icon */}
                            <svg
                                className="h-16 w-16 text-neon/15"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth={1.5}
                            >
                                <rect x="2" y="3" width="20" height="14" rx="2" />
                                <path d="M8 21h8M12 17v4" />
                            </svg>
                            <p className="text-sm text-text-secondary max-w-xs">
                                The browser feed will appear once the agent begins navigating.
                            </p>
                            <div className="animate-pulse-neon mt-1 h-1 w-20 rounded-full bg-neon/20" />
                        </div>
                    </div>
                )}
            </div>

            {/* Status chips */}
            <div className="flex items-center justify-between border-t-[3px] border-neon px-4 py-2.5">
                <div className="flex items-center gap-1.5">
                    <span className={`h-1.5 w-1.5 rounded-full ${base64Image ? "bg-success animate-status-pulse" : "bg-text-secondary"}`} />
                    <span className="text-[10px] font-bold uppercase tracking-widest text-text-secondary">
                        Viewport Status: {base64Image ? "Active" : "Idle"}
                    </span>
                </div>
                <span className="text-[10px] font-bold uppercase tracking-widest text-text-secondary">
                    OCR {base64Image ? "Engaged" : "Standby"}
                </span>
            </div>
        </div>
    );
}
