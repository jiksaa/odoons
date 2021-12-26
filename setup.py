import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="odoons-jiksaa",
    version="0.0.5",
    author="Jiksaa <Jonathan Beersaerts>",
    description="Odoo addons management tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jiksaa/odoons",
    packages=setuptools.find_packages(),
    classifiers=["Programming Language :: Python :: 3"],
    python_requires=">=3.6",
    install_requires=["ruamel.yaml>=0.15.1"],
    entry_points={"console_scripts": ["odoons = odoons.core:main"]},
)
