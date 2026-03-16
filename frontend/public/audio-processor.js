class PCMProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
        this.bufferSize = 2048; // Exactly 4096 bytes of Int16 data
        this.buffer = new Float32Array(this.bufferSize);
        this.bytesWritten = 0;
    }

    process(inputs, outputs, parameters) {
        const input = inputs[0];
        if (!input || input.length === 0) return true;

        const channel = input[0];

        for (let i = 0; i < channel.length; i++) {
            this.buffer[this.bytesWritten++] = channel[i];

            // Once the buffer is full, convert to Int16 and send it!
            if (this.bytesWritten >= this.bufferSize) {
                const int16Buffer = new Int16Array(this.bufferSize);
                for (let j = 0; j < this.bufferSize; j++) {
                    let s = Math.max(-1, Math.min(1, this.buffer[j]));
                    int16Buffer[j] = s < 0 ? s * 0x8000 : s * 0x7FFF;
                }

                this.port.postMessage(int16Buffer.buffer);
                this.bytesWritten = 0; // Reset for the next chunk
            }
        }
        return true;
    }
}
registerProcessor("pcm-capture-processor", PCMProcessor);