# Odoons

Odoo addons management tool

## Features

- Init addons from Git repositories.
- Update existing addons.
- Reset addons.
- Install Python requirements.
- Build addons_path for Odoo instance.


## Install

    pip install odoons
    
## Usage

First define your Odoo addons repositories in a `addons.yml` file on the root of your project.
Here is a example of the `addons.yml` content:

    repositories:
    
      # Odoo community sources
      odoo:
        path: vendor/odoo
        url: git@github.com:odoo/odoo.git   # SSH
        branch: 12.0
        
      # OCA Web Addons sources
      oca-web:
        path: vendor/oca/web
        url: https://github.com/OCA/web     # HTTPS
        commit: 

Run the following command to initialize your addons defined in the YAML file

    odoons init
