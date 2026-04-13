"""Persona management CLI commands for AstrBot."""

import json
from dataclasses import dataclass
from typing import Annotated

import tyro

from .personas_utils import (
    list_personas,
    get_persona,
    create_persona,
    update_persona,
    delete_persona,
)


@dataclass
class List:
    """List all personas.

    Show all configured personas with their system prompts.
    """

    verbose: bool = False  # Show full system prompt

    def run(self) -> None:
        """Execute the list command."""
        personas = list_personas()

        if personas:
            print("\nConfigured Personas:")
            print("-" * 80)
            print(f"{'ID':<20} {'System Prompt':<50}")
            print("-" * 80)

            for persona in personas:
                prompt = persona.get("system_prompt", "")
                if not self.verbose and len(prompt) > 48:
                    prompt = prompt[:45] + "..."
                print(f"{persona.get('persona_id', ''):<20} {prompt}")
        else:
            print("No personas configured.")


@dataclass
class Create:
    """Create a new persona.

    Create a persona with a system prompt and optional settings.
    """

    id: Annotated[str, tyro.conf.Positional]  # Persona ID
    prompt: Annotated[str, tyro.conf.Positional]  # System prompt
    begin_dialogs: str | None = None  # JSON array of starter dialogs
    tools: str | None = None  # JSON array of tool names (null for all)
    skills: str | None = None  # JSON array of skill names (null for all)
    error_message: str = ""  # Custom error message

    def run(self) -> None:
        """Execute the create command."""
        try:
            begin_dialogs_list = json.loads(self.begin_dialogs) if self.begin_dialogs else []
            tools_list = json.loads(self.tools) if self.tools else None
            skills_list = json.loads(self.skills) if self.skills else None

            persona = create_persona(
                persona_id=self.id,
                system_prompt=self.prompt,
                begin_dialogs=begin_dialogs_list,
                tools=tools_list,
                skills=skills_list,
                custom_error_message=self.error_message,
            )
            print(f"\nPersona '{persona['persona_id']}' created successfully!")
            print(f"  System prompt: {persona['system_prompt'][:50]}...")
        except ValueError as e:
            print(f"Error: {e}")
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON: {e}")


@dataclass
class Edit:
    """Edit a persona.

    Modify persona settings.
    """

    id: Annotated[str, tyro.conf.Positional]  # Persona ID
    prompt: str | None = None  # New system prompt
    begin_dialogs: str | None = None  # JSON array of starter dialogs
    tools: str | None = None  # JSON array of tool names
    skills: str | None = None  # JSON array of skill names
    error_message: str | None = None  # Custom error message

    def run(self) -> None:
        """Execute the edit command."""
        try:
            updates = {}

            if self.prompt:
                updates["system_prompt"] = self.prompt

            if self.begin_dialogs:
                updates["begin_dialogs"] = json.loads(self.begin_dialogs)

            if self.tools:
                updates["tools"] = json.loads(self.tools)

            if self.skills:
                updates["skills"] = json.loads(self.skills)

            if self.error_message is not None:
                updates["custom_error_message"] = self.error_message

            if not updates:
                print("No changes specified. Use --prompt, --begin-dialogs, --tools, --skills, or --error-message")
                return

            persona = update_persona(self.id, updates)
            print(f"Persona '{self.id}' updated successfully!")

        except ValueError as e:
            print(f"Error: {e}")
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON: {e}")


@dataclass
class Delete:
    """Delete a persona.

    Remove a persona by its ID.
    """

    id: Annotated[str, tyro.conf.Positional]  # Persona ID to delete

    def run(self) -> None:
        """Execute the delete command."""
        try:
            delete_persona(self.id)
            print(f"Persona '{self.id}' has been deleted")
        except ValueError as e:
            print(f"Error: {e}")


@dataclass
class Show:
    """Show persona details.

    Display full information about a persona.
    """

    id: Annotated[str, tyro.conf.Positional]  # Persona ID

    def run(self) -> None:
        """Execute the show command."""
        persona = get_persona(self.id)

        if persona is None:
            print(f"Error: Persona '{self.id}' not found")
            return

        print(f"\n{'=' * 50}")
        print(f"Persona: {persona['persona_id']}")
        print(f"{'=' * 50}")
        print(f"\nSystem Prompt:")
        print(f"  {persona['system_prompt']}")

        begin_dialogs = persona.get("begin_dialogs", [])
        if begin_dialogs:
            print(f"\nBegin Dialogs:")
            for i, dialog in enumerate(begin_dialogs, 1):
                print(f"  {i}. {dialog}")

        tools = persona.get("tools")
        if tools is not None:
            print(f"\nTools: {', '.join(tools) if tools else 'None'}")
        else:
            print(f"\nTools: All (default)")

        skills = persona.get("skills")
        if skills is not None:
            print(f"\nSkills: {', '.join(skills) if skills else 'None'}")
        else:
            print(f"\nSkills: All (default)")

        if persona.get("custom_error_message"):
            print(f"\nCustom Error Message: {persona['custom_error_message']}")
