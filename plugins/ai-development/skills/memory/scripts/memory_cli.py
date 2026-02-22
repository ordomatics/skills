#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "click>=8.0",
# ]
# ///
"""
Memory CLI - JSON-based Semantic Memory System

A structured memory system for Claude with schema-enforced entries.
Memory root: .claude/memories/ (relative to current directory)

Memory Types:
- Semantic memory: facts, preferences, knowledge (this CLI)
- Episodic memory: conversation history (trajectories)
- Procedural memory: how-to, workflows (skills, CLAUDE.md)

Each memory entry has:
- id: unique identifier
- category: preference, fact, context, note
- subject: user, project, tool, assistant
- content: the actual memory content
- tags: list of tags for filtering
- confidence: 0.0-1.0 confidence score
- source: explicit, inferred, observed
- created_at/updated_at: timestamps
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from uuid import uuid4

import click


# =============================================================================
# CONFIGURATION
# =============================================================================

MEMORY_ROOT = Path.cwd() / ".claude" / "memories"
INDEX_FILE = MEMORY_ROOT / "index.json"

VALID_CATEGORIES = ["preference", "fact", "context", "note"]
VALID_SUBJECTS = ["user", "project", "tool", "assistant", "other"]
VALID_SOURCES = ["explicit", "inferred", "observed"]


# =============================================================================
# DATA STRUCTURES
# =============================================================================

def get_memory_root() -> Path:
    """Get the memory root directory, creating if needed."""
    MEMORY_ROOT.mkdir(parents=True, exist_ok=True)
    return MEMORY_ROOT


def generate_id() -> str:
    """Generate a unique memory ID."""
    date_part = datetime.now().strftime("%Y%m%d")
    uuid_part = uuid4().hex[:8]
    return f"mem_{date_part}_{uuid_part}"


def create_memory_entry(
    content: str,
    category: str = "note",
    subject: str = "user",
    tags: List[str] = None,
    confidence: float = 1.0,
    source: str = "explicit",
    memory_id: str = None
) -> Dict[str, Any]:
    """Create a new memory entry with all required fields."""
    now = datetime.now().isoformat()
    
    return {
        "id": memory_id or generate_id(),
        "category": category,
        "subject": subject,
        "content": content,
        "tags": tags or [],
        "confidence": max(0.0, min(1.0, confidence)),
        "source": source,
        "created_at": now,
        "updated_at": now
    }


def validate_memory(memory: Dict[str, Any]) -> List[str]:
    """Validate a memory entry, return list of errors."""
    errors = []
    
    if not memory.get("id"):
        errors.append("Missing 'id' field")
    
    if not memory.get("content"):
        errors.append("Missing 'content' field")
    
    category = memory.get("category")
    if category and category not in VALID_CATEGORIES:
        errors.append(f"Invalid category '{category}'. Must be one of: {VALID_CATEGORIES}")
    
    subject = memory.get("subject")
    if subject and subject not in VALID_SUBJECTS:
        errors.append(f"Invalid subject '{subject}'. Must be one of: {VALID_SUBJECTS}")
    
    source = memory.get("source")
    if source and source not in VALID_SOURCES:
        errors.append(f"Invalid source '{source}'. Must be one of: {VALID_SOURCES}")
    
    confidence = memory.get("confidence")
    if confidence is not None:
        if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
            errors.append("Confidence must be a number between 0.0 and 1.0")
    
    return errors


# =============================================================================
# INDEX MANAGEMENT
# =============================================================================

def load_index() -> Dict[str, Any]:
    """Load the memory index."""
    if not INDEX_FILE.exists():
        return {"memories": [], "version": "1.0"}
    
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_index(index: Dict[str, Any]):
    """Save the memory index."""
    get_memory_root()  # Ensure directory exists
    
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)


def add_memory_to_index(memory: Dict[str, Any]) -> bool:
    """Add a memory to the index. Returns False if ID already exists."""
    index = load_index()
    
    # Check for duplicate ID
    for existing in index["memories"]:
        if existing["id"] == memory["id"]:
            return False
    
    index["memories"].append(memory)
    save_index(index)
    return True


def update_memory_in_index(memory_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update a memory in the index. Returns updated memory or None if not found."""
    index = load_index()
    
    for i, mem in enumerate(index["memories"]):
        if mem["id"] == memory_id:
            # Apply updates
            for key, value in updates.items():
                if key != "id" and key != "created_at":  # Don't update id or created_at
                    mem[key] = value
            mem["updated_at"] = datetime.now().isoformat()
            
            index["memories"][i] = mem
            save_index(index)
            return mem
    
    return None


