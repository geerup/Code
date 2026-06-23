"""Command-line entry point for uConsole AIO Control."""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .config import ConfigError, install_default_config, load_config, user_config_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aioctl",
        description="Keyboard-driven control panel for the uConsole + HackerGadgets "
        "v2 AIO (SDR / LoRa / GPS / USB rail).",
    )
    parser.add_argument(
        "-c",
        "--config",
        metavar="PATH",
        help="Path to a YAML config (overrides auto-discovery).",
    )
    parser.add_argument(
        "--init",
        action="store_true",
        help="Write the default config to the user config path and exit.",
    )
    parser.add_argument(
        "--config-path",
        action="store_true",
        help="Print the resolved user config path and exit.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate the config and exit without launching the UI.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"aioctl {__version__}",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.config_path:
        print(user_config_path())
        return 0

    if args.init:
        path = install_default_config()
        print(f"Default config written to: {path}")
        return 0

    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        return 2

    if args.check:
        total = sum(len(c.entries) for c in config.categories)
        print(
            f"OK: '{config.name}' - {len(config.categories)} categories, "
            f"{total} entries "
            f"(source: {config.source_path or 'built-in defaults'})"
        )
        return 0

    # Import here so --check / --init work without a working terminal.
    from .app import AIOControlApp

    AIOControlApp(config).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
