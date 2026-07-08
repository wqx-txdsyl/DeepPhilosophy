const { app, BrowserWindow } = require('electron');
const path = require('path');
const http = require('http');
const fs = require('fs');

let mainWindow;
let server;

function startServer(dir) {
  const mime = { '.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json',
    '.png':'image/png','.jpg':'image/jpeg','.webp':'image/webp','.svg':'image/svg+xml','.ico':'image/x-icon' };
  server = http.createServer((req, res) => {
    let filePath = path.join(dir, req.url.split('?')[0]);
    if (filePath.endsWith('/')) filePath = path.join(filePath, 'index.html');
    const ext = path.extname(filePath);
    fs.readFile(filePath, (err, data) => {
      if (err) { res.writeHead(404); res.end('Not found'); return; }
      res.writeHead(200, { 'Content-Type': mime[ext] || 'application/octet-stream' });
      res.end(data);
    });
  });
  server.listen(0, '127.0.0.1', () => {
    const port = server.address().port;
    mainWindow.loadURL(`http://127.0.0.1:${port}`);
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({ width: 1280, height: 800,
    webPreferences: { nodeIntegration: false, contextIsolation: true } });
  startServer(path.join(__dirname, '..'));
  mainWindow.on('closed', () => { mainWindow = null; if (server) server.close(); });
}

app.whenReady().then(createWindow);
app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit(); });
