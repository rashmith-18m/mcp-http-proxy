import argparse
import json
import logging
import os
import ssl as _ssl
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

# Configure logging — writes to stderr so STDIO protocol on stdout is unaffected.
# Set ROCKET_LOG_LEVEL=DEBUG for verbose output (default: INFO).
_log_level = os.environ.get("ROCKET_LOG_LEVEL", "DEBUG").upper()
logging.basicConfig(
    level=getattr(logging, _log_level, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("rocket_mcp_proxy")


def _inject_os_certificates():
    """Merge OS certificate store certs into certifi's bundle so httpx trusts system CAs."""
    logger.debug("Certificate injection: platform=%s", sys.platform)
    os_certs_pem = ""

    if sys.platform == "win32":
        # Windows: extract from Windows Certificate Store via stdlib
        cert_count = 0
        for store_name in ("ROOT", "CA"):
            try:
                for cert, encoding, trust in _ssl.enum_certificates(store_name):
                    if encoding == "x509_asn":
                        os_certs_pem += _ssl.DER_cert_to_PEM_cert(cert) + "\n"
                        cert_count += 1
            except OSError:
                pass
        logger.debug("Windows cert store: extracted %d certificates", cert_count)
    elif sys.platform == "darwin":
        # macOS: export from system keychains
        try:
            result = subprocess.run(
                ["/usr/bin/security", "find-certificate", "-a", "-p",
                 "/System/Library/Keychains/SystemRootCertificates.keychain",
                 "/Library/Keychains/System.keychain"],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0:
                os_certs_pem = result.stdout
                cert_count = os_certs_pem.count("BEGIN CERTIFICATE")
                logger.debug("macOS keychain: extracted %d certificates", cert_count)
            else:
                logger.warning("macOS security command failed (rc=%d): %s", result.returncode, result.stderr[:200])
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
            logger.warning("macOS certificate extraction failed: %s", e)
    else:
        # Linux: use system cert bundle
        for bundle_path in (
            "/etc/ssl/certs/ca-certificates.crt",
            "/etc/pki/tls/certs/ca-bundle.crt",
            "/etc/ssl/ca-bundle.pem",
        ):
            if os.path.isfile(bundle_path):
                with open(bundle_path, "r") as f:
                    os_certs_pem = f.read()
                logger.debug("Linux cert bundle: loaded from %s (%d bytes)", bundle_path, len(os_certs_pem))
                break

    if not os_certs_pem:
        logger.debug("No OS certificates found — using certifi defaults only")
        return  # No OS certs found; fall back to certifi defaults

    # Write combined PEM to a stable temp location
    cert_dir = Path(tempfile.gettempdir()) / "rocket_mcp_proxy"
    cert_dir.mkdir(exist_ok=True)
    cert_file = cert_dir / "ca-bundle.pem"

    # Combine OS certs with certifi's bundle (ensures standard public CAs remain trusted)
    import certifi
    with open(certifi.where(), "r") as f:
        combined = os_certs_pem + "\n" + f.read()

    cert_file.write_text(combined, encoding="utf-8")

    # Override certifi so httpx uses our combined bundle
    certifi.where = lambda: str(cert_file)
    os.environ["SSL_CERT_FILE"] = str(cert_file)
    logger.debug("OS certificates injected — combined bundle at %s", cert_file)


_inject_os_certificates()

# Only these host patterns are allowed. Add more as needed.
ALLOWED_HOST_SUFFIXES = [
    "localhost",
    "127.0.0.1",
    "::1",
    ".rocketsoftware.com"
]


def is_url_allowed(url: str) -> bool:
    """Check if the URL's host matches the allowlist."""
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()
    return any(
        hostname == suffix.lstrip(".") or hostname.endswith(suffix)
        for suffix in ALLOWED_HOST_SUFFIXES
    )


def parse_headers(header_values: list[str]) -> dict[str, str]:
    headers: dict[str, str] = {}
    for header_value in header_values:
        key, _, value = header_value.partition("=")
        if key and value:
            headers[key] = value
    return headers


def config_search_paths() -> list[Path]:
    """Return candidate config paths in priority order (first found wins)."""
    paths: list[Path] = []

    # 1. Sidecar: JSON file next to the executable/script
    executable_path = Path(sys.argv[0]).resolve()
    paths.append(executable_path.with_suffix(".json"))

    # 2. Platform user-config directory
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", "~/AppData/Roaming")).expanduser()
    elif sys.platform == "darwin":
        base = Path("~/Library/Application Support").expanduser()
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", "~/.config")).expanduser()
    paths.append(base / "rocket_mcp_proxy" / "config.json")

    return paths


def default_config_path() -> Path:
    """Return the first config file that exists, or the user-config path as default."""
    candidates = config_search_paths()
    logger.debug("Config search paths: %s", [str(p) for p in candidates])
    for candidate in candidates:
        if candidate.is_file():
            logger.info("Config file found: %s", candidate)
            return candidate
    fallback = candidates[-1]
    logger.warning("No config file found — will try default: %s", fallback)
    return fallback


def normalize_server_config(server_config: Any, config_path: Path, context: str = "") -> dict[str, Any]:
    if not isinstance(server_config, dict):
        suffix = f" ({context})" if context else ""
        raise ValueError(f"Config server entry must be a JSON object{suffix}: {config_path}")

    url = server_config.get("url")
    if not isinstance(url, str) or not url.strip():
        suffix = f" ({context})" if context else ""
        raise ValueError(
            f"Config server entry must define a non-empty string 'url'{suffix}: {config_path}"
        )

    headers = server_config.get("headers", {})
    if isinstance(headers, list):
        headers = parse_headers(headers)
    elif isinstance(headers, dict):
        normalized_headers: dict[str, str] = {}
        for key, value in headers.items():
            if not isinstance(key, str) or not isinstance(value, str):
                suffix = f" ({context})" if context else ""
                raise ValueError(
                    f"Config file 'headers' entries must be string key/value pairs{suffix}: {config_path}"
                )
            normalized_headers[key] = value
        headers = normalized_headers
    else:
        suffix = f" ({context})" if context else ""
        raise ValueError(
            f"Config file 'headers' must be an object or a list of key=value strings{suffix}: {config_path}"
        )

    # Transport type: "http" (streamable HTTP, default) or "sse"
    transport_type = server_config.get("type") or "http"
    if transport_type not in ("http", "sse"):
        suffix = f" ({context})" if context else ""
        raise ValueError(
            f"Config 'type' must be 'http' or 'sse'{suffix}: {config_path}"
        )

    # Auth: "oauth" (auto), {"type": "oauth", "clientId": "...", ...}, or a bearer token string
    auth_config = server_config.get("auth")
    auth: dict[str, Any] | str | None = None
    if auth_config is not None:
        if isinstance(auth_config, str):
            # "oauth" or a bearer token string
            auth = auth_config
        elif isinstance(auth_config, dict):
            auth_type = auth_config.get("type", "").lower()
            if auth_type != "oauth":
                suffix = f" ({context})" if context else ""
                raise ValueError(
                    f"Config 'auth.type' must be 'oauth' when auth is an object{suffix}: {config_path}"
                )
            auth = auth_config
        else:
            suffix = f" ({context})" if context else ""
            raise ValueError(
                f"Config 'auth' must be a string or an object{suffix}: {config_path}"
            )

    return {"url": url.strip(), "headers": headers, "type": transport_type, "auth": auth}


def load_config(config_path: Path, server_name: str | None = None) -> dict[str, Any]:
    logger.debug("Loading config from: %s", config_path)
    try:
        with config_path.open("r", encoding="utf-8") as config_file:
            config = json.load(config_file)
    except FileNotFoundError as exc:
        raise ValueError(f"Config file not found: {config_path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Config file is not valid JSON: {config_path}: {exc}") from exc

    if not isinstance(config, dict):
        raise ValueError(f"Config file must contain a JSON object: {config_path}")

    servers = config.get("servers")
    if servers is not None:
        logger.debug("Multi-server config detected — available servers: %s", list(servers.keys()))
        if not isinstance(servers, dict) or not servers:
            raise ValueError(f"Config file 'servers' must be a non-empty object: {config_path}")

        selected_server = server_name or config.get("defaultServer")
        if not selected_server:
            if len(servers) == 1:
                selected_server = next(iter(servers))
            else:
                available = ", ".join(sorted(servers))
                raise ValueError(
                    f"Config file contains multiple servers. Provide --server or defaultServer. "
                    f"Available: {available}: {config_path}"
                )

        logger.info("Selected server: '%s'", selected_server)
        server_config = servers.get(selected_server)
        if server_config is None:
            available = ", ".join(sorted(servers))
            raise ValueError(
                f"Server '{selected_server}' not found in config. Available: {available}: {config_path}"
            )

        return normalize_server_config(server_config, config_path, context=f"server={selected_server}")

    if server_name:
        raise ValueError(
            f"Config file does not define a 'servers' object. Remove --server or use multi-server format: {config_path}"
        )

    logger.debug("Single-server config format")
    return normalize_server_config(config, config_path)


def resolve_proxy_settings(args: argparse.Namespace) -> tuple[str, dict[str, str], str, Any]:
    if args.url:
        logger.info("Using CLI URL: %s", args.url)
        return args.url, parse_headers(args.headers), (args.type or "http"), None

    config_path = Path(args.config).expanduser() if args.config else default_config_path()
    config = load_config(config_path, server_name=args.server)
    transport_type = args.type if args.type else config["type"]
    logger.debug("Resolved config — url=%s type=%s headers=%d auth=%s",
                 config["url"], transport_type, len(config["headers"]),
                 "present" if config.get("auth") else "none")
    return config["url"], config["headers"], transport_type, config.get("auth")


def main():
    parser = argparse.ArgumentParser(description="STDIO proxy for HTTP-based MCP servers")
    parser.add_argument("--url", help="URL of the HTTP MCP server")
    parser.add_argument("--headers", nargs="*", default=[], help="Headers as key=value pairs (e.g. Authorization='Basic abc123')")
    parser.add_argument(
        "--config",
        help=(
            "Path to a JSON config file with either a single server ('url' and optional 'headers') "
            "or a multi-server object under 'servers'. "
            "If omitted and --url is not provided, the proxy loads a sidecar JSON file "
            "next to the executable or script."
        ),
    )
    parser.add_argument(
        "--server",
        help=(
            "Server name when using a multi-server config file. "
            "If omitted, defaultServer is used; if only one server exists, it is auto-selected."
        ),
    )
    parser.add_argument(
        "--type",
        choices=["http", "sse"],
        default=None,
        help="Transport type: 'http' (streamable HTTP, default) or 'sse'. Overrides config file.",
    )
    args = parser.parse_args()

    try:
        url, headers, transport_type, auth_config = resolve_proxy_settings(args)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    logger.info("Proxy starting — url=%s transport=%s auth=%s", url, transport_type,
                "oauth" if auth_config == "oauth" else type(auth_config).__name__ if auth_config else "none")

    if not is_url_allowed(url):
        logger.error("URL not in allowlist: %s", url)
        print(
            f"ERROR: URL '{url}' is not allowed. "
            f"Only localhost and *.rocketsoftware.com endpoints are permitted. "
            f"If you need access to an external MCP server, raise an RAC with the AI.CoE team.",
            file=sys.stderr,
        )
        sys.exit(1)

    logger.debug("URL allowlist check passed for: %s", url)

    # Ensure localhost traffic bypasses any corporate proxy.
    # Merge with existing NO_PROXY so external proxy settings are preserved.
    _bypass = {"localhost", "127.0.0.1", "::1"}
    for var in ("NO_PROXY", "no_proxy"):
        existing = os.environ.get(var, "")
        entries = {e.strip() for e in existing.split(",") if e.strip()}
        merged = ",".join(sorted(entries | _bypass))
        os.environ[var] = merged
    logger.debug("NO_PROXY set to: %s", os.environ.get("NO_PROXY", ""))

    # Import here (deferred) to avoid bytecode analysis issues with dependencies
    import mcp.types
    from fastmcp.client.auth.oauth import OAuth
    from fastmcp.client.messages import MessageHandler
    from fastmcp.client.transports import SSETransport, StreamableHttpTransport
    from fastmcp.server.providers.proxy import FastMCPProxy, ProxyProvider, StatefulProxyClient

    # Enable debug logging for OAuth/auth flow internals
    logging.getLogger("fastmcp.client.auth").setLevel(logging.DEBUG)
    logging.getLogger("fastmcp.client.transports").setLevel(logging.DEBUG)
    logging.getLogger("mcp.client.auth").setLevel(logging.DEBUG)
    logging.getLogger("httpx").setLevel(logging.INFO)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    # ---------------------------------------------------------------------------
    # Notification-forwarding message handler
    # ---------------------------------------------------------------------------
    # When the upstream MCP server sends notifications like tools/list_changed,
    # resources/list_changed, or prompts/list_changed, we need to:
    #   1. Invalidate the ProxyProvider's cache so the next list_tools() fetches fresh data
    #   2. Forward the notification to the downstream IDE session via STDIO
    # Without this, dynamic tool loading (progressive tool discovery) is broken.

    class NotificationForwardingHandler(MessageHandler):
        """Intercepts list-changed notifications from upstream and forwards them downstream."""

        def __init__(self):
            self._proxy: FastMCPProxy | None = None

        def set_proxy(self, proxy: FastMCPProxy) -> None:
            self._proxy = proxy

        def _get_provider(self) -> ProxyProvider | None:
            """Get the ProxyProvider from the proxy server."""
            if self._proxy is None:
                return None
            for provider in self._proxy.providers:
                if isinstance(provider, ProxyProvider):
                    return provider
            return None

        def _get_downstream_sessions(self):
            """Get all active downstream server sessions."""
            from mcp import ServerSession
            if self._proxy is None:
                return []
            # The StatefulProxyClient._caches maps ServerSession → Client
            # We can get the sessions from there, but more reliably we use
            # the proxy's _mcp_server which tracks active sessions via request_ctx
            # For STDIO there's typically one session — get it from _caches keys
            client_factory = self._proxy.client_factory
            if hasattr(client_factory, '__self__'):
                stateful_client = client_factory.__self__
                if hasattr(stateful_client, '_caches'):
                    return list(stateful_client._caches.keys())
            return []

        async def on_tool_list_changed(
            self, message: mcp.types.ToolListChangedNotification
        ) -> None:
            logger.info("Upstream notification: tools/list_changed — invalidating cache and forwarding")
            provider = self._get_provider()
            if provider is not None:
                provider._tools_cache = None
            for session in self._get_downstream_sessions():
                try:
                    await session.send_tool_list_changed()
                    logger.debug("Forwarded tools/list_changed to downstream session")
                except Exception as e:
                    logger.warning("Failed to forward tools/list_changed: %s", e)

        async def on_resource_list_changed(
            self, message: mcp.types.ResourceListChangedNotification
        ) -> None:
            logger.info("Upstream notification: resources/list_changed — invalidating cache and forwarding")
            provider = self._get_provider()
            if provider is not None:
                provider._resources_cache = None
                provider._templates_cache = None
            for session in self._get_downstream_sessions():
                try:
                    await session.send_resource_list_changed()
                    logger.debug("Forwarded resources/list_changed to downstream session")
                except Exception as e:
                    logger.warning("Failed to forward resources/list_changed: %s", e)

        async def on_prompt_list_changed(
            self, message: mcp.types.PromptListChangedNotification
        ) -> None:
            logger.info("Upstream notification: prompts/list_changed — invalidating cache and forwarding")
            provider = self._get_provider()
            if provider is not None:
                provider._prompts_cache = None
            for session in self._get_downstream_sessions():
                try:
                    await session.send_prompt_list_changed()
                    logger.debug("Forwarded prompts/list_changed to downstream session")
                except Exception as e:
                    logger.warning("Failed to forward prompts/list_changed: %s", e)

        async def on_resource_updated(
            self, message: mcp.types.ResourceUpdatedNotification
        ) -> None:
            logger.info("Upstream notification: resources/updated uri=%s — forwarding", message.params.uri)
            for session in self._get_downstream_sessions():
                try:
                    await session.send_resource_updated(message.params.uri)
                    logger.debug("Forwarded resources/updated to downstream session")
                except Exception as e:
                    logger.warning("Failed to forward resources/updated: %s", e)

        async def on_cancelled(
            self, message: mcp.types.CancelledNotification
        ) -> None:
            logger.info("Upstream notification: cancelled requestId=%s — forwarding", message.params.requestId)
            for session in self._get_downstream_sessions():
                try:
                    await session.send_notification(
                        mcp.types.ServerNotification(
                            mcp.types.CancelledNotification(
                                method="notifications/cancelled",
                                params=mcp.types.CancelledNotificationParams(
                                    requestId=message.params.requestId,
                                    reason=message.params.reason,
                                ),
                            )
                        )
                    )
                    logger.debug("Forwarded cancelled to downstream session")
                except Exception as e:
                    logger.warning("Failed to forward cancelled: %s", e)

    notification_handler = NotificationForwardingHandler()

    # Resolve auth parameter for transport
    auth = None
    if auth_config == "oauth":
        logger.info("OAuth mode: automatic discovery (no pre-configured client credentials)")
        auth = "oauth"
    elif isinstance(auth_config, dict):
        # OAuth with explicit client credentials
        oauth_kwargs: dict[str, Any] = {}
        if auth_config.get("clientId"):
            oauth_kwargs["client_id"] = auth_config["clientId"]
        if auth_config.get("clientSecret"):
            oauth_kwargs["client_secret"] = auth_config["clientSecret"]
        if auth_config.get("scopes"):
            oauth_kwargs["scopes"] = auth_config["scopes"]
        if auth_config.get("callbackPort"):
            oauth_kwargs["callback_port"] = int(auth_config["callbackPort"])
        logger.info("OAuth mode: explicit credentials — client_id=%s scopes=%s",
                    oauth_kwargs.get("client_id", "<none>"), oauth_kwargs.get("scopes", "<none>"))
        auth = OAuth(**oauth_kwargs)
    elif isinstance(auth_config, str) and auth_config != "oauth":
        # Bearer token string
        logger.info("Auth mode: static bearer token")
        auth = auth_config
    else:
        logger.info("Auth mode: none (no auth configured)")

    logger.info("Creating %s transport to %s", transport_type.upper(), url)
    if transport_type == "sse":
        transport = SSETransport(url, headers=headers if headers else None, auth=auth)
    else:
        transport = StreamableHttpTransport(url, headers=headers if headers else None, auth=auth)

    if hasattr(transport, 'auth') and transport.auth is not None:
        auth_obj = transport.auth
        logger.info("Transport auth object: %s", type(auth_obj).__name__)
        if hasattr(auth_obj, 'mcp_url'):
            logger.info("OAuth bound to MCP URL: %s", auth_obj.mcp_url)
        if hasattr(auth_obj, 'redirect_port'):
            logger.info("OAuth callback will listen on http://localhost:%d/callback", auth_obj.redirect_port)

    # Use StatefulProxyClient to maintain session continuity:
    # all requests within the same downstream session reuse ONE upstream
    # HTTP connection → same Mcp-Session-Id → server sees a persistent session.
    logger.debug("Creating StatefulProxyClient with session caching")
    client = StatefulProxyClient(transport=transport, message_handler=notification_handler)
    proxy = FastMCPProxy(client_factory=client.new_stateful, name="MCP Proxy")
    # Wire the proxy reference so the notification handler can forward to downstream sessions
    notification_handler.set_proxy(proxy)

    # ---------------------------------------------------------------------------
    # Fix #4: Forward roots/list_changed from IDE → upstream server
    # ---------------------------------------------------------------------------
    # When the IDE's workspace folders change, it sends notifications/roots/list_changed.
    # The proxy server must forward this upstream so servers that use workspace roots
    # can re-query and adapt.
    async def _handle_roots_list_changed(notification):
        logger.info("IDE notification: roots/list_changed — forwarding upstream")
        # Forward to all cached upstream sessions
        for session_key, upstream_client in list(client._caches.items()):
            try:
                if upstream_client.is_connected():
                    await upstream_client.send_roots_list_changed()
                    logger.debug("Forwarded roots/list_changed to upstream server")
            except Exception as e:
                logger.warning("Failed to forward roots/list_changed upstream: %s", e)

    proxy._mcp_server.notification_handlers[mcp.types.RootsListChangedNotification] = _handle_roots_list_changed

    # ---------------------------------------------------------------------------
    # Fix #5: Proxy completion/complete requests to upstream server
    # ---------------------------------------------------------------------------
    # When the IDE requests tab-completion for prompt arguments or resource
    # template URIs, the proxy must forward the request upstream and return results.
    async def _handle_complete_request(req: mcp.types.CompleteRequest) -> mcp.types.ServerResult:
        logger.info("IDE request: completion/complete ref=%s arg=%s", req.params.ref, req.params.argument)
        try:
            upstream = await notification_handler._get_provider()._get_client()
            async with upstream:
                # Convert CompletionArgument back to dict for client API
                argument_dict = {"name": req.params.argument.name, "value": req.params.argument.value}
                # Convert CompletionContext back to dict if present
                context_args = None
                if req.params.context is not None and hasattr(req.params.context, 'arguments'):
                    context_args = req.params.context.arguments
                result = await upstream.complete_mcp(
                    ref=req.params.ref,
                    argument=argument_dict,
                    context_arguments=context_args,
                )
                logger.debug("Completion result: %d values", len(result.completion.values) if result.completion else 0)
                return mcp.types.ServerResult(result)
        except Exception as e:
            logger.warning("Completion request failed: %s", e)
            return mcp.types.ServerResult(
                mcp.types.CompleteResult(
                    completion=mcp.types.Completion(values=[], total=None, hasMore=None)
                )
            )

    proxy._mcp_server.request_handlers[mcp.types.CompleteRequest] = _handle_complete_request

    # ---------------------------------------------------------------------------
    # Fix #1: Advertise resources.listChanged and prompts.listChanged capabilities
    # ---------------------------------------------------------------------------
    # The default run_stdio_async() only passes tools_changed=True. We need all
    # three so the IDE knows it can expect dynamic list changes for tools,
    # resources, and prompts.
    from mcp.server.lowlevel.server import NotificationOptions
    from mcp.server.stdio import stdio_server

    # ---------------------------------------------------------------------------
    # Fix #2: Forward cancellation from IDE → upstream server
    # ---------------------------------------------------------------------------
    # When the IDE cancels a tool call, the SDK cancels the proxy's handler task
    # via anyio. But with a persistent StatefulProxyClient session, the upstream
    # server doesn't know the request was cancelled — it keeps working.
    # We wrap ProxyTool.run() to catch the cancellation and forward it upstream.
    import anyio
    from fastmcp.server.providers.proxy import ProxyTool

    _original_proxy_tool_run = ProxyTool.run

    async def _cancellation_aware_run(self, arguments, context=None):
        """Wraps ProxyTool.run to forward cancellation to the upstream server."""
        try:
            return await _original_proxy_tool_run(self, arguments, context)
        except BaseException as exc:
            if isinstance(exc, anyio.get_cancelled_exc_class()):
                # Task was cancelled (IDE sent notifications/cancelled)
                # Try to forward cancellation to upstream server
                logger.info("Tool call cancelled by IDE — forwarding cancellation upstream")
                try:
                    upstream_client = await self._get_client()
                    if upstream_client.is_connected() and hasattr(upstream_client, 'session'):
                        # The upstream request_id isn't easily accessible here,
                        # but closing/disconnecting the client session signals the server
                        await upstream_client._disconnect(force=True)
                        logger.debug("Upstream client disconnected to signal cancellation")
                except Exception as cancel_err:
                    logger.warning("Failed to forward cancellation upstream: %s", cancel_err)
            raise

    ProxyTool.run = _cancellation_aware_run

    logger.info("Proxy server ready — waiting for STDIO connections")
    logger.info("Platform: %s %s | Python: %s", sys.platform, os.uname().machine if hasattr(os, 'uname') else 'unknown', sys.version.split()[0])
    try:
        async def _run_with_full_capabilities():
            async with stdio_server() as (read_stream, write_stream):
                await proxy._mcp_server.run(
                    read_stream,
                    write_stream,
                    proxy._mcp_server.create_initialization_options(
                        notification_options=NotificationOptions(
                            tools_changed=True,
                            resources_changed=True,
                            prompts_changed=True,
                        ),
                    ),
                )

        anyio.run(_run_with_full_capabilities)
    except KeyboardInterrupt:
        logger.info("Proxy stopped by user (KeyboardInterrupt)")
    except Exception as exc:
        logger.exception("Proxy crashed with unhandled exception: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()