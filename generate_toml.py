# region Pre-Defined

import os
from pydantic import BaseModel
from crimson.templator import format_insert, format_indent, format_insert_loop
from typing import List

topics_t = r""""\\[topic\\]",
"""

dependencies_t = r""""\\[dependency\\]",
"""

template = r"""[build-system]
requires = ["setuptools>=61.0.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "\[name_space\]-\[module_name\]"
version = "\[version\]"
description = "\[description\]"
readme = "README.md"
authors = [
  { name="\[name\]", email="\[email\]" },
]

classifiers = [
    "Development Status :: Pre-Alpha",

    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",

    "Intended Audience :: Developers",

    \{topics_f\}
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",

    "Typing :: Typed",

]
dependencies = [
    \{dependencies_f\}
]
requires-python = ">=3.9"

[project.urls]
"Homepage" = "https://github.com/\[github_id\]/\[module_name\]"
"Bug Tracker" = "https://github.com/\[github_id\]/\[module_name\]/issues"
"""


class Kwargs(BaseModel):
    name: str = "Sisung Kim"
    email: str = "sisung.kim1@gmail.com"
    github_id: str = "crimson206"
    version: str
    name_space: str
    module_name: str
    description: str
    topics: List[str]
    dependencies: List[str]


class Options(BaseModel):
    discussion: bool = False


def add_options(template: str, options: Options) -> str:

    if options.discussion:
        discussion_block = r'''"Discussion" = "https://github.com/\[github_id\]/\[module_name\]/discussions"'''
        template += discussion_block

    return template


# endregion

# ******************************************************
# region Utils


def create_skeleton(name_space: str, module_name: str):
    module_name = module_name.replace("-", "_")
    os.makedirs(f"src/{name_space}/{module_name}", exist_ok=True)
    with open(f"src/{name_space}/{module_name}/__init__.py", "w") as f:
        f.write("# Init file for the module")


setup_env_template = r"""\[bin_bash\]

read -p "Please enter the Python version you want to use (e.g., 3.9): " PYTHON_VERSION

conda create --name \[module_name\] python=$PYTHON_VERSION -y

conda activate \[module_name\]

pip install -r requirements.txt
pip install -r requirements_test.txt
pip install -r requirements_dev.txt

"""


def generate_setup_env_script(module_name, setup_env_template):
    with open("scripts/setup_env.sh", "w") as file:
        script = format_insert(
            setup_env_template, module_name=module_name, bin_bash="# !bin/bash"
        )
        file.write(script)

    print(
        f"Now, you can access the module name {module_name} in your terminal by $MODULE_NAME"
    )
    print("To generate an conda env for your new module, run following command.")
    print("source scripts/setup_env.sh")


def generate_toml(pyproject_body):
    with open("pyproject.toml", "w") as file:
        file.write(pyproject_body)


def empty_readme():
    with open("README.md", "w") as file:
        file.write("Not valid yet.")


def generate_requirements(dependencies_f: str):
    dependencies_f = dependencies_f.replace('"', "").replace(',', "")
    with open("requirements.txt", "w") as file:
        file.write(dependencies_f)


# endregion

# ******************************************************
# region User Setup


options = Options(
    # Will you use the discussion session in your repo?
    discussion=False
)

dependencies = [
    "crimson-intelli-type==0.4.0"
]


# Define the general information of your package
kwargs = Kwargs(
    version="0.1.0",
    name_space="crimson",
    module_name="package-name",
    description="Your package description.",
    # https://pypi.org/classifiers/
    topics=["Topic :: Software Development :: Libraries :: Python Modules"],
    dependencies=dependencies,
)


kwargs_skeleton = kwargs.model_copy()
kwargs_skeleton.name_space = kwargs_skeleton.name_space.replace("-", "/")

# endregion

# ******************************************************
# region Execution

template: str = add_options(template, options=options)

pyproject_body: str = format_insert(template, **kwargs.model_dump())

topics_f: str = format_insert_loop(topics_t, kwargs={"topic": kwargs.topics})
dependencies_f: str = format_insert_loop(
    dependencies_t, kwargs={"dependency": kwargs.dependencies}
)

pyproject_body: str = format_indent(
    pyproject_body,
    topics_f=topics_f,
    dependencies_f=dependencies_f,
)


generate_toml(pyproject_body=pyproject_body)


create_skeleton(
    name_space=kwargs_skeleton.name_space, module_name=kwargs_skeleton.module_name
)

generate_setup_env_script(
    module_name=kwargs.module_name, setup_env_template=setup_env_template
)

generate_requirements(dependencies_f)

# endregion
