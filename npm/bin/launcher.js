#!/usr/bin/env node
"use strict";

const { spawn, execFileSync } = require("child_process");
const path = require("path");
const fs = require("fs");
const os = require("os");
const https = require("https");

// --- Configuration ---
const ARTIFACTORY_BASE = "https://wal-artifactory.rocketsoftware.com/artifactory";
const ARTIFACTORY_REPO = "cypf-npm-dev-wal";
const ARTIFACTORY_AUTH = "Basic Ymx3bW9iZjpBS0NwOG1Zb1VmS0RUUlNoTWFYQnhUamg4TDQ1Zk5zelRueDJyVGlucGJoeWlmZFl0SnQ4Nkp6d2FwZDVERE5oWVp0eGJLdk42";
const PACKAGE_NAME = "@aicoe/rocket-mcp-proxy";
const REGISTRY_URL = `${ARTIFACTORY_BASE}/api/npm/${ARTIFACTORY_REPO}`;

const PLATFORM_BINARIES = {
  "win32-x64":    "rocket_mcp_proxy-windows-latest.exe",
  "win32-arm64":  "rocket_mcp_proxy-windows-latest.exe",
  "darwin-x64":   "rocket_mcp_proxy-macos-x64",
  "darwin-arm64": "rocket_mcp_proxy-macos-arm64",
  "linux-x64":    "rocket_mcp_proxy-ubuntu-latest",
};

// --- Helpers ---

function getConfigDir() {
  if (process.platform === "win32") {
    const appdata = process.env.APPDATA || path.join(os.homedir(), "AppData", "Roaming");
    return path.join(appdata, "rocket_mcp_proxy");
  }
  if (process.platform === "darwin") {
    return path.join(os.homedir(), "Library", "Application Support", "rocket_mcp_proxy");
  }
  const xdgConfig = process.env.XDG_CONFIG_HOME || path.join(os.homedir(), ".config");
  return path.join(xdgConfig, "rocket_mcp_proxy");
}

function getBinaryName() {
  const key = `${process.platform}-${process.arch}`;
  const name = PLATFORM_BINARIES[key];
  if (!name) {
    console.error(`ERROR: Unsupported platform/arch '${key}'. Supported: ${Object.keys(PLATFORM_BINARIES).join(", ")}`);
    process.exit(1);
  }
  return name;
}

function getBinaryPath(version) {
  const configDir = getConfigDir();
  return path.join(configDir, "bin", version, getBinaryName());
}

function getDownloadUrl(version) {
  const binaryName = getBinaryName();
  return `${ARTIFACTORY_BASE}/${ARTIFACTORY_REPO}/rocket-mcp-proxy/${version}/${binaryName}`;
}

function getLocalVersion() {
  const versionFile = path.join(getConfigDir(), "bin", ".current_version");
  try {
    return fs.readFileSync(versionFile, "utf-8").trim();
  } catch {
    return null;
  }
}

function setLocalVersion(version) {
  const versionFile = path.join(getConfigDir(), "bin", ".current_version");
  const dir = path.dirname(versionFile);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
  fs.writeFileSync(versionFile, version, "utf-8");
}

function fetchLatestVersion() {
  return new Promise((resolve, reject) => {
    const url = `${REGISTRY_URL}/${encodeURIComponent(PACKAGE_NAME).replace("%40", "@")}`;
    https.get(url, { headers: { Authorization: ARTIFACTORY_AUTH } }, (response) => {
      if (response.statusCode !== 200) {
        reject(new Error(`Registry returned HTTP ${response.statusCode}`));
        return;
      }
      let data = "";
      response.on("data", (chunk) => { data += chunk; });
      response.on("end", () => {
        try {
          const pkg = JSON.parse(data);
          const latest = pkg["dist-tags"] && pkg["dist-tags"]["latest"];
          if (latest) {
            resolve(latest);
          } else {
            reject(new Error("No 'latest' dist-tag found"));
          }
        } catch (err) {
          reject(err);
        }
      });
    }).on("error", reject);
  });
}

