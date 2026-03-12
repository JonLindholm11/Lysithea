# setup.py
# Installs the global `lysithea` CLI command.
#
# Usage:
#   pip install -e .          (from repo root — editable install)
#   pip install .             (standard install)
#
# After install, `lysithea --fix "prompt" --path ./project` works from anywhere.

from setuptools import setup, find_packages

setup(
    name='lysithea',
    version='0.3.0',
    description='Lysithea — AI-powered code scaffolding and audit platform',
    author='Jon Lindholm',
    license='MIT',
    packages=find_packages(where='Lysithea'),
    package_dir={'': 'Lysithea'},
    python_requires='>=3.8',
    install_requires=[
        'ollama',
    ],
    entry_points={
        'console_scripts': [
            # `lysithea` command maps to cli.py:main()
            # Works from any directory after: pip install -e .
            'lysithea = cli:main',
        ],
    },
)