def delete_memory_from_index(memory_id: str) -> bool:
    """Delete a memory from the index. Returns True if found and deleted."""
    index = load_index()
    
    for i, mem in enumerate(index["memories"]):
        if mem["id"] == memory_id:
            del index["memories"][i]
            save_index(index)
            return True
    
    return False


def get_memory_by_id(memory_id: str) -> Optional[Dict[str, Any]]:
    """Get a memory by ID."""
    index = load_index()
    
    for mem in index["memories"]:
        if mem["id"] == memory_id:
            return mem
    
    return None


def find_memory_by_partial_id(partial_id: str) -> Optional[Dict[str, Any]]:
    """Find a memory by partial ID match."""
    index = load_index()
    
    matches = [m for m in index["memories"] if m["id"].startswith(partial_id) or partial_id in m["id"]]
    
    if len(matches) == 1:
        return matches[0]
    elif len(matches) > 1:
        return None  # Ambiguous
    
    return None


def filter_memories(
    category: str = None,
    subject: str = None,
    tag: str = None,
    min_confidence: float = None,
    source: str = None
) -> List[Dict[str, Any]]:
    """Filter memories by various criteria."""
    index = load_index()
    results = index["memories"]
    
    if category:
        results = [m for m in results if m.get("category") == category]
    
    if subject:
        results = [m for m in results if m.get("subject") == subject]
    
    if tag:
        results = [m for m in results if tag in m.get("tags", [])]
    
    if min_confidence is not None:
        results = [m for m in results if m.get("confidence", 0) >= min_confidence]
    
    if source:
        results = [m for m in results if m.get("source") == source]
    
    return results


def search_memories(query: str) -> List[Dict[str, Any]]:
    """Search memories by content."""
    index = load_index()
    query_lower = query.lower()
    
    results = []
    for mem in index["memories"]:
        content = mem.get("content", "").lower()
        tags = " ".join(mem.get("tags", [])).lower()
        
        if query_lower in content or query_lower in tags:
            results.append(mem)
    
    return results


# =============================================================================
# CLI COMMANDS
# =============================================================================

@click.group()
@click.version_option(version="2.0.0")
def cli():
    """
    Memory CLI - JSON-based semantic memory for Claude.
    
    Stores structured memories with categories, tags, and confidence scores.
    Memory location: .claude/memories/index.json
    """
    pass


@cli.command()
@click.argument("content")
@click.option("--category", "-c", type=click.Choice(VALID_CATEGORIES), default="note", help="Memory category")
@click.option("--subject", "-s", type=click.Choice(VALID_SUBJECTS), default="user", help="Memory subject")
@click.option("--tags", "-t", multiple=True, help="Tags (can specify multiple)")
@click.option("--confidence", "-conf", type=float, default=1.0, help="Confidence score (0.0-1.0)")
@click.option("--source", type=click.Choice(VALID_SOURCES), default="explicit", help="Memory source")
@click.option("--id", "memory_id", default=None, help="Custom memory ID (auto-generated if not provided)")
def add(content: str, category: str, subject: str, tags: tuple, confidence: float, source: str, memory_id: str):
    """
    Add a new memory.
    
    CONTENT: The memory content text
    """
    memory = create_memory_entry(
        content=content,
        category=category,
        subject=subject,
        tags=list(tags),
        confidence=confidence,
        source=source,
        memory_id=memory_id
    )
    
    # Validate
    errors = validate_memory(memory)
    if errors:
        for error in errors:
            click.echo(f"Error: {error}", err=True)
        sys.exit(1)
    
    # Add to index
    if not add_memory_to_index(memory):
        raise click.ClickException(f"Memory with ID '{memory['id']}' already exists")
    
    click.echo(f"Memory added: {memory['id']}")
    click.echo(f"  Category: {memory['category']}")
    click.echo(f"  Subject: {memory['subject']}")
    click.echo(f"  Content: {memory['content'][:50]}{'...' if len(memory['content']) > 50 else ''}")


