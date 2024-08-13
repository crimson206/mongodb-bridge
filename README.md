**Template README.md**\
This file is from the [template repository](https://github.com/crimson206/template/blob/main/README.md).
Rewrite it for your own package.

## Python Package Setup

### Setup Base

To install required pip modules for `generate_toml.py`, run
``` bash
source scripts/setup_base.sh
```

### User Setup

- go to `generate_toml.py` file, and complete the setup in the `User Setup` session.

```python
options = Options(
    # Will you use the discussion session in your repo?
    discussion=False
)

# Define the general information of your package
kwargs = Kwargs(
    name_space="None",
    module_name="None",
    description="None",
)
```

If you wrote all the information, run
```
python generate_toml.py
```

#### Template

If you want to understand the generation process, check the `template` variable in `generate_toml.py`.

### Setup Env

#### Prerequisite

Finish [User Setup](#user-setup) first.
Of course, conda command must be available.

#### Setup Env

Run
``` bash
source scripts/setup_env.sh
```

steps
- create an conda environment named as your $MODULE_NAME
- activate the environment.
- install requirements.txt

#### Generate Private Env
Generate a private repository in this repo.
I recommend you to write all the unstructured codes in this repo.

``` bash
source scripts/generate_dev_repo.sh
```

It will ask you the name of your repo, and then, generate a repo named f'{your_repo_name}-dev'.

**Usage Tip**

If you wrote your codes in a wrong branch,
- backup the files to the dev repo
- remove changes in your main(not main branch) repo
- move to your correct branch
- place back the backup codes


## Workflows

I currently setup test and release workflows.

**Test**

If you make a PR with the patterns [ main, develop, 'release/*', 'feature/*' ],

It will perform your unittest in ["3.9", "3.10", "3.11"]

**Release**

required secret : PYPI_API_TOKEN

I usually make PRs only when I start release branches.
release workflow is not conducted automatically. If you think your branch is ready to be published, 

- go to https://github.com/{github_id}/{repo_name}/actions/workflows/release.yaml
- find the button, 'Run workflow'
- select the branch to publish. In my case, release/x.x.x
