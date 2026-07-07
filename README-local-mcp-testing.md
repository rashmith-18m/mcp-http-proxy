# Testing Local MCP Servers with GitHub Copilot

Connect your IDE (VS Code, IntelliJ, or Eclipse) to your MCP servers.
---

## Table of Contents

- [1. Prerequisites](#1-prerequisites)
- [2. VS Code Setup](#2-vs-code-setup)
- [3. IntelliJ IDEA Setup](#3-intellij-idea-setup)
- [4. Eclipse Setup](#4-eclipse-setup)
- [5. Configuring Your MCP Servers (config.json)](#5-configuring-your-mcp-servers-configjson)
- [6. TLS / Certificate Setup](#6-tls--certificate-setup)
- [7. OAuth / SSO Setup](#7-oauth--sso-setup)
- [Troubleshooting](#troubleshooting)

---

## 1. Prerequisites

Before you begin, make sure you have:

> **Important:** Your VPN must be connected any time you start an MCP server. The first run downloads required components; subsequent runs use the cached copy.

---

## 2. VS Code Setup

### Step 1: Find the MCP Servers

1. Open **VS Code**.
2. Open the **Copilot Chat** panel (click the chat icon in the sidebar, or press `Ctrl+Alt+I`).
3. At the bottom of the chat input, click the **Configure Tools** icon (🔧).
4. Click the **MCP** icon (top-right corner) of the panel that opens up, then select the option **"Browse MCP Servers"** in the options listed in the dropdown.

You will see a list of available servers named `mcp-server-1` through `mcp-server-6`.

### Step 2: Install a Server

1. Click on one of the `mcp-server-*` entries (e.g., `mcp-server-1`).
2. Click **Install**.

### Step 3: Configure the Server

After installing, you need to point the server to your MCP endpoint using the `config.json` file.

1. Open your `config.json` file. The location depends on your OS:

   | OS | Path |
   |----|------|
   | **Windows** | `%APPDATA%\rocket_mcp_proxy\config.json` |
   | **macOS** | `~/Library/Application Support/rocket_mcp_proxy/config.json` |
   | **Linux** | `~/.config/rocket_mcp_proxy/config.json` |

2. Edit the file to add your MCP server URL (see [Section 5](#5-configuring-your-mcp-servers-configjson) for full details).


### Step 4: Start and Stop the Server

**To start:**
  1. Open the **Copilot Chat** panel (click the chat icon in the sidebar, or press `Ctrl+Alt+I`).
  2. At the bottom of the chat input, click the **Configure Tools** icon (🔧).
  3. Click the **MCP** icon (top-right corner) of the panel that opens up, then select the option **"Browse MCP Servers"** in the options listed in the dropdown.
  4. You will see a list of available servers named `mcp-server-1` through `mcp-server-6`.
  5. Select your server → click on the gear icon → **Start Server**.
  6. Once started, the Console Output (click on the gear icon → **Show Output**) will show the logs and finally, the number of tools available from your server.
  7. To see the tool names, click the **Configure Tools** icon at the the bottom of the chat input, a panel pops up with a list of MCP server names and their corresponding tools.

**To stop:**
  1. Open the **Copilot Chat** panel (click the chat icon in the sidebar, or press `Ctrl+Alt+I`).
  2. At the bottom of the chat input, click the **Configure Tools** icon (🔧).
  3. Click the **MCP** icon (top-right corner) of the panel that opens up, then select the option **"Browse MCP Servers"** in the options listed in the dropdown.
  4. You will see a list of available servers named `mcp-server-1` through `mcp-server-6`.
  5. Select your server → click on the gear icon → click **Stop Server**.



---

## 3. IntelliJ IDEA Setup

> Requires **IntelliJ IDEA 2025.3.4** or later.

### Step 1: Install the GitHub Copilot Plugin (Nightly Build)

1. Open **IntelliJ IDEA**.
2. Go to **Settings** → **Plugins**.
3. Click the ⚙️ icon (gear) → **Install Plugin from Disk…**
4. Navigate to the following folder:
   - **Windows:** `%APPDATA%\rocket_mcp_proxy\`
   - **macOS:** `~/Library/Application Support/rocket_mcp_proxy/`
   - **Linux:** `~/.config/rocket_mcp_proxy/`
5. Select the **github-copilot-intellij-1.8.3-nightly.22094-251** (`.zip` file) and click **OK**.
6. Restart IntelliJ when prompted.

### Step 2: Install a Server

1. Click on the **Copilot icon** at the bottom right and select the option **"Open Chat"**.
2. Click the **Gear icon** on the top right of the Copilot Chat and then select the option **"MCP Registry"**.
3. You will see a list of available servers named `mcp-server-1` through `mcp-server-6`.
4. Click **Install** adjacent to the server you like to install.

### Step 3: Configure the Server

After installing, you need to point the server to your MCP endpoint using the `config.json` file.

1. Open your `config.json` file. The location depends on your OS:

   | OS | Path |
   |----|------|
   | **Windows** | `%APPDATA%\rocket_mcp_proxy\config.json` |
   | **macOS** | `~/Library/Application Support/rocket_mcp_proxy/config.json` |
   | **Linux** | `~/.config/rocket_mcp_proxy/config.json` |

2. Edit the file to add your MCP server URL (see [Section 5](#5-configuring-your-mcp-servers-configjson) for full details).

### Step 4: Start and Stop the Server

**To start:**
  1. Open the **Copilot Chat** panel (click the Copilot icon at the bottom right and select **"Open Chat"**).
  2. At the bottom of the chat input, click the **Configure Tools** icon (🔧).
  3. A panel pops up with a list of MCP server names.
  4. Select your server → click on **Start**.
  5. Once started, the Console Output (click on **More** → **Show Output**) will show the logs.
  6. After the server starts successfully, the tool names can be viewed below the server name.

**To stop:**
  1. Open the **Copilot Chat** panel (click the Copilot icon at the bottom right and select **"Open Chat"**).
  2. At the bottom of the chat input, click the **Configure Tools** icon (🔧).
  3. A panel pops up with a list of MCP server names.
  4. Select your server → click on **Stop**.

---

## 4. Eclipse Setup

### Step 1: Install the Copilot Plugin

1. Open **Eclipse**.
2. Go to **Help** → **Eclipse Marketplace…**
3. Search for and install **GitHub Copilot - Nightly 0.18.0**.
4. Click **Install** and follow the prompts.
5. Restart Eclipse when prompted.

### Step 2: Install a Server

1. Click on the **Copilot icon** at the bottom right and select the option **"Open Chat"**.
2. At the bottom of the chat input, click the **Configure Tools** icon (🔧).
3. In the popup that opens, click the **"Open MCP Registry"** button (center right of the popup).
4. You will see a list of available servers named `mcp-server-1` through `mcp-server-6`.
5. Click **Install** adjacent to the server you like to install.

### Step 3: Configure the Server

After installing, you need to point the server to your MCP endpoint using the `config.json` file.

1. Open your `config.json` file. The location depends on your OS:

   | OS | Path |
   |----|------|
   | **Windows** | `%APPDATA%\rocket_mcp_proxy\config.json` |
   | **macOS** | `~/Library/Application Support/rocket_mcp_proxy/config.json` |
   | **Linux** | `~/.config/rocket_mcp_proxy/config.json` |

2. Edit the file to add your MCP server URL (see [Section 5](#5-configuring-your-mcp-servers-configjson) for full details).

### Step 4: View the Tools

1. Open the **Copilot Chat** panel (click the Copilot icon at the bottom right and select **"Open Chat"**).
2. At the bottom of the chat input, click the **Configure Tools** icon (🔧).
3. A panel pops up with a list of MCP server names and its tool names will be listed once the server starts successfully.

---

## 5. Configuring Your MCP Servers (config.json)

The `config.json` file is the place to configure all the details of MCP servers. Open it in any text editor to edit.

**File location:**

| OS | Path |
|----|------|
| **Windows** | `%APPDATA%\rocket_mcp_proxy\config.json` |
| **macOS** | `~/Library/Application Support/rocket_mcp_proxy/config.json` |
| **Linux** | `~/.config/rocket_mcp_proxy/config.json` |

### Supported connection types

The config supports three connection types:

| Type | Use when |
|------|----------|
| `"streamable-http"` | Your MCP server uses Streamable HTTP (most common). `"http"` also works as an alias. |
| `"sse"` | Your MCP server uses Server-Sent Events |
| `"stdio"` | Your MCP server runs as a local command (e.g., a Python script or Node.js app) |

> **Note:** For `stdio` servers, outbound network connections are filtered by the same host allowlist used for HTTP/SSE servers. Only `localhost` and approved `*.rocketsoftware.com` / `*.verticacorp.com` endpoints are reachable.

### Example: Basic HTTP server (mcp-server-1)

```json
{
  "url": "http://localhost:8081/mcp",
  "type": "streamable-http"
}
```

### Example: HTTP server with custom headers (mcp-server-2)

```json
{
  "url": "http://localhost:8082/mcp",
  "type": "streamable-http",
  "headers": {
    "Authorization": "Bearer your-token-here",
    "X-Custom-Header": "custom-value"
  }
}
```

### Example: SSE server (mcp-server-3)

```json
{
  "url": "http://localhost:8083/sse",
  "type": "sse"
}
```

### Example: OAuth - automatic discovery (mcp-server-4)

```json
{
  "url": "https://your-server.rocketsoftware.com/mcp",
  "type": "streamable-http",
  "oauth": "oauth"
}
```

### Example: OAuth with explicit credentials (mcp-server-5)

```json
{
  "url": "https://your-server.rocketsoftware.com/mcp",
  "type": "streamable-http",
  "oauth": {
    "clientId": "your-client-id",
    "clientSecret": "your-client-secret",
    "scopes": "openid profile",
    "callbackPort": 8085
  }
}
```

### Example: OAuth with client ID only (mcp-server-6)

```json
{
  "url": "https://your-server.rocketsoftware.com/mcp",
  "type": "streamable-http",
  "oauth": {
    "clientId": "your-client-id"
  }
}
```

### Example: Local stdio server

```json
{
  "type": "stdio",
  "command": "python3",
  "args": ["my_mcp_server.py", "--port", "3000"],
  "cwd": "/path/to/project",
  "env": {
    "DATABASE_URL": "sqlite:///local.db",
    "LOG_LEVEL": "debug"
  }
}
```

> **Security:** The stdio child process runs behind a filtering proxy that enforces the same host allowlist as HTTP/SSE servers. Only connections to `localhost`, `*.rocketsoftware.com`, and `*.verticacorp.com` are permitted — all other outbound HTTP/HTTPS requests are blocked.

### Config fields reference

**For `streamable-http` and `sse` servers:**

| Field | Required | Description |
|-------|----------|-------------|
| `url` | Yes | The URL of your MCP server |
| `type` | No | `"streamable-http"` (default), `"http"` (alias), or `"sse"` |
| `headers` | No | Custom headers to include in every request |
| `oauth` | No | OAuth configuration — see [Section 7](#7-oauth--sso-setup). Legacy `"auth"` field also supported. |

**For `stdio` servers:**

| Field | Required | Description |
|-------|----------|-------------|
| `type` | Yes | Must be `"stdio"` |
| `command` | Yes | Command to run (e.g., `"python3"`, `"node"`, `"npx"`) |
| `args` | No | Array of arguments passed to the command |
| `env` | No | Environment variables for the child process |
| `cwd` | No | Working directory for the child process |

### Allowed URLs

For security, the MCP connections are allowed only to:
- `localhost` / `127.0.0.1`
- `*.rocketsoftware.com`
- `*.verticacorp.com`

For `stdio` servers, URL restrictions are enforced by a local filtering proxy — the child process can only reach the same allowed hosts listed above.

If you need to connect to a different host, contact the AI.CoE team.

---

## 6. TLS / Certificate Setup

If your MCP server uses **HTTPS** with a certificate signed by a well-known authority (e.g., DigiCert, Let's Encrypt), no action is needed — it will work automatically.

If your server uses a **self-signed certificate** or a **corporate/internal CA**, you need to add that certificate to your operating system's trust store.

### Windows

1. Get the certificate file (`.cer`, `.crt`, or `.pem`) from your server administrator.
2. Double-click the certificate file → click **Install Certificate**.
3. Select **Current User** (or **Local Machine** if you have admin rights).
4. Choose **"Place all certificates in the following store"** → click **Browse** → select **"Trusted Root Certification Authorities"**.
5. Click **Next** → **Finish**.

### macOS

1. Get the certificate file from your server administrator.
2. Double-click the certificate — it opens in **Keychain Access**.
3. Add it to the **System** keychain.
4. Double-click the imported certificate → expand **Trust** → set to **"Always Trust"**.
5. Close the window and enter your password when prompted.
```

After adding the certificate, restart your MCP server in the IDE.

---

## 7. OAuth / SSO Setup

If your MCP server requires you to log in via SSO (e.g., Okta, Azure AD), this is handled automatically. When you start the server, it will open your browser for authentication.

### Option A: Automatic OAuth (simplest — as in mcp-server-4)

Add `"oauth": "oauth"` to your server config:

```json
{
  "url": "https://your-server.rocketsoftware.com/mcp",
  "type": "streamable-http",
  "oauth": "oauth"
}
```

When you start the server:
1. Your browser will open a login page.
2. Log in with your SSO credentials.
3. The browser will redirect back and you will be authenticated.

### Option B: OAuth with explicit credentials (as in mcp-server-5)

If your administrator has given you a specific Client ID and Secret:

```json
{
  "url": "https://your-server.rocketsoftware.com/mcp",
  "type": "streamable-http",
  "oauth": {
    "clientId": "your-client-id",
    "clientSecret": "your-client-secret",
    "scopes": "openid profile",
    "callbackPort": 8085
  }
}
```

When you start the server:
1. The configured `clientId` and `clientSecret` identify the MCP connector application to your identity provider.
2. You will complete user sign-in in the browser (SSO login).
3. After successful auth, the browser redirects back and the server is authenticated.

### Option C: OAuth with Client ID only (as in mcp-server-6)

If your administrator has given you only a Client ID (no secret):

```json
{
  "url": "https://your-server.rocketsoftware.com/mcp",
  "type": "streamable-http",
  "oauth": {
    "clientId": "your-client-id"
  }
}
```

When you start the server:
1. The configured `clientId` identifies the MCP connector application to your identity provider.
2. You will complete user sign-in in the browser (SSO login).
3. After successful auth, the browser redirects back and the server is authenticated.

### OAuth fields

| Field | Required | Description |
|-------|----------|-------------|
| `clientId` | No | Client ID (provided by your admin). Leave out for automatic setup. |
| `clientSecret` | No | Client Secret (if required by your admin) |
| `scopes` | No | Access scopes (your admin will tell you if needed) |
| `callbackPort` | No | Port for the login callback (default: automatic) |

> **Note:** The legacy `"auth"` field name is still supported for backward compatibility.

> **Note:** You will need to log in again each time the server restarts (tokens are not saved to disk).

---

## Troubleshooting

| Problem | What to do |
|---------|-----------|
| Server won't start / download error | Make sure your **VPN is connected**. The connector needs access to internal servers. |
| `Config file not found` | Start the server once — the config file is created automatically. Then edit it. |
| `URL '...' is not allowed` | Only `localhost` and `*.rocketsoftware.com` URLs are permitted. Contact AI.CoE for exceptions. |
| SSL/TLS certificate error | Your server's certificate is not trusted. See [Section 6](#6-tls--certificate-setup). |
| OAuth: browser doesn't open | Make sure your default browser is set. On remote/headless machines, OAuth cannot work. |
| No tools showing after start | Check that your MCP server is actually running and the URL in `config.json` is correct. |
| `Connection refused` | Your MCP server is not running or the port number is wrong. |


## Supported Platforms

| Platform | Architecture |
|----------|-------------|
| Windows | x64 |
| macOS | Apple Silicon (M1/M2/M3/M4) |
| macOS | Intel |
| Linux | x64 |
