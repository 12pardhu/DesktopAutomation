import { FormEvent, useRef, useState } from "react";
import { Mic, Send, Square, Volume2 } from "lucide-react";
import type { ChatMessage } from "../types/app";

type SpeechRecognitionConstructor = new () => {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onresult: ((event: SpeechRecognitionEventLike) => void) | null;
  onerror: ((event: { error?: string }) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
};

type SpeechRecognitionEventLike = {
  results: ArrayLike<ArrayLike<{ transcript: string }>>;
};

declare global {
  interface Window {
    SpeechRecognition?: SpeechRecognitionConstructor;
    webkitSpeechRecognition?: SpeechRecognitionConstructor;
  }
}

export function ChatPanel({
  messages,
  isBusy,
  speakReplies,
  latestTranscript,
  voiceStatus,
  onVoiceStatusChange,
  onVoicePreview,
  onSend,
  onVoice,
  onSpeakLast,
}: {
  messages: ChatMessage[];
  isBusy: boolean;
  speakReplies: boolean;
  latestTranscript: string;
  voiceStatus: string;
  onVoiceStatusChange: (state: string) => void;
  onVoicePreview: (transcript: string) => void;
  onSend: (text: string) => Promise<void>;
  onVoice: (blob: Blob, transcriptHint?: string) => Promise<void>;
  onSpeakLast: () => Promise<void>;
}) {
  const [text, setText] = useState("");
  const [recording, setRecording] = useState(false);
  const audioContextRef = useRef<AudioContext | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const chunksRef = useRef<Float32Array[]>([]);
  const recognitionRef = useRef<InstanceType<SpeechRecognitionConstructor> | null>(null);
  const browserTranscriptRef = useRef("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    const value = text.trim();
    if (!value || isBusy) return;
    setText("");
    await onSend(value);
  }

  async function toggleRecording() {
    if (recording) {
      await stopRecording();
      return;
    }
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: { noiseSuppression: true, echoCancellation: true, autoGainControl: true },
    });
    onVoiceStatusChange("Listening...");
    const audioContext = new AudioContext({ sampleRate: 16000 });
    const source = audioContext.createMediaStreamSource(stream);
    const processor = audioContext.createScriptProcessor(4096, 1, 1);
    chunksRef.current = [];
    processor.onaudioprocess = (event) => {
      const channel = event.inputBuffer.getChannelData(0);
      chunksRef.current.push(new Float32Array(channel));
    };
    source.connect(processor);
    processor.connect(audioContext.destination);
    mediaStreamRef.current = stream;
    audioContextRef.current = audioContext;
    sourceRef.current = source;
    processorRef.current = processor;
    browserTranscriptRef.current = "";
    startBrowserRecognition();
    setRecording(true);
  }

  async function stopRecording() {
    stopBrowserRecognition()
    processorRef.current?.disconnect();
    sourceRef.current?.disconnect();
    mediaStreamRef.current?.getTracks().forEach((track) => track.stop());
    await audioContextRef.current?.close();
    onVoiceStatusChange("Transcribing your voice command...");
    const wavBlob = encodeWav(chunksRef.current, 16000);
    chunksRef.current = [];
    mediaStreamRef.current = null;
    audioContextRef.current = null;
    sourceRef.current = null;
    processorRef.current = null;
    setRecording(false);
    if (wavBlob.size <= 44) {
      onVoiceStatusChange("No voice audio captured. Please try again.");
      return;
    }
    await onVoice(wavBlob, browserTranscriptRef.current.trim() || undefined);
  }

  function startBrowserRecognition() {
    const Recognition = window.SpeechRecognition ?? window.webkitSpeechRecognition;
    if (!Recognition) {
      browserTranscriptRef.current = "";
      return;
    }
    browserTranscriptRef.current = "";
    const recognition = new Recognition();
    recognitionRef.current = recognition;
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = "en-US";
    recognition.onresult = (event) => {
      let transcript = "";
      for (let index = 0; index < event.results.length; index += 1) {
        transcript += event.results[index][0]?.transcript ?? "";
      }
      transcript = transcript.trim();
      if (transcript) {
        browserTranscriptRef.current = transcript;
        setText(transcript);
        onVoicePreview(transcript);
      }
    };
    recognition.onerror = () => {
      recognitionRef.current = null;
    };
    recognition.onend = () => {
      recognitionRef.current = null;
    };
    try {
      recognition.start();
    } catch {
      recognitionRef.current = null;
    }
  }

  function stopBrowserRecognition() {
    if (!recognitionRef.current) {
      return;
    }
    try {
      recognitionRef.current.stop();
    } catch {
      recognitionRef.current = null;
    }
  }

  return (
    <section className="flex min-h-[620px] min-w-0 flex-col rounded-[28px] border border-line/80 bg-panel/90 shadow-[0_24px_80px_rgba(0,0,0,0.28)]">
      <div className="border-b border-line/80 px-5 py-4">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="min-w-0 flex-1">
            <h2 className="font-semibold text-mist">Command center</h2>
            <p className="text-sm text-slate-400">Type or speak a task and the offline queue will execute it step by step.</p>
          </div>
          <button
            type="button"
            onClick={onSpeakLast}
            className="inline-flex w-full items-center justify-center gap-2 rounded-full border border-accent/30 bg-panelSoft px-4 py-3 text-sm font-medium text-mist hover:border-accent sm:w-auto"
          >
            <Volume2 className="h-4 w-4" />
            {speakReplies ? "Replay reply" : "Speak test"}
          </button>
        </div>
      </div>
      <div className="flex-1 space-y-3 overflow-y-auto px-5 py-5">
        {messages.map((message, index) => (
          <div
            key={`${message.timestamp}-${index}`}
            className={`max-w-[85%] rounded-[22px] px-4 py-3 text-sm leading-6 ${
              message.role === "user"
                ? "ml-auto bg-accent text-ink shadow-lg shadow-emerald-950/20"
                : "border border-line/80 bg-panelSoft text-slate-200"
            }`}
          >
            {message.content}
          </div>
        ))}
      </div>
      <form onSubmit={submit} className="grid gap-3 border-t border-line/80 px-5 py-4">
        <div className="rounded-[24px] border border-line/80 bg-panelSoft/70 px-4 py-3">
          <p className="text-xs uppercase tracking-[0.18em] text-accent">Voice bar</p>
          <p className="mt-2 text-sm text-slate-300">
            {latestTranscript || voiceStatus || "Your latest transcribed voice command will appear here."}
          </p>
        </div>
        <textarea
          value={text}
          onChange={(event) => setText(event.target.value)}
          placeholder={
            text || latestTranscript
              ? ""
              : 'Try "Open Chrome then open YouTube", "Search file report.pdf and open it", or "Downloads folder open invoice.xlsx"'
          }
          rows={3}
          className="min-h-[140px] w-full rounded-[24px] border border-line bg-ink/70 px-4 py-3 text-base text-mist outline-none placeholder:text-slate-500 focus:border-accent sm:min-h-[120px] sm:text-sm"
        />
        <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap">
          <button
            type="button"
            onClick={toggleRecording}
            className="inline-flex w-full items-center justify-center gap-2 rounded-full border border-accent/30 bg-panelSoft px-4 py-3 text-sm font-semibold text-mist hover:border-accent sm:w-auto"
          >
            {recording ? <Square className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
            {recording ? "Stop recording" : "Voice input"}
          </button>
          <button
            type="submit"
            disabled={isBusy}
            className="inline-flex w-full items-center justify-center gap-2 rounded-full bg-honey px-4 py-3 text-sm font-semibold text-ink shadow-lg shadow-black/20 disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto"
          >
            <Send className="h-4 w-4" />
            {isBusy ? "Planning..." : "Run command"}
          </button>
        </div>
      </form>
    </section>
  );
}

function encodeWav(chunks: Float32Array[], sampleRate: number) {
  const length = chunks.reduce((total, chunk) => total + chunk.length, 0);
  const samples = new Float32Array(length);
  let offset = 0;
  for (const chunk of chunks) {
    samples.set(chunk, offset);
    offset += chunk.length;
  }

  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);
  writeAscii(view, 0, "RIFF");
  view.setUint32(4, 36 + samples.length * 2, true);
  writeAscii(view, 8, "WAVE");
  writeAscii(view, 12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeAscii(view, 36, "data");
  view.setUint32(40, samples.length * 2, true);

  let index = 44;
  for (const sample of samples) {
    const value = Math.max(-1, Math.min(1, sample));
    view.setInt16(index, value < 0 ? value * 0x8000 : value * 0x7fff, true);
    index += 2;
  }
  return new Blob([buffer], { type: "audio/wav" });
}

function writeAscii(view: DataView, offset: number, value: string) {
  for (let index = 0; index < value.length; index += 1) {
    view.setUint8(offset + index, value.charCodeAt(index));
  }
}
