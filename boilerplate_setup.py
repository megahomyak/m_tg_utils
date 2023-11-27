import os
import stat as stat_module

_boilerplate_list = []

def _boilerplate(file_name, file_contents, is_executable=False):
    _boilerplate_list.append((file_name, file_contents.strip(), is_executable))

_boilerplate("build", """
python -m m_tg_utils generate_config && mypy . --ignore-missing-imports
""", is_executable=True)

_boilerplate("run", """
#!/bin/bash
./build && python bot.py
""", is_executable=True)

_boilerplate("deploy", """
#!/usr/bin/bash

./build && ssh {server} << EOF
    cd {dir}
    git pull
    ./build
    poetry install --no-root --sync
    systemctl restart {dir}
EOF
""", is_executable=True)

_boilerplate("pyproject.toml", """
[tool.poetry]
name = "{dir}"
version = "0.1.0"
description = ""
authors = ["megahomyak <g.megahomyak@gmail.com>"]

[tool.poetry.dependencies]
python = "^3.8"

[tool.poetry.dev-dependencies]
mypy = "^1.7.1"

[build-system]
requires = ["poetry-core>=1.0.0"]
build-backend = "poetry.core.masonry.api"
""")

_boilerplate(".gitignore", """
**/__pycache__
config.cson
""")

def generate_and_place(directory_name, server_name):
    os.mkdir(directory_name)
    for file_name, file_contents, is_executable in _boilerplate_list:
        file_contents = file_contents.format(
            directory_name=directory_name,
            server_name=server_name
        )
        file_path = os.path.join(directory_name, file_name)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(file_contents)
        if is_executable:
            stat = os.stat(file_path)
            os.chmod(file_path, stat.st_mode | stat_module.S_IEXEC)
