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

### Categories

- **preference**: User preferences and choices
- **fact**: Verified facts about user, project, or domain
- **context**: Current context or state information
- **note**: General notes and observations

### Subjects

- **user**: About the user
- **project**: About the current project
- **tool**: About tools and their usage
- **assistant**: About Claude's behavior
- **other**: Anything else

### Sources

- **explicit**: User explicitly stated this
- **inferred**: Derived from context
- **observed**: Observed from behavior

## CLI Usage

All commands via `uv run ~/.claude/skills/memory/scripts/memory_cli.py <command>`.

### Commands

#### add

Add a new memory.

```bash
# Simple note
uv run ~/.claude/skills/memory/scripts/memory_cli.py add "User prefers dark mode"

# With full metadata
uv run ~/.claude/skills/memory/scripts/memory_cli.py add "User prefers CLI over GUI" \
  --category preference \
  --subject user \
  --tags cli --tags ui \
  --confidence 0.9 \
  --source explicit

# Project fact
uv run ~/.claude/skills/memory/scripts/memory_cli.py add "Project uses Python 3.10+" \
  --category fact \
  --subject project \
  --tags python --tags requirements
```

#### list

List memories with optional filters.

```bash
# List all
uv run ~/.claude/skills/memory/scripts/memory_cli.py list

# Filter by category
uv run ~/.claude/skills/memory/scripts/memory_cli.py list --category preference

# Filter by subject
uv run ~/.claude/skills/memory/scripts/memory_cli.py list --subject user

# Filter by tag
uv run ~/.claude/skills/memory/scripts/memory_cli.py list --tag python

# Filter by minimum confidence
uv run ~/.claude/skills/memory/scripts/memory_cli.py list --min-confidence 0.8

# Combine filters
uv run ~/.claude/skills/memory/scripts/memory_cli.py list --category fact --subject project --limit 10

# Output as JSON
uv run ~/.claude/skills/memory/scripts/memory_cli.py list --json-output
```

#### get

Get a memory by ID (supports partial match).

```bash
uv run ~/.claude/skills/memory/scripts/memory_cli.py get mem_20260117_abc12345

# Partial ID match
uv run ~/.claude/skills/memory/scripts/memory_cli.py get abc12345

# Output as JSON
uv run ~/.claude/skills/memory/scripts/memory_cli.py get mem_20260117_abc12345 --json-output
```

#### update

Update an existing memory.

```bash
# Update content
uv run ~/.claude/skills/memory/scripts/memory_cli.py update mem_20260117_abc12345 \
  --content "Updated content here"

# Update category and confidence
uv run ~/.claude/skills/memory/scripts/memory_cli.py update mem_20260117_abc12345 \
  --category fact \
  --confidence 0.95

# Replace tags
uv run ~/.claude/skills/memory/scripts/memory_cli.py update mem_20260117_abc12345 \
  --tags new-tag --tags another-tag
```

#### delete

Delete a memory.

```bash
# With confirmation
uv run ~/.claude/skills/memory/scripts/memory_cli.py delete mem_20260117_abc12345

# Force delete (no confirmation)
uv run ~/.claude/skills/memory/scripts/memory_cli.py delete mem_20260117_abc12345 --force
```

#### search

Search memories by content and tags.

```bash
uv run ~/.claude/skills/memory/scripts/memory_cli.py search "python"
uv run ~/.claude/skills/memory/scripts/memory_cli.py search "CLI" --limit 5
uv run ~/.claude/skills/memory/scripts/memory_cli.py search "preferences" --json-output
```

#### stats

Show memory statistics.

```bash
uv run ~/.claude/skills/memory/scripts/memory_cli.py stats
```

Output includes:
- Total memories count
- Average confidence
- Count by category
- Count by subject
- All unique tags

#### export

Export all memories as JSON.

```bash
# Compact JSON
uv run ~/.claude/skills/memory/scripts/memory_cli.py export

# Pretty-printed JSON
uv run ~/.claude/skills/memory/scripts/memory_cli.py export --pretty

# Save to file
uv run ~/.claude/skills/memory/scripts/memory_cli.py export --pretty > backup.json
```

#### import

Import memories from a JSON file.

```bash
# Merge with existing (skip duplicates)
uv run ~/.claude/skills/memory/scripts/memory_cli.py import backup.json --merge

# Replace all existing memories
uv run ~/.claude/skills/memory/scripts/memory_cli.py import backup.json --replace
```

#### clear

Clear all memories (with confirmation).

```bash
uv run ~/.claude/skills/memory/scripts/memory_cli.py clear
```

## When to Use

- **Store user preferences**: Remember how the user likes things done
- **Track project facts**: Keep important project information
- **Build knowledge base**: Accumulate domain knowledge over time
- **Maintain context**: Store current working context
- **Learn from interactions**: Record inferred patterns and preferences

## Example Workflow

```bash
# At session start - check what we know
uv run ~/.claude/skills/memory/scripts/memory_cli.py list --limit 10

# User mentions a preference
uv run ~/.claude/skills/memory/scripts/memory_cli.py add "User prefers TypeScript over JavaScript" \
  --category preference --subject user --tags typescript --tags languages

# Learn a project fact
uv run ~/.claude/skills/memory/scripts/memory_cli.py add "Project uses PostgreSQL 15" \
  --category fact --subject project --tags database --confidence 1.0

# Later, search for relevant memories
uv run ~/.claude/skills/memory/scripts/memory_cli.py search "database"

# Check memory stats
uv run ~/.claude/skills/memory/scripts/memory_cli.py stats
```