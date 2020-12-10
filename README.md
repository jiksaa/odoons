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
    # Adding OCA Web addons repositories
    oca-web:
      type: git
      path: vendor/oca/web
      url: git@github.com:OCA/web.git
      branch: 12.0

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

```
usage: Odoons [-h] [-f FILE] COMMAND

COMMAND:

init        Initialize Odoo and addons
install     Install or update python dependencies
update      Update Odoo and addons sources code 
addons      List additional addons
config      Generate Odoo configuration file with proper addons_path
reset       Delete additional addons

optional arguments:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  Path to odoons YAML file. Default: odoons.yml
```

## Basic Project Setup

The [example](example) directory contains a basic project template using Odoons. 
It contains:

- An Odoons YAML file
- An Odoo configuration file template
- A directory for local addons
