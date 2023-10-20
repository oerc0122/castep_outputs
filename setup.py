"""
Setuptools setup script for castep_outputs

To install locally:

    python setup.py install

"""

import sys
from setuptools import setup, find_packages

# Check for valid Python version
if sys.version_info[:2] < (3, 8):
    print(f"castep_outputs requires Python 3.8. Python {'.'.join(sys.version_info[:2])} detected")

packages_test = find_packages()

with open("README.rst", "r", encoding="utf-8") as readme:
    README = readme.read()

setup(
    name="castep_outputs",
    version="0.1.6",
    license='BSD3',
    license_files=('LICENSE'),
    description='A package for extracting information from castep outputs',
    long_description=README,
    packages=find_packages(),
    author="Jacob Wilkins",
    author_email="jacob.wilkins@stfc.ac.uk",
    url="https://github.com/oerc0122/castep_outputs",
    download_url="https://github.com/oerc0122/castep_outputs",
    python_requires='>=3.8',
    install_requires=[],
    extras_require={'ruamel': 'ruamel.yaml>=0.17.22',
                    'yaml': 'PyYAML>=3.13',
                    'docs': ['jupyter-book>=0.13.1', 'sphinx-book-theme>=0.3.3', 'sphinx-argparse>=0.4.0']},
    entry_points={"console_scripts": ['castep_outputs = castep_outputs.castep_outputs_main:main']},
    include_package_data=True
)
