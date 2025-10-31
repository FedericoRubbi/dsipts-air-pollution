# Install pyenv
Instructions for pyenv installation: https://github.com/pyenv/pyenv

# Install python 3.11.13 (required by DSIPTS)

pyenv install -v 3.11.13
pyenv local 3.11.13
python -m venv .venv
source .venv/bin/activate
python --version

# Install packages for notebook
pip install -r requirements.txt