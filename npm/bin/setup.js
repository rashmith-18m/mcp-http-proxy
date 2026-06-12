#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");

/**
 * Determines the platform-specific config directory for rocket_mcp_proxy.
 *   Windows: %APPDATA%\rocket_mcp_proxy
 *   macOS:   ~/Library/Application Support/rocket_mcp_proxy
 *   Linux:   ~/.config/rocket_mcp_proxy
 */
function getConfigDir() {
  if (process.platform === "win32") {
    const appdata = process.env.APPDATA || path.join(require("os").homedir(), "AppData", "Roaming");
    return path.join(appdata, "rocket_mcp_proxy");
  }
  if (process.platform === "darwin") {
    return path.join(require("os").homedir(), "Library", "Application Support", "rocket_mcp_proxy");
  }
  const xdgConfig = process.env.XDG_CONFIG_HOME || path.join(require("os").homedir(), ".config");
  return path.join(xdgConfig, "rocket_mcp_proxy");
}

/**
 * Copy a file from src to dest only if dest does not already exist.
 * Returns true if copied, false if skipped.
 */
function copyIfMissing(src, dest, label) {
  if (fs.existsSync(dest)) {
    console.log(`  [skip] ${label} already exists: ${dest}`);
    return false;
  }
  fs.copyFileSync(src, dest);
  console.log(`  [done] ${label} -> ${dest}`);
  return true;
}

function setup() {
  const configDir = getConfigDir();
  const resourcesDir = path.join(__dirname, "..", "resources");

  console.log(`\nRocket MCP Proxy — setup`);
  console.log(`Config directory: ${configDir}\n`);

  // 1. Create the config directory
  if (!fs.existsSync(configDir)) {
    fs.mkdirSync(configDir, { recursive: true });
    console.log(`  [done] Created directory: ${configDir}`);
  }

  // 2. Copy config.json (never overwrite existing user config)
  const configSrc = path.join(resourcesDir, "config.json");
  const configDest = path.join(configDir, "config.json");
  if (fs.existsSync(configSrc)) {
    copyIfMissing(configSrc, configDest, "config.json");
  }

  // 3. Copy any other resource files (IntelliJ plugin zips, etc.)
  //    Everything in resources/ except config.json gets copied
  if (fs.existsSync(resourcesDir)) {
    const files = fs.readdirSync(resourcesDir);
    for (const file of files) {
      if (file === "config.json") continue;
      const src = path.join(resourcesDir, file);
      const dest = path.join(configDir, file);
      if (fs.statSync(src).isFile()) {
        copyIfMissing(src, dest, file);
      }
    }
  }

  console.log(`\nSetup complete.\n`);
  console.log(`Next steps:`);
  console.log(`  1. Edit ${configDest}`);
  console.log(`     Point each server's "url" to your MCP server endpoint.`);
  console.log(`  2. Open your IDE and start the MCP servers.\n`);
}

setup();
