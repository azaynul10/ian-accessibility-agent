"use client";

import { useRef, useCallback, useState, useEffect } from "react";
import type { AgentStatus } from "@/components/StatusBar";
import type { TranscriptionMessage } from "@/components/TranscriptionFeed";

// ─── AG-UI event shapes ──────────────────────────────────
interface TextMessageContentEvent {
    type: "TextMessageContent";
    data: {
        role: "user" | "agent";
        text: string;
        messageId?: string;
    };
}

interface ActivitySnapshotEvent {
    type: "ActivitySnapshot";
    data: {
        status?: AgentStatus;
        activityType?: string;
        content?: { base64: string };
    };
}

interface ErrorEvent {
    type: "Error" | "RunError";
    data: {
        message: string;
    };
}

type AgUiEvent = TextMessageContentEvent | ActivitySnapshotEvent | ErrorEvent;

// ─── Hook ────────────────────────────────────────────────
const WS_URL = "wss://ian-backend-service-595627512045.us-central1.run.app/ag-ui";

export function useAgentConnection() {
    const wsRef = useRef<WebSocket | null>(null);
    const [agentStatus, setAgentStatus] = useState<AgentStatus>("idle");
    const [messages, setMessages] = useState<TranscriptionMessage[]>([]);
    const [screenshotBase64, setScreenshotBase64] = useState<string | undefined>(undefined);

    // Connect WebSocket eagerly on mount so it's ready when the user presses the button.
    // Cloud Run cold starts can take seconds — we can't wait until button press!
    useEffect(() => {
        connect();
        return () => {
            if (wsRef.current) {
                console.log("[AG-UI] Cleaning up old WebSocket connection...");
                wsRef.current.close();
                wsRef.current = null;
            }
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // ── Dispatch incoming AG-UI events ──────────────────────
    const handleMessage = useCallback((event: MessageEvent) => {
        let parsed: AgUiEvent;
        try {
            parsed = JSON.parse(event.data);
        } catch {
            console.warn("[AG-UI] Non-JSON message:", event.data);
            return;
        }

        switch (parsed.type) {
            case "TextMessageContent": {
                const { role, text, messageId } = parsed.data;
                const msg: TranscriptionMessage = {
                    id: messageId ?? crypto.randomUUID(),
                    role,
                    text,
                };
                setMessages((prev) => [...prev, msg]);
                break;
            }

            case "ActivitySnapshot": {
                // Screenshot snapshot — update the live image
                if (parsed.data.activityType === "SCREENSHOT" && parsed.data.content) {
                    setScreenshotBase64(parsed.data.content.base64);
                } else if (parsed.data.status) {
                    setAgentStatus(parsed.data.status);
                }
                break;
            }

            case "Error":
            case "RunError": {
                console.error("[AG-UI] Backend error:", parsed.data.message);
                setAgentStatus("idle");
                break;
            }

            default:
                console.log("[AG-UI] Unhandled event type:", (parsed as { type: string }).type);
        }
    }, []);

    // ── Connect ─────────────────────────────────────────────
    const connect = useCallback(() => {
        // Prevent ghost sockets from stacking up
        if (wsRef.current && wsRef.current.readyState <= WebSocket.OPEN) {
            console.log("[AG-UI] WebSocket already connecting/open. Skipping.");
            return;
        }

        console.log("[AG-UI] Opening new WebSocket connection...");
        const ws = new WebSocket(WS_URL);

        ws.onopen = () => {
            console.log("[AG-UI] Connected and ready");
            // Don't set status here — status changes on button press
        };

        ws.onmessage = handleMessage;

        ws.onclose = () => {
            console.log("[AG-UI] Disconnected");
            if (wsRef.current === ws) {
                wsRef.current = null;
                setAgentStatus("idle");
                setScreenshotBase64(undefined);
            }
        };

        ws.onerror = (err) => {
            console.error("[AG-UI] WebSocket error:", err);
        };

        wsRef.current = ws;
    }, [handleMessage]);

    // ── Signal end of audio (keep WS open for responses) ──
    const disconnect = useCallback(() => {
        if (wsRef.current) {
            if (wsRef.current.readyState === WebSocket.OPEN) {
                console.log("[AG-UI] Sending EndOfAudio signal to trigger LLM response...");
                wsRef.current.send(JSON.stringify({ type: "EndOfAudio" }));
                setAgentStatus("navigating");
            } else {
                console.warn("[AG-UI] Could not send EndOfAudio, socket is closed!");
            }
        }
    }, []);

    // ── Signal start of speaking ─────────────────────────────
    const sendStartSpeaking = useCallback(() => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            console.log("[AG-UI] Sending StartSpeaking...");
            wsRef.current.send(JSON.stringify({ type: "StartSpeaking" }));
            setAgentStatus("listening");
        } else {
            console.warn("[AG-UI] Cannot send StartSpeaking, socket not open. Reconnecting...");
            connect();
        }
    }, [connect]);

    // ── Send audio chunk ───────────────────────────────────
    const sendAudioChunk = useCallback((base64Audio: string) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(
                JSON.stringify({
                    type: "AudioChunk",
                    data: { base64Audio },
                }),
            );
        }
    }, []);

    return {
        agentStatus,
        messages,
        screenshotBase64,
        connect,
        disconnect,
        sendAudioChunk,
        sendStartSpeaking,
        setAgentStatus,
    };
}