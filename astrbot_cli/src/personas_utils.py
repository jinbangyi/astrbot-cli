"""Persona management utilities for AstrBot CLI."""

import json
import sqlite3
from pathlib import Path
from typing import Any

from .path_config import get_astrbot_root

# Default persona
DEFAULT_PERSONA = {
    "persona_id": "default",
    "system_prompt": "You are a helpful and friendly assistant.",
    "begin_dialogs": [],
    "tools": None,  # None means all tools
    "skills": None,  # None means all skills
    "custom_error_message": "",
}


def get_database_path() -> Path:
    """Get the AstrBot SQLite database path."""
    astrbot_root = get_astrbot_root()
    if astrbot_root:
        return astrbot_root / "data" / "data_v4.db"
    return Path.cwd() / "data" / "data_v4.db"


def get_connection() -> sqlite3.Connection:
    """Get a database connection.

    Returns:
        sqlite3.Connection: Database connection

    """
    db_path = get_database_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_database() -> None:
    """Initialize the personas table if it doesn't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS personas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            persona_id TEXT UNIQUE NOT NULL,
            system_prompt TEXT NOT NULL,
            begin_dialogs TEXT DEFAULT '[]',
            tools TEXT,
            skills TEXT,
            custom_error_message TEXT DEFAULT '',
            folder_id TEXT,
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Check if default persona exists
    cursor.execute("SELECT COUNT(*) FROM personas WHERE persona_id = ?", ("default",))
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            """
            INSERT INTO personas (persona_id, system_prompt, begin_dialogs, tools, skills, custom_error_message)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                DEFAULT_PERSONA["persona_id"],
                DEFAULT_PERSONA["system_prompt"],
                json.dumps(DEFAULT_PERSONA["begin_dialogs"]),
                json.dumps(DEFAULT_PERSONA["tools"]) if DEFAULT_PERSONA["tools"] else None,
                json.dumps(DEFAULT_PERSONA["skills"]) if DEFAULT_PERSONA["skills"] else None,
                DEFAULT_PERSONA["custom_error_message"],
            ),
        )

    conn.commit()
    conn.close()


def list_personas() -> list[dict]:
    """List all personas.

    Returns:
        List of persona dictionaries

    """
    init_database()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT persona_id, system_prompt, begin_dialogs, tools, skills, custom_error_message, folder_id, sort_order
        FROM personas
        ORDER BY sort_order, persona_id
    """
    )

    personas = []
    for row in cursor.fetchall():
        personas.append({
            "persona_id": row["persona_id"],
            "system_prompt": row["system_prompt"],
            "begin_dialogs": json.loads(row["begin_dialogs"]) if row["begin_dialogs"] else [],
            "tools": json.loads(row["tools"]) if row["tools"] else None,
            "skills": json.loads(row["skills"]) if row["skills"] else None,
            "custom_error_message": row["custom_error_message"] or "",
            "folder_id": row["folder_id"],
            "sort_order": row["sort_order"],
        })

    conn.close()
    return personas


def get_persona(persona_id: str) -> dict | None:
    """Get a persona by ID.

    Args:
        persona_id: Persona ID

    Returns:
        Persona dictionary or None if not found

    """
    init_database()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT persona_id, system_prompt, begin_dialogs, tools, skills, custom_error_message, folder_id, sort_order
        FROM personas
        WHERE persona_id = ?
    """,
        (persona_id,),
    )

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return {
        "persona_id": row["persona_id"],
        "system_prompt": row["system_prompt"],
        "begin_dialogs": json.loads(row["begin_dialogs"]) if row["begin_dialogs"] else [],
        "tools": json.loads(row["tools"]) if row["tools"] else None,
        "skills": json.loads(row["skills"]) if row["skills"] else None,
        "custom_error_message": row["custom_error_message"] or "",
        "folder_id": row["folder_id"],
        "sort_order": row["sort_order"],
    }


def create_persona(
    persona_id: str,
    system_prompt: str,
    begin_dialogs: list[str] | None = None,
    tools: list[str] | None = None,
    skills: list[str] | None = None,
    custom_error_message: str = "",
) -> dict:
    """Create a new persona.

    Args:
        persona_id: Unique persona ID
        system_prompt: System prompt text
        begin_dialogs: List of starter dialog entries
        tools: List of tool names (None for all tools)
        skills: List of skill names (None for all skills)
        custom_error_message: Custom error message

    Returns:
        The created persona

    Raises:
        ValueError: If persona ID already exists

    """
    init_database()
    conn = get_connection()
    cursor = conn.cursor()

    # Check if persona exists
    cursor.execute("SELECT COUNT(*) FROM personas WHERE persona_id = ?", (persona_id,))
    if cursor.fetchone()[0] > 0:
        conn.close()
        raise ValueError(f"Persona '{persona_id}' already exists")

    # Get max sort_order
    cursor.execute("SELECT COALESCE(MAX(sort_order), 0) FROM personas")
    sort_order = cursor.fetchone()[0] + 1

    cursor.execute(
        """
        INSERT INTO personas (persona_id, system_prompt, begin_dialogs, tools, skills, custom_error_message, sort_order)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (
            persona_id,
            system_prompt,
            json.dumps(begin_dialogs or []),
            json.dumps(tools) if tools else None,
            json.dumps(skills) if skills else None,
            custom_error_message,
            sort_order,
        ),
    )

    conn.commit()
    conn.close()

    return get_persona(persona_id)


def update_persona(persona_id: str, updates: dict) -> dict:
    """Update a persona.

    Args:
        persona_id: Persona ID
        updates: Dictionary of fields to update

    Returns:
        Updated persona

    Raises:
        ValueError: If persona not found

    """
    init_database()
    conn = get_connection()
    cursor = conn.cursor()

    # Check if persona exists
    cursor.execute("SELECT COUNT(*) FROM personas WHERE persona_id = ?", (persona_id,))
    if cursor.fetchone()[0] == 0:
        conn.close()
        raise ValueError(f"Persona '{persona_id}' not found")

    # Build update query
    valid_fields = ["system_prompt", "begin_dialogs", "tools", "skills", "custom_error_message", "folder_id", "sort_order"]
    set_clauses = []
    values = []

    for field, value in updates.items():
        if field in valid_fields:
            if field in ["begin_dialogs", "tools", "skills"]:
                value = json.dumps(value) if value is not None else None
            set_clauses.append(f"{field} = ?")
            values.append(value)

    if set_clauses:
        values.append(persona_id)
        cursor.execute(
            f"""
            UPDATE personas
            SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP
            WHERE persona_id = ?
        """,
            values,
        )
        conn.commit()

    conn.close()
    return get_persona(persona_id)


def delete_persona(persona_id: str) -> None:
    """Delete a persona.

    Args:
        persona_id: Persona ID

    Raises:
        ValueError: If persona not found or is 'default'

    """
    if persona_id == "default":
        raise ValueError("Cannot delete the default persona")

    init_database()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM personas WHERE persona_id = ?", (persona_id,))
    if cursor.fetchone()[0] == 0:
        conn.close()
        raise ValueError(f"Persona '{persona_id}' not found")

    cursor.execute("DELETE FROM personas WHERE persona_id = ?", (persona_id,))
    conn.commit()
    conn.close()
