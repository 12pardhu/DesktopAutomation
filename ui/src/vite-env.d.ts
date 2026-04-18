/// <reference types="vite/client" />

interface Window {
  assistantDesktop?: {
    openExternal: (url: string) => Promise<void>;
    transcribeLocalAudio: (
      audioBuffer: ArrayBuffer,
      language?: string,
    ) => Promise<{ transcript: string; detected_language: string; error?: string | null }>;
  };
}
