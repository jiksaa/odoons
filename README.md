# Odoons

Odoons is a python command line tools that help setting up an Odoo project. It used a dedicated
YAML file describing the project configuration. Based on this YAML file, Odoons will provide the
following features: 

- Initialize Odoo and its python dependencies
- Initialize addons from various Git repositories.
- Update existing addons.
- Reset addons.
- Install Python requirements.
- Build Odoo configuration file.
- Migrate Odoo buildout file(s) to Odoons structure


## Installation

Install Odoons with the following command:

    pip install git+https://github.com/jiksaa/odoons

## Getting Started

A default project structure using Odoons should have an `odoons.yml` file with the following
content:

```yaml
odoons:
  
  # Odoo configuration section
  odoo:
    # Odoo version (git branch)
    version: 12.0

    # Path where Odoo should be cloned
    path: vendor/odoo

    # Optional Odoo repository URL
    url: https://github.com/odoo/odoo
    
    # Optional Odoo commit to freeze version to
    commit: 3ba8984ef0b3342baab2abd2b1ba774f1abd8e0a

    # Odoo configuration file options
    options:
      data_dir: data
      db_user: odoo
      db_password: odoo
      db_name: odoo
      # ...

  # Odoons options section
  options:
    # Install odoo as a command line
    install-odoo-command: true
    
    # Automatically install python dependencies
    apply-requirements: true

    # Odoo configuration file template
    config-template: odoo.cfg.template

  # Additionnal addons section
  addons:
    # Additional addons...
    oca-web:
      type: git
      path: vendor/oca/web
      url: git@github.com:OCA/web.git
      branch: 12.0
    
    # Additional addons (frozen to specific commit)
    oca-queue:
      type: git
      path: vendor/oca/queue
      url: git@github.com:OCA/queue.git
      commit: 3ba8984ef0b3342baab2abd2b1ba774f1abd8e0a

    # Adding local directory addons
    local:
      type: local
      path: src
```

Run the following command to initialize your addons defined in the YAML file

    odoons init

Odoons will clone Odoo and addons repositories and install python dependencies.
As usual, it is recommended to setup the project inside a virtual environment.

## Odoons Usage

```bash
usage: Odoons [-h] [-f FILE] COMMAND

COMMAND:

init        Initialize Odoo, addons and configuration file
install     Install or update python dependencies
migrate     Migrate buildout file(s) to Odoons
update      Update Odoo and addons sources code 
addons      List additional addons
config      Generate Odoo configuration file with proper addons_path
reset       Delete additional addons

optional arguments:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  Path to odoons YAML file. Default: odoons.yml
```

### `init` command

Initialize Odoo, addons and configuration file.
This command is roughly equivalent to running both `install` and `config` command.

```bash
usage: Odoons init [-h] [--no-requirements] [--skip-config]

optional arguments:
  -h, --help         show this help message and exit
  --no-requirements  Ignore PIP requirements.txt installation from cloned repositories
  --skip-config      Skip Odoo configuration file generation
```

### `install` command

Install Python dependencies inside current environment. Odoons will search for `requirements.txt` file in addons
directories and install them through `pip`

### `migrate` command

```bash
odoons [-h] [-f FILE] migrate [-h] [-b BUILDOUT_FILE]
```

Considering an existing project using Odoo buildout recipe with potentially multiple buildout files such as
- `buildout.cfg.template`
- `buildout.cfg.dev` extending the above
- ...
- `buildout.cfg` extending the above

Running the following Odoons command will generate an odoons YAML configuration file from the project structure
defined in buildout files
```bash
odoons -f odoons.yml migrate --buildout-file buildout.cfg
```

### `update` command

Update addons repositories and their python dependencies.

### `addons` command

List addons path as expected in an Odoo configuration file `addons_path` entry.

### `config` command

Generate an Odoo configuration file from the configured template and options specified in the odoons YAML file

### `reset` command

Delete all remote repository directory


## Basic Project Setup

The [example/project_structure](example) directory contains a basic project template using Odoons. 
It contains:

- An Odoons YAML file
- An Odoo configuration file template
- A directory for local addons

```bash
virtualenv -p python3 venv
venv/bin/pip install git+https://github.com/jiksaa/odoons
venv/bin/odoons init
```