function downloadFile(url, destPath) {
  return new Promise((resolve, reject) => {
    const dir = path.dirname(destPath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }

    const tmpPath = destPath + ".tmp";
    let settled = false;
    const fail = (err) => {
      if (settled) return;
      settled = true;
      if (fs.existsSync(tmpPath)) fs.unlinkSync(tmpPath);
      reject(err);
    };

    const request = (reqUrl, redirects) => {
      if (redirects > 5) {
        fail(new Error(`Too many redirects downloading from ${url}`));
        return;
      }
      const mod = reqUrl.startsWith("https") ? https : require("http");
      mod.get(reqUrl, { headers: { Authorization: ARTIFACTORY_AUTH } }, (response) => {
        if (response.statusCode === 301 || response.statusCode === 302) {
          response.resume(); // drain the redirect body
          request(response.headers.location, redirects + 1);
          return;
        }
        if (response.statusCode !== 200) {
          fail(new Error(`Download failed: HTTP ${response.statusCode} from ${reqUrl}`));
          return;
        }

        const totalBytes = parseInt(response.headers["content-length"] || "0", 10);
        let downloaded = 0;

        const file = fs.createWriteStream(tmpPath);
        file.on("error", (err) => fail(err));

        response.on("data", (chunk) => {
          downloaded += chunk.length;
          if (totalBytes > 0) {
            const pct = Math.round((downloaded / totalBytes) * 100);
            process.stderr.write(`\rDownloading rocket_mcp_proxy... ${pct}%`);
          }
        });

        response.pipe(file);
        file.on("finish", () => {
          file.close(() => {
            if (settled) return;
            if (downloaded === 0) {
              fail(new Error(`Download returned empty body from ${reqUrl}`));
              return;
            }
            process.stderr.write("\n");
            try {
              fs.renameSync(tmpPath, destPath);
              if (process.platform !== "win32") {
                fs.chmodSync(destPath, 0o755);
              }
              settled = true;
              resolve();
            } catch (err) {
              fail(err);
            }
          });
        });
      }).on("error", (err) => fail(err));
    };

    request(url, 0);
  });
}

// --- Setup ---

function ensureSetup() {
  const configDir = getConfigDir();
  const configPath = path.join(configDir, "config.json");
  if (!fs.existsSync(configPath)) {
    try {
      execFileSync(process.execPath, [path.join(__dirname, "setup.js")], {
        stdio: "inherit",
      });
    } catch {
      // Continue — proxy will report missing config
    }
  }
}

// --- Main ---

async function main() {
  ensureSetup();

  // Determine which version to use
  let version = getLocalVersion();

  // Check registry for latest version (with timeout — don't block forever)
  try {
    const latestVersion = await Promise.race([
      fetchLatestVersion(),
      new Promise((_, reject) => setTimeout(() => reject(new Error("timeout")), 5000)),
    ]);

    if (latestVersion !== version) {
      console.error(`New version available: ${latestVersion} (current: ${version || "none"})`);
      version = latestVersion;
    }
  } catch {
    // Network error or timeout — use cached version if available
    if (!version) {
      console.error("ERROR: No cached binary and unable to reach Artifactory to check latest version.");
      process.exit(1);
    }
  }

  const binaryPath = getBinaryPath(version);

  // Download binary if not present for this version
  if (!fs.existsSync(binaryPath)) {
    const url = getDownloadUrl(version);
    console.error(`Downloading rocket_mcp_proxy v${version}...`);
    console.error(`URL: ${url}`);
    try {
      await downloadFile(url, binaryPath);
      setLocalVersion(version);
      console.error(`Downloaded to: ${binaryPath}`);
      // On Windows, wait for antivirus to finish scanning the new binary
      if (process.platform === "win32") {
        await new Promise((resolve) => setTimeout(resolve, 3000));
      }
    } catch (err) {
      console.error(`ERROR: Failed to download binary: ${err.message}`);
      // Fall back to any previously cached version
      const fallback = getLocalVersion();
      if (fallback && fs.existsSync(getBinaryPath(fallback))) {
        console.error(`Falling back to cached version: ${fallback}`);
        version = fallback;
      } else {
        process.exit(1);
      }
    }
  } else {
    // Binary exists — make sure version file is current
    setLocalVersion(version);
  }

  // Run the binary (with retry for Windows EBUSY after fresh download)
  const finalBinaryPath = getBinaryPath(version);

  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  let lastError;
  for (let attempt = 0; attempt < 10; attempt++) {
    try {
      const child = spawn(finalBinaryPath, process.argv.slice(2), {
        stdio: "inherit",
        windowsHide: true,
      });

      // If spawn succeeded, wait for exit
      child.on("error", (err) => {
        console.error(`ERROR: Failed to start proxy: ${err.message}`);
        process.exit(1);
      });

      child.on("exit", (code, signal) => {
        if (signal) {
          process.kill(process.pid, signal);
        } else {
          process.exit(code ?? 1);
        }
      });

      return; // spawn succeeded, we're done
    } catch (err) {
      lastError = err;
      if (err.code === "EBUSY") {
        console.error(`Binary is busy (antivirus scan?), retrying in 2s... (attempt ${attempt + 1}/10)`);
        await sleep(2000);
      } else {
        break;
      }
    }
  }

  console.error(`ERROR: Failed to start proxy: ${lastError.message}`);
  process.exit(1);
}

main();