@cli.command("list")
@click.option("--category", "-c", type=click.Choice(VALID_CATEGORIES), help="Filter by category")
@click.option("--subject", "-s", type=click.Choice(VALID_SUBJECTS), help="Filter by subject")
@click.option("--tag", "-t", help="Filter by tag")
@click.option("--min-confidence", "-conf", type=float, help="Minimum confidence score")
@click.option("--source", type=click.Choice(VALID_SOURCES), help="Filter by source")
@click.option("--limit", "-l", type=int, default=20, help="Maximum results")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def list_memories(category: str, subject: str, tag: str, min_confidence: float, source: str, limit: int, json_output: bool):
    """List memories with optional filters."""
    memories = filter_memories(
        category=category,
        subject=subject,
        tag=tag,
        min_confidence=min_confidence,
        source=source
    )
    
    if not memories:
        click.echo("No memories found.")
        return
    
    # Sort by updated_at descending
    memories.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    memories = memories[:limit]
    
    if json_output:
        click.echo(json.dumps(memories, indent=2, ensure_ascii=False))
        return
    
    click.echo(f"Found {len(memories)} memories:\n")
    
    for mem in memories:
        conf = mem.get("confidence", 1.0)
        conf_bar = "●" * int(conf * 5) + "○" * (5 - int(conf * 5))
        
        click.echo(f"[{mem['id']}]")
        click.echo(f"  {mem.get('category', '?'):10} | {mem.get('subject', '?'):8} | {conf_bar} ({conf:.1f})")
        click.echo(f"  {mem.get('content', '')[:70]}{'...' if len(mem.get('content', '')) > 70 else ''}")
        
        tags = mem.get("tags", [])
        if tags:
            click.echo(f"  Tags: {', '.join(tags)}")
        click.echo()


@cli.command()
@click.argument("memory_id")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def get(memory_id: str, json_output: bool):
    """
    Get a memory by ID.
    
    MEMORY_ID: Full or partial memory ID
    """
    # Try exact match first
    memory = get_memory_by_id(memory_id)
    
    # Try partial match
    if not memory:
        memory = find_memory_by_partial_id(memory_id)
    
    if not memory:
        raise click.ClickException(f"Memory not found: {memory_id}")
    
    if json_output:
        click.echo(json.dumps(memory, indent=2, ensure_ascii=False))
        return
    
    click.echo(f"Memory: {memory['id']}")
    click.echo("=" * 50)
    click.echo(f"Category:   {memory.get('category', 'N/A')}")
    click.echo(f"Subject:    {memory.get('subject', 'N/A')}")
    click.echo(f"Confidence: {memory.get('confidence', 'N/A')}")
    click.echo(f"Source:     {memory.get('source', 'N/A')}")
    click.echo(f"Created:    {memory.get('created_at', 'N/A')}")
    click.echo(f"Updated:    {memory.get('updated_at', 'N/A')}")
    
    tags = memory.get("tags", [])
    if tags:
        click.echo(f"Tags:       {', '.join(tags)}")
    
    click.echo()
    click.echo("Content:")
    click.echo("-" * 50)
    click.echo(memory.get("content", ""))


@cli.command()
@click.argument("memory_id")
@click.option("--content", "-c", help="New content")
@click.option("--category", type=click.Choice(VALID_CATEGORIES), help="New category")
@click.option("--subject", type=click.Choice(VALID_SUBJECTS), help="New subject")
@click.option("--tags", "-t", multiple=True, help="New tags (replaces existing)")
@click.option("--confidence", "-conf", type=float, help="New confidence score")
@click.option("--source", type=click.Choice(VALID_SOURCES), help="New source")
def update(memory_id: str, content: str, category: str, subject: str, tags: tuple, confidence: float, source: str):
    """
    Update an existing memory.
    
    MEMORY_ID: Full or partial memory ID
    """
    # Find memory
    memory = get_memory_by_id(memory_id)
    if not memory:
        memory = find_memory_by_partial_id(memory_id)
    
    if not memory:
        raise click.ClickException(f"Memory not found: {memory_id}")
    
    # Build updates
    updates = {}
    if content is not None:
        updates["content"] = content
    if category is not None:
        updates["category"] = category
    if subject is not None:
        updates["subject"] = subject
    if tags:
        updates["tags"] = list(tags)
    if confidence is not None:
        updates["confidence"] = max(0.0, min(1.0, confidence))
    if source is not None:
        updates["source"] = source
    
    if not updates:
        raise click.ClickException("No updates provided")
    
    # Apply updates
    updated = update_memory_in_index(memory["id"], updates)
    if updated:
        click.echo(f"Memory updated: {updated['id']}")
    else:
        raise click.ClickException("Failed to update memory")


@cli.command()
@click.argument("memory_id")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
def delete(memory_id: str, force: bool):
    """
    Delete a memory.
    
    MEMORY_ID: Full or partial memory ID
    """
    # Find memory
    memory = get_memory_by_id(memory_id)
    if not memory:
        memory = find_memory_by_partial_id(memory_id)
    
    if not memory:
        raise click.ClickException(f"Memory not found: {memory_id}")
    
    if not force:
        click.echo(f"About to delete: {memory['id']}")
        click.echo(f"  Content: {memory.get('content', '')[:50]}...")
        if not click.confirm("Continue?"):
            click.echo("Cancelled.")
            return
    
    if delete_memory_from_index(memory["id"]):
        click.echo(f"Memory deleted: {memory['id']}")
    else:
        raise click.ClickException("Failed to delete memory")


