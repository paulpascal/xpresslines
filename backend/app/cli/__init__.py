"""Command-line tasks: `flask --app app seed`, `flask --app app check-seats`."""

from flask import Flask

from .checks import check_seats_command
from .seed import seed_command


def register_commands(app: Flask) -> None:
    app.cli.add_command(seed_command)
    app.cli.add_command(check_seats_command)
