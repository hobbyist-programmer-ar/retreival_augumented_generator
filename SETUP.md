# Setting up this project

## Setup for a Virtual Environment
* Execute the below mentioned command to create a Virtual environment.
* This Virtual Environment will be used to install all of the required python packages
```bash
python3 -m venv .ragvenv ## Creates the venv in the folder mentioned in the second argument
source .ragvenv/bin/activate ## Activate the ragvenv that we just created
which python ## Checks if the venv is activated
## O/P for the command will be the ./.ragvenv/bin/python folder.
```

## Prepping th PIP
* Make sure you are using the latest version of pip to install all the python libraries
```bash
python3 -m pip install --upgrade pip ## Upgrades the PIP version
python3 -m pip --version ## Check ths installed version of PIP
## O/P pip 25.1.1 from ./.ragvenv/lib/python3.13/site-packages/pip
```
