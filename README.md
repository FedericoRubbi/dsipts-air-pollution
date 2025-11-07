# Setup Guide

## Installing pyenv on Linux

Before you can install Python 3.11.13, you need to install pyenv, which allows you to manage multiple Python versions on your system.

### Step 1: Install Build Dependencies

First, install all the required build dependencies needed to compile Python from source:

```bash
sudo apt-get update && sudo apt-get install -y make build-essential libssl-dev zlib1g-dev \
libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev git
```

These packages include:
- **build-essential**: Essential compilation tools (gcc, make, etc.)
- **libssl-dev**: SSL/TLS support for Python
- **zlib1g-dev, libbz2-dev, liblzma-dev**: Compression libraries
- **libreadline-dev**: Interactive shell support
- **libsqlite3-dev**: SQLite database support
- **libffi-dev**: Foreign function interface library
- **libxml2-dev, libxmlsec1-dev**: XML processing libraries
- **tk-dev**: Tkinter GUI support
- **git, curl, wget**: Version control and download tools

### Step 2: Download and Install pyenv

Use the official pyenv installer script:

```bash
curl https://pyenv.run | bash
```

This will:
- Clone the pyenv repository to `~/.pyenv`
- Install useful plugins: pyenv-doctor, pyenv-update, pyenv-virtualenv

### Step 3: Configure Your Shell

Add pyenv initialization to your `~/.bashrc` file:

```bash
cat >> ~/.bashrc << 'EOF'

# Pyenv configuration
export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init - bash)"
eval "$(pyenv virtualenv-init -)"
EOF
```

### Step 4: Reload Your Shell

Apply the changes by reloading your shell:

```bash
exec bash
```

Alternatively, close and reopen your terminal.

### Step 5: Verify Installation

Check that pyenv is working correctly:

```bash
pyenv --version
# Should output: pyenv 2.6.11 (or newer)

pyenv commands
# Should list available commands
```

## Installing Python 3.11.13 (required by DSIPTS)

Once pyenv is installed, you can install the required Python version:

```bash
# Install Python 3.11.13
pyenv install -v 3.11.13

# Set it as the local version for this project
pyenv local 3.11.13

# Verify the Python version
python --version
# Should output: Python 3.11.13
```

## Setting Up the Virtual Environment

Create and activate a virtual environment for the project:

```bash
python -m venv .venv
source .venv/bin/activate
python --version
```

## Install Project Dependencies

First, update the submodules 

```bash
git submodule update --init --recursive
```

Then, install the required packages for the notebook:

```bash
pip install -r requirements.txt
```

## Installing DSIPTS in Developer Mode

If you need to develop or modify the DSIPTS framework, install it in editable mode:

```bash
# Install DSIPTS from the submodule in editable mode
pip install -e ./DSIPTS

# Verify installation
pip show dsipts
# The Location should point to the DSIPTS directory
```

## Useful pyenv Commands

```bash
# List all available Python versions
pyenv install --list

# List installed Python versions
pyenv versions

# Show current active version
pyenv version

# Set global Python version (system-wide)
pyenv global 3.11.13

# Set local Python version (current directory only)
pyenv local 3.11.13

# Uninstall a Python version
pyenv uninstall 3.11.13

# Update pyenv itself
pyenv update
```