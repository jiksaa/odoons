import os
from configparser import ConfigParser, ExtendedInterpolation

from ruamel.yaml import YAML

ADDONS_REQ_INSTALL_CONFIG = "install-requirements"

OPT_APPLY_REQS = "apply-requirements"
OPT_INSTALL_ODOO = "install-odoo-command"
OPT_CONF_TEMPLATE = "config-template"
OPT_CONF_DIR = "config-directory"
OPT_BIN_DIR = "bin-directory"

DEFAULT_OPTIONS = {
    OPT_APPLY_REQS: True,
    OPT_INSTALL_ODOO: True,
    OPT_CONF_TEMPLATE: "odoo.cfg.template",
    OPT_CONF_DIR: "etc",
    OPT_BIN_DIR: "bin",
}


def load_odoons_config(path):
    yaml = YAML(typ="safe")
    with open(path, "r") as file:
        odoons_file = yaml.load(file)
    if "odoons" not in odoons_file:
        raise Exception("missing odoons section in {}".format(path))
    return {
        'odoo': odoons_file["odoons"]["odoo"],
        "options": odoons_file["odoons"].get("options", {}),
        "addons": odoons_file["odoons"].get("addons", []),
    }


def get_config_parser():
    return ConfigParser(interpolation=ExtendedInterpolation(), strict=False)


def get_git_addons_path(conf):
    """
    Function computing addons path according to the given addons configuration dict()

    `conf` dict is expecting to follow the addons configuration entries structure

    This method mainly handle the standalone option which allows to use Git repository
    containing a standalone module.


    :param conf: addons configuration dict()
    :return: string representation of addons path
    """
    abspath = os.path.abspath(conf["path"])
    if "standalone" in conf and conf["standalone"]:
        abspath = os.path.abspath(os.path.join(conf["path"], conf["standalone"]))
    return abspath
