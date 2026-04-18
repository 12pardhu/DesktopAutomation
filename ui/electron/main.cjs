const { app, BrowserWindow, ipcMain, shell } = require("electron");
const { spawn } = require("node:child_process");
const fs = require("node:fs");
const http = require("node:http");
const os = require("node:os");
const path = require("node:path");

const isDev = process.env.NODE_ENV !== "production";
let backendProcess = null;

function backendUrl() {
  return "http://127.0.0.1:8765/health";
}

function backendPythonPath() {
  const root = path.join(__dirname, "..", "..");
  if (process.platform === "win32") {
    return path.join(root, "backend", ".venv", "Scripts", "python.exe");
  }
  return path.join(root, "backend", ".venv", "bin", "python");
}

function backendCwd() {
  return path.join(__dirname, "..", "..", "backend");
}

function projectRoot() {
  return path.join(__dirname, "..", "..");
}

function pingBackend() {
  return new Promise((resolve) => {
    const request = http.get(backendUrl(), (response) => {
      response.resume();
      resolve(response.statusCode && response.statusCode < 500);
    });
    request.on("error", () => resolve(false));
    request.setTimeout(800, () => {
      request.destroy();
      resolve(false);
    });
  });
}

async function ensureBackend() {
  if (await pingBackend()) {
    return;
  }
  const pythonPath = backendPythonPath();
  backendProcess = spawn(pythonPath, ["-m", "app.main"], {
    cwd: backendCwd(),
    stdio: "ignore",
    detached: false,
  });
}

function createWindow() {
  const window = new BrowserWindow({
    width: 1280,
    height: 820,
    minWidth: 980,
    minHeight: 680,
    title: "Offline AI Assistant",
    backgroundColor: "#0b1220",
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  if (isDev) {
    window.loadURL("http://127.0.0.1:5173");
  } else {
    window.loadFile(path.join(__dirname, "../dist/index.html"));
  }
}

app.whenReady().then(async () => {
  await ensureBackend();
  createWindow();
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});

ipcMain.handle("open-external", async (_event, url) => {
  if (typeof url === "string" && url.startsWith("http://127.0.0.1")) {
    await shell.openExternal(url);
  }
});

ipcMain.handle("transcribe-local-audio", async (_event, audioBuffer, language = "auto") => {
  const tempAudioPath = path.join(os.tmpdir(), `offline-assistant-${Date.now()}.wav`);
  const swiftScriptPath = path.join(projectRoot(), "backend", "app", "voice_module", "macos_stt.swift");

  fs.writeFileSync(tempAudioPath, Buffer.from(audioBuffer));

  try {
    const result = spawnSyncSafe("xcrun", ["swift", swiftScriptPath, tempAudioPath, mapLocales(language)], {
      cwd: projectRoot(),
      env: {
        ...process.env,
        SWIFT_MODULECACHE_PATH: "/tmp/swift-module-cache",
        CLANG_MODULE_CACHE_PATH: "/tmp/clang-module-cache",
      },
    });
    if (result.status !== 0) {
      throw new Error(result.stdout?.error || result.stderr || "Local voice transcription failed.");
    }
    return result.stdout;
  } finally {
    try {
      fs.unlinkSync(tempAudioPath);
    } catch {
      // Ignore cleanup errors for temp audio.
    }
  }
});

function spawnSyncSafe(command, args, options) {
  const { spawnSync } = require("node:child_process");
  const result = spawnSync(command, args, { ...options, encoding: "utf8" });
  let stdout = {};
  try {
    stdout = JSON.parse((result.stdout || "").trim() || "{}");
  } catch {
    stdout = {};
  }
  return { ...result, stdout };
}

function mapLocales(language) {
  if (language === "hi") return "hi-IN,en-US";
  if (language === "te") return "te-IN,en-US";
  return "en-US,hi-IN,te-IN";
}

app.on("before-quit", () => {
  if (backendProcess) {
    backendProcess.kill();
    backendProcess = null;
  }
});
