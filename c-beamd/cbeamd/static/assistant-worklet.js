// the recorder's audio worklet: hands the microphone's samples (mono float32,
// at the audio context's rate) to the page in 100 ms blocks, which drive the
// level meter and are joined into the wav for whisper. loaded by assistant.js.
class AssistantRecorder extends AudioWorkletProcessor {
  constructor() {
    super();
    this.chunks = [];
    this.collected = 0;
    this.block = Math.round(sampleRate / 10);
  }

  process(inputs) {
    const channel = inputs[0] && inputs[0][0];
    if (channel) {
      this.chunks.push(new Float32Array(channel));
      this.collected += channel.length;
      if (this.collected >= this.block) {
        const block = new Float32Array(this.collected);
        let offset = 0;
        for (const chunk of this.chunks) {
          block.set(chunk, offset);
          offset += chunk.length;
        }
        this.port.postMessage(block, [block.buffer]);
        this.chunks = [];
        this.collected = 0;
      }
    }
    return true;
  }
}

registerProcessor('assistant-recorder', AssistantRecorder);
