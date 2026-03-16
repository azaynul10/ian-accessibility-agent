"use client";

import { useRef, useCallback } from "react";

// ─── Utility ─────────────────────────────────────────────
/** Int16 PCM ArrayBuffer → Base64 string (browser-safe). */
function arrayBufferToBase64(buffer: ArrayBuffer): string {
    const bytes = new Uint8Array(buffer);
    let binary = "";
    for (let i = 0; i < bytes.length; i++) {
        binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
}

// ─── Hook ────────────────────────────────────────────────
/**
 * Captures raw 16-bit PCM audio at 16 kHz using the modern
 * AudioWorklet API and streams Base64-encoded chunks via a
 * callback.
 *
 * We DO NOT use ScriptProcessorNode because it runs on the 
 * main thread and drops audio frames, causing pure silence.
 */
export function useAudioCapture(
    /** Called with each Base64-encoded PCM chunk, ready for the WS. */
    onChunk: (base64Audio: string) => void,
) {
    const ctxRef = useRef<AudioContext | null>(null);
    const streamRef = useRef<MediaStream | null>(null);
    const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
    const workletRef = useRef<AudioWorkletNode | null>(null);

    const start = useCallback(async () => {
        if (streamRef.current) return; // Prevent double initialization

        // 1. Request mic access (echo cancellation included)
        const stream = await navigator.mediaDevices.getUserMedia({
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true,  // <--- This balances low/high volumes instantly!
                sampleRate: 16000,      // Forces 16kHz at the hardware level
                channelCount: 1         // Forces Mono audio
            },
        });
        streamRef.current = stream;

        // 2. Force AudioContext to 16 kHz
        const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
        const ctx = new AudioContextClass({ sampleRate: 16000 });
        ctxRef.current = ctx;

        // 3. Load the worklet module (WITH CACHE BUSTER!)
        await ctx.audioWorklet.addModule(`/audio-processor.js?t=${Date.now()}`);

        // 4. Create source from mic stream
        const source = ctx.createMediaStreamSource(stream);
        sourceRef.current = source;

        // 5. Create AudioWorkletNode
        const workletNode = new AudioWorkletNode(ctx, "pcm-capture-processor");
        workletRef.current = workletNode;

        // 6. Listen for PCM buffers from the worklet thread
        workletNode.port.onmessage = (e: MessageEvent<ArrayBuffer>) => {
            let b64 = arrayBufferToBase64(e.data);

            // Strip any accidental Data URI header
            b64 = b64.replace(/^data:audio\/\w+;base64,/, "");

            // Never send empty chunks
            if (!b64) return;

            onChunk(b64);
        };

        // 7. Connect: mic → worklet
        source.connect(workletNode);
        workletNode.connect(ctx.destination);
    }, [onChunk]);

    const stop = useCallback(() => {
        // Disconnect worklet
        workletRef.current?.disconnect();
        workletRef.current = null;

        // Disconnect source
        sourceRef.current?.disconnect();
        sourceRef.current = null;

        // Close audio context
        if (ctxRef.current && ctxRef.current.state !== "closed") {
            ctxRef.current.close().catch(console.error);
        }
        ctxRef.current = null;

        // Stop mic tracks
        streamRef.current?.getTracks().forEach((t) => t.stop());
        streamRef.current = null;
    }, []);

    return { start, stop };
}
