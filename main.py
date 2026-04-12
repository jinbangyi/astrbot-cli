"""Main entry point for AstrBot CLI."""

import tyro

from src.quick_start import main as quick_start_main


def main() -> None:
    """AstrBot CLI tools."""
    tyro.cli(quick_start_main)


if __name__ == "__main__":
    main()
