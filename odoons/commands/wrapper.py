import os
import sys
import stat

from .command import Command, commands_registry
from odoons.utils.config import OPT_BIN_DIR, DEFAULT_OPTIONS
from odoons.utils import printing


class Wrapper(Command):
    def _generate_start_odoo(self):
        printing.info("Generating wrapper...")
        bin_dir = self._options.get(OPT_BIN_DIR, DEFAULT_OPTIONS[OPT_BIN_DIR])
        if not os.path.exists(bin_dir):
            os.makedirs(bin_dir, exist_ok=True)
        start_odoo_path = os.path.join(os.path.abspath(bin_dir), "start_odoo")
        config_path = commands_registry["config"]()._get_config_path(self._options)
        lines = [
            "#!{}".format(sys.executable),
            "import sys",
            "import os",
            "starter = \"{}/bin/odoo\"".format(sys.exec_prefix),
            "conf = \"{}\"".format(config_path),
            "arguments = ['-c', conf]",
            "for i, a in enumerate(arguments):",
            "    sys.argv.insert(i + 1, a)",

            "os.chdir(os.path.split(starter)[0])",
            "glob = globals()",
            "glob['__name__'] = '__main__'",
            "glob['__file__'] = starter",
            "sys.argv[0] = starter",
            "try:",
            "    if sys.version_info < (3, 0):",
            "        execfile(starter, globals())",
            "    else:",
            "        exec(open(starter).read(), globals())",
            "except SystemExit as exc:",
            "    raise exc",
        ]
        with open(start_odoo_path, "w") as f:
            f.write(os.linesep.join(lines))
        st = os.stat(start_odoo_path)
        os.chmod(start_odoo_path, st.st_mode | stat.S_IEXEC)

    def run(self, args):
        self.load_config(args.file)
        self._generate_start_odoo()
