from .command import Command, commands_registry

from odoons.utils import printing
from odoons.utils.config import OPT_APPLY_REQS

DEFAULT_ODOO_URL = "https://github.com/odoo/odoo"


class Init(Command):
    def configure_parser(self, parser):
        parser.add_argument(
            "--no-requirements",
            action="store_true",
            help="Ignore PIP requirements.txt installation from cloned repositories",
        )
        parser.add_argument(
            "--skip-config",
            action="store_true",
            help="Skip Odoo configuration file generation",
        )

    def run(self, args):
        """
        Action method responsible of the ACTION_INIT sub command

        :return: None
        """
        printing.info("Initializing project...")
        self.load_config(args.file)

        apply_requirements = (
            OPT_APPLY_REQS in self._options
            and self._options[OPT_APPLY_REQS]
            and not args.no_requirements
        )
        generate_config = not args.skip_config

        commands_registry["pull"]().run(args)
        if apply_requirements:
            commands_registry["install"]().run(args)
        if generate_config:
            commands_registry["config"]().run(args)

        commands_registry["wrapper"]().run(args)
