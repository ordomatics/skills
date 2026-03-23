---
name: memory
description: JSON-based semantic memory system for Claude. Use when Claude needs to store, retrieve, update, or search persistent knowledge across conversations. Stores structured memories with categories, tags, confidence scores, and metadata. Memory is stored in .claude/memories/index.json.
---

# Memory Skill

JSON-based semantic memory system for persistent knowledge storage.

## Memory Location

All memories are stored in `.claude/memories/index.json`.

## Memory Schema

Each memory entry has:

```json
{
  "id": "mem_20260117_abc12345",
  "category": "preference",
  "subject": "user",
  "content": "User prefers CLI over GUI",
  "tags": ["cli", "preferences"],
  "confidence": 0.9,
  "source": "explicit",
  "created_at": "2026-01-17T12:00:00Z",
  "updated_at": "2026-01-17T12:00:00Z"
}
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier (auto-generated) |
| `category` | enum | `preference`, `fact`, `context`, `note` |
| `subject` | enum | `user`, `project`, `tool`, `assistant`, `other` |
| `content` | string | The actual memory content |
| `tags` | array | Tags for filtering and organization |
| `confidence` | float | 0.0-1.0 confidence score |
| `source` | enum | `explicit`, `inferred`, `observed` |
| `created_at` | datetime | Creation timestamp |
| `updated_at` | datetime | Last update timestamp |

## CLI Usage

All commands via `uv run ~/.claude/skills/memory/scripts/memory_cli.py <command>`.

### Commands

| Command | Description |
|---------|-------------|
| `add "content"` | Add a new memory with optional metadata flags |
| `list` | List memories with optional filters (--category, --subject, --tag) |
| `get <id>` | Get a memory by full or partial ID |
| `update <id>` | Update content, category, tags, or confidence |
| `delete <id>` | Delete a memory (with confirmation) |
| `search "query"` | Search memories by content and tags |
| `stats` | Show memory statistics (counts, averages, tags) |
| `export` | Export all memories as JSON |
| `import <file>` | Import memories from JSON (--merge or --replace) |
| `clear` | Clear all memories (with confirmation) |

### Example Workflow

```bash
# At session start — check what we know
uv run ~/.claude/skills/memory/scripts/memory_cli.py list --limit 10

# Store a user preference
uv run ~/.claude/skills/memory/scripts/memory_cli.py add "User prefers TypeScript over JavaScript" \
  --category preference --subject user --tags typescript --tags languages

# Store a project fact
uv run ~/.claude/skills/memory/scripts/memory_cli.py add "Project uses PostgreSQL 15" \
  --category fact --subject project --tags database --confidence 1.0

# Search for relevant memories
uv run ~/.claude/skills/memory/scripts/memory_cli.py search "database"
```

## When to Use

- **Store user preferences**: Remember how the user likes things done
- **Track project facts**: Keep important project information
- **Build knowledge base**: Accumulate domain knowledge over time
- **Maintain context**: Store current working context
- **Learn from interactions**: Record inferred patterns and preferences
