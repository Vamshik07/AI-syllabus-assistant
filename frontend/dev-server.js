const { spawn } = require("node:child_process");
const { existsSync } = require("node:fs");
const path = require("node:path");

const frontendDir = __dirname;
const backendDir = path.resolve(frontendDir, "..", "backend");
const venvPython = path.join(backendDir, "venv", "Scripts", "python.exe");
const nextScript = path.join(frontendDir, "node_modules", "next", "dist", "bin", "next");
const python = existsSync(venvPython) ? venvPython : "python";

const backend = spawn(
  python,
  ["-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
  {
    cwd: backendDir,
    stdio: "inherit",
    windowsHide: false,
  },
);

backend.on("error", (error) => {
  console.error(`Unable to start the FastAPI backend: ${error.message}`);
  process.exitCode = 1;
});

const frontend = spawn(
  process.execPath,
  [nextScript, "dev", "-p", "3001"],
  {
    cwd: frontendDir,
    stdio: "inherit",
    windowsHide: false,
  },
);

frontend.on("error", (error) => {
  console.error(`Unable to start the Next.js frontend: ${error.message}`);
  backend.kill();
  process.exitCode = 1;
});

const shutdown = () => {
  backend.kill();
  frontend.kill();
};

process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);

frontend.on("exit", (code) => {
  backend.kill();
  process.exit(code ?? 0);
});
