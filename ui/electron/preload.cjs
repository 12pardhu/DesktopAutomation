const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("assistantDesktop", {
  openExternal: (url) => ipcRenderer.invoke("open-external", url),
});
