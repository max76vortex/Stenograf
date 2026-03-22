/**
 * Обёртка для obsidian-mcp-server: подгружает env из .cursor/obsidian-audio-brain.env
 * и запускает сервер с этими переменными (обход проблемы, когда Cursor не передаёт env в процесс).
 */
const { spawn } = require("child_process");
const path = require("path");
const fs = require("fs");

const dir = __dirname;
const envPath = path.join(dir, "obsidian-audio-brain.env");

if (!fs.existsSync(envPath)) {
  console.error("Missing .cursor/obsidian-audio-brain.env. Create it with OBSIDIAN_BASE_URL and OBSIDIAN_API_KEY.");
  process.exit(1);
}

const envContent = fs.readFileSync(envPath, "utf8");
const env = { ...process.env };
for (const line of envContent.split(/\r?\n/)) {
  const m = line.match(/^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$/);
  if (m) env[m[1].trim()] = m[2].trim().replace(/^["']|["']$/g, "");
}

// Запуск сервера напрямую через node (без .cmd), чтобы env гарантированно попал в процесс
const serverDir = path.join(process.env.APPDATA || "", "npm", "node_modules", "obsidian-mcp-server");
const serverMain = path.join(serverDir, "dist", "index.js");

if (!fs.existsSync(serverMain)) {
  console.error("obsidian-mcp-server not found at", serverMain);
  process.exit(1);
}

const child = spawn(process.execPath, [serverMain], {
  env,
  stdio: "inherit",
  cwd: serverDir,
});

child.on("error", (err) => {
  console.error("Failed to start obsidian-mcp-server:", err.message);
  process.exit(1);
});

child.on("exit", (code) => {
  process.exit(code ?? 0);
});
