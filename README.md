# Logam Mulia MCP Server

MCP server for Indonesian gold (logam mulia) prices from 18+ sources.

**Source API:** [logam-mulia-api](https://github.com/iamutaki/logam-mulia-api)

## Quick Start

```bash
# Run directly (from repo)
uv run python -m logam_mulia_mcp.server
```

```bash
# Run from GitHub (no clone needed)
uvx --from git+https://github.com/rizalibnu/logam-mulia-mcp logam-mulia-mcp
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

```json
{
  "mcpServers": {
    "logam-mulia": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/rizalibnu/logam-mulia-mcp", "logam-mulia-mcp"]
    }
  }
}
```

No install, no clone. `uvx` fetches & caches automatically.

### Hermes

```yaml
tools:
  mcp_servers:
    logam-mulia:
      command: uvx
      args:
        - --from
        - git+https://github.com/rizalibnu/logam-mulia-mcp
        - logam-mulia-mcp
```

### Direct (any shell)

```bash
pip install -e .
logam-mulia-mcp
```
