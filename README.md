# Logam Mulia MCP Server

MCP server for Indonesian gold (logam mulia) prices from 18+ sources.

**Source API:** [logam-mulia-api](https://github.com/iamutaki/logam-mulia-api)

## Quick Start

```bash
# Run directly (from repo)
uv run python -m logam_mulia_mcp.server
```

```bash
# Run from PyPI (no clone, no install)
uvx logam-mulia-mcp
```

## MCP Tools

| Tool | Description |
|------|-------------|
| `get_price(source, refresh?)` | Latest price from a source |
| `get_price_history(source, page?, length?, weight?, material?, material_type?)` | Paginated history |
| `list_sources()` | All 18 available sources |
| `get_all_prices()` | Latest from all sources at once |
| `get_news()` | Latest gold news articles |
| `get_news_detail(url)` | Full article text |

## Configuration

| Env | Default | Description |
|-----|---------|-------------|
| `LOGAM_MULIA_BASE_URL` | `https://logam-mulia-api.iamutaki.workers.dev` | API base URL |
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `sse` |
| `HTTP_TIMEOUT` | `30` | HTTP client timeout (s) |

## Integration

### Claude Code / Cursor / Any MCP host (via uvx)

Add to your `claude_desktop_config.json` or `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "logam-mulia": {
      "command": "uvx",
      "args": ["logam-mulia-mcp"]
    }
  }
}
```

**Optional: custom API base URL**

```json
{
  "mcpServers": {
    "logam-mulia": {
      "command": "uvx",
      "args": ["logam-mulia-mcp"],
      "env": {
        "LOGAM_MULIA_BASE_URL": "https://your-proxy.example.com"
      }
    }
  }
}
```

No install, no clone. `uvx` fetches from PyPI automatically.

### Hermes

```yaml
tools:
  mcp_servers:
    logam-mulia:
      command: uvx
      args:
        - logam-mulia-mcp
      # env:                          # optional custom base URL
      #   LOGAM_MULIA_BASE_URL: https://your-proxy.example.com
```

### Direct (any shell)

```bash
# With default API
pip install -e .
logam-mulia-mcp

# With custom API base URL
LOGAM_MULIA_BASE_URL=https://your-proxy.example.com logam-mulia-mcp
```
