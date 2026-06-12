# rocket-mcp-proxy

STDIO-to-HTTP proxy for MCP servers. Allows VS Code, IntelliJ, and Eclipse GitHub Copilot to connect to HTTP-based MCP servers through the standard STDIO interface.

## Repository Structure

```
mcp-http-proxy/
├── rocket_mcp_proxy.py        # Main proxy (Python source)
├── build_proxy.py             # PyInstaller build script
├── pyproject.toml             # Python package metadata
├── rocket_mcp_proxy.spec      # PyInstaller spec (auto-generated)
├── publish.sh                 # Script to upload binaries + publish npm package
├── .github/
│   └── workflows/
│       └── build.yml          # GitHub Actions — builds binaries per platform
├── npm/
│   ├── package.json           # npm package definition
│   ├── .npmrc                 # Artifactory registry config
│   ├── bin/
│   │   ├── launcher.js        # Entry point — downloads + runs the binary
│   │   └── setup.js           # Copies default config to user config dir
│   └── resources/
│       └── config.json        # Default MCP server configuration
├── build/                     # Downloaded GitHub Actions artifacts go here
│   ├── rocket_mcp_proxy-windows-latest/
│   ├── rocket_mcp_proxy-macos-latest/
│   └── rocket_mcp_proxy-ubuntu-latest/
└── dist/                      # Local PyInstaller build output
```

## How It Works

The proxy is distributed as a lightweight **npm package** (~3 KB) that downloads the correct platform binary on first run:

1. User runs `npx @aicoe/rocket-mcp-proxy` (or the IDE invokes it)
2. `launcher.js` detects the OS (`win32`, `darwin`, `linux`)
3. If the binary isn't cached locally, it downloads **only** the matching one (~27 MB) from Artifactory
4. The binary is cached at the user's config directory — subsequent runs skip the download
5. The binary is spawned with the user's arguments

The binaries are self-contained executables built by PyInstaller — **no Python required** on the end user's machine.

## Building Binaries (GitHub Actions)

This repo lives in the Rocket GitHub org where we don't have GitHub Actions access. To build:

### 1. Push to your personal GitHub repo

```bash
# Add your personal repo as a remote (one-time)
git remote add personal https://github.com/<your-username>/mcp-http-proxy.git

# Push
git push personal master
```

### 2. Trigger the build

- Go to your personal repo on GitHub
- Navigate to **Actions** → **Build Binaries**
- Click **Run workflow** (or it runs automatically on push to `master`)

The workflow builds on 3 platforms in parallel:
| Runner | Output Binary |
|---|---|
| `ubuntu-latest` | `rocket_mcp_proxy-ubuntu-latest` |
| `macos-latest` | `rocket_mcp_proxy-macos-latest` |
| `windows-latest` | `rocket_mcp_proxy-windows-latest.exe` |

### 3. Download artifacts

- Go to the completed workflow run
- Download each artifact zip from the **Artifacts** section
- Extract them into the `build/` directory:

```
build/
├── rocket_mcp_proxy-windows-latest/
│   └── rocket_mcp_proxy-windows-latest.exe
├── rocket_mcp_proxy-macos-latest/
│   └── rocket_mcp_proxy-macos-latest
└── rocket_mcp_proxy-ubuntu-latest/
    └── rocket_mcp_proxy-ubuntu-latest
```

## Publishing to Artifactory

### Using the publish script (recommended)

```bash
# Publish using version from package.json
./publish.sh

# Or specify a version
./publish.sh 1.2.0
```

The script:
1. Verifies all 3 binaries exist in `build/`
2. Uploads each binary to `cypf-npm-dev-wal` at `/rocket-mcp-proxy/<version>/`
3. Updates `package.json` and `launcher.js` versions if needed
4. Runs `npm publish` to publish the npm package

### Manual publishing

#### Upload binaries

```bash
AUTH="Basic Ymx3bW9iZjpBS0NwOG1Zb1VmS0RUUlNoTWFYQnhUamg4TDQ1Zk5zelRueDJyVGlucGJoeWlmZFl0SnQ4Nkp6d2FwZDVERE5oWVp0eGJLdk42"
BASE="https://wal-artifactory.rocketsoftware.com/artifactory/cypf-npm-dev-wal/rocket-mcp-proxy/1.0.0"

# Upload each binary
curl --retry 3 -H "Authorization: $AUTH" \
  -T build/rocket_mcp_proxy-windows-latest/rocket_mcp_proxy-windows-latest.exe \
  "$BASE/rocket_mcp_proxy-windows-latest.exe"

curl --retry 3 -H "Authorization: $AUTH" \
  -T build/rocket_mcp_proxy-macos-latest/rocket_mcp_proxy-macos-latest \
  "$BASE/rocket_mcp_proxy-macos-latest"

curl --retry 3 -H "Authorization: $AUTH" \
  -T build/rocket_mcp_proxy-ubuntu-latest/rocket_mcp_proxy-ubuntu-latest \
  "$BASE/rocket_mcp_proxy-ubuntu-latest"
```

#### Publish npm package

```bash
cd npm
npm publish
```

## Bumping Versions

When releasing a new version:

1. Update `version` in `npm/package.json`
2. Update `BINARY_VERSION` in `npm/bin/launcher.js` to match
3. Build new binaries via GitHub Actions
4. Run `./publish.sh`

Or just run `./publish.sh <new-version>` — it updates both files automatically.

## Local Development

### Build binary locally (Linux only on WSL/Linux)

```bash
pip install pyinstaller fastmcp
python build_proxy.py
# Output: dist/rocket_mcp_proxy
```

### Run the proxy directly (without building)

```bash
pip install fastmcp
python rocket_mcp_proxy.py --server mcp-server-1
```

## Artifactory Details

| Item | Location |
|---|---|
| Registry | `cypf-npm-dev-wal` (local npm repo) |
| npm package | `@aicoe/rocket-mcp-proxy` |
| Binaries path | `/rocket-mcp-proxy/<version>/<binary-name>` |
| Service account | `blwmobf` |

## End User Installation

```bash
# Windows / macOS / Linux — one command
npx @aicoe/rocket-mcp-proxy --server mcp-server-1
```

Users need to configure their npm to use the Artifactory registry:

```bash
npm config set registry https://wal-artifactory.rocketsoftware.com/artifactory/api/npm/cypf-npm-dev-wal/
```