@cli.command()
@click.argument("query")
@click.option("--limit", "-l", type=int, default=10, help="Maximum results")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def search(query: str, limit: int, json_output: bool):
    """
    Search memories by content.
    
    QUERY: Search term
    """
    results = search_memories(query)
    
    if not results:
        click.echo(f"No memories found for: {query}")
        return
    
    results = results[:limit]
    
    if json_output:
        click.echo(json.dumps(results, indent=2, ensure_ascii=False))
        return
    
    click.echo(f"Found {len(results)} memories matching '{query}':\n")
    
    for mem in results:
        click.echo(f"[{mem['id']}] {mem.get('category', '?')} | {mem.get('subject', '?')}")
        click.echo(f"  {mem.get('content', '')[:70]}{'...' if len(mem.get('content', '')) > 70 else ''}")
        click.echo()


@cli.command()
def stats():
    """Show memory statistics."""
    index = load_index()
    memories = index.get("memories", [])
    
    if not memories:
        click.echo("No memories stored.")
        return
    
    # Count by category
    by_category = {}
    for mem in memories:
        cat = mem.get("category", "unknown")
        by_category[cat] = by_category.get(cat, 0) + 1
    
    # Count by subject
    by_subject = {}
    for mem in memories:
        subj = mem.get("subject", "unknown")
        by_subject[subj] = by_subject.get(subj, 0) + 1
    
    # Average confidence
    confidences = [m.get("confidence", 1.0) for m in memories]
    avg_confidence = sum(confidences) / len(confidences)
    
    # All tags
    all_tags = set()
    for mem in memories:
        all_tags.update(mem.get("tags", []))
    
    click.echo("Memory Statistics")
    click.echo("=" * 40)
    click.echo(f"Total memories: {len(memories)}")
    click.echo(f"Average confidence: {avg_confidence:.2f}")
    click.echo(f"Unique tags: {len(all_tags)}")
    click.echo()
    
    click.echo("By Category:")
    for cat, count in sorted(by_category.items()):
        click.echo(f"  {cat}: {count}")
    click.echo()
    
    click.echo("By Subject:")
    for subj, count in sorted(by_subject.items()):
        click.echo(f"  {subj}: {count}")
    
    if all_tags:
        click.echo()
        click.echo(f"Tags: {', '.join(sorted(all_tags))}")


@cli.command("export")
@click.option("--pretty", "-p", is_flag=True, help="Pretty-print JSON")
def export_memories(pretty: bool):
    """Export all memories as JSON."""
    index = load_index()
    
    if pretty:
        click.echo(json.dumps(index, indent=2, ensure_ascii=False))
    else:
        click.echo(json.dumps(index, ensure_ascii=False))


@cli.command("import")
@click.argument("file", type=click.Path(exists=True))
@click.option("--merge", "-m", is_flag=True, help="Merge with existing (skip duplicates)")
@click.option("--replace", "-r", is_flag=True, help="Replace all existing memories")
def import_memories(file: str, merge: bool, replace: bool):
    """
    Import memories from a JSON file.
    
    FILE: Path to JSON file
    """
    with open(file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Handle both full index format and array of memories
    if isinstance(data, dict) and "memories" in data:
        new_memories = data["memories"]
    elif isinstance(data, list):
        new_memories = data
    else:
        raise click.ClickException("Invalid format. Expected {memories: [...]} or [...]")
    
    # Validate all memories
    for mem in new_memories:
        errors = validate_memory(mem)
        if errors:
            raise click.ClickException(f"Invalid memory {mem.get('id', '?')}: {errors}")
    
    if replace:
        index = {"memories": new_memories, "version": "1.0"}
        save_index(index)
        click.echo(f"Replaced all memories. Imported {len(new_memories)} memories.")
    elif merge:
        index = load_index()
        existing_ids = {m["id"] for m in index["memories"]}
        
        added = 0
        skipped = 0
        for mem in new_memories:
            if mem["id"] in existing_ids:
                skipped += 1
            else:
                index["memories"].append(mem)
                added += 1
        
        save_index(index)
        click.echo(f"Merged: {added} added, {skipped} skipped (duplicates).")
    else:
        raise click.ClickException("Specify --merge or --replace")


@cli.command()
def clear():
    """Clear all memories (with confirmation)."""
    index = load_index()
    count = len(index.get("memories", []))
    
    if count == 0:
        click.echo("No memories to clear.")
        return
    
    click.echo(f"About to delete {count} memories.")
    if click.confirm("Are you sure?"):
        save_index({"memories": [], "version": "1.0"})
        click.echo(f"Cleared {count} memories.")
    else:
        click.echo("Cancelled.")


if __name__ == "__main__":
    cli()