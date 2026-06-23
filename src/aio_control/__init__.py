"""uConsole AIO Control.

A keyboard-driven terminal control panel for the ClockworkPi uConsole and the
HackerGadgets "v2 AIO" (SDR / LoRa / GPS / USB-rail) all-in-one board.

The whole control surface is data-driven: categories, launchable apps and
on/off commands all live in an editable YAML config that the app scans at
start-up, so the command set can grow over time (including commands generated
by Claude Code) without touching the source.
"""

__version__ = "0.1.0"
