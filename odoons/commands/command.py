"""
This file defines the base Command class handling the base
"""
from odoons.utils.config import load_odoons_config, DEFAULT_OPTIONS


commands_registry = {}


class CommandType(type):
    def __init__(cls, name, bases, attrs):
        super(CommandType, cls).__init__(name, bases, attrs)
        name = getattr(cls, name, cls.__name__.lower())
        cls.name = name
        if name not in ['command', 'basecommand']:
            commands_registry[name] = cls


BaseCommand = CommandType('Command', (object,), {
    "run": lambda self, args: None,
    "configure_parser": lambda self, parser: None,
    "_args": None,
    "_parser": None,
    "_options": dict(DEFAULT_OPTIONS),
    "_odoo": None,
    "_addons": None,
})


class Command(BaseCommand):
    def load_config(self, path):
        parsed_config = load_odoons_config(path)
        self._odoo = parsed_config["odoo"]
        self._addons = parsed_config.get("addons", [])
        self._options.update(parsed_config.get("options", {}))

