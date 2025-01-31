#!/bin/bash

# Project directory (you can adjust this if needed)
PROJECT_DIR=$(pwd)  # Current directory

# Virtual environment name
VENV_NAME=".venv"

# Virtual environment path
VENV_PATH="$PROJECT_DIR/$VENV_NAME"

# Git repository URL
REPO_URL="https://github.com/apireno/surrealDB_Embedding_Model.git"

# Package name (used for pip install)
PACKAGE_NAME="surrealDB_embedding_model"  # Or the correct name from the repo

# Activate the virtual environment (FIXED - using full path)
echo "Activating virtual environment..."
if ( ! -d "$VENV_PATH" ); then  
  echo "Creating virtual environment..."
  python3 -m venv "$VENV_PATH" || { echo "Error creating virtual environment. Make sure venv is installed."; exit 1; }
else
  echo "Virtual environment already exists."
fi



# Activate the virtual environment
echo "Activating virtual environment..."
source "$VENV_PATH/bin/activate" || { echo "Error activating virtual environment."; exit 1; }

echo "Installing requirements..."
pip install -r requirements.txt

# Install the Git repo as a dependency in editable mode
echo "Installing $REPO_URL in editable mode..."


# Method 1 (using pip directly with git URL):  This is generally preferred.
pip install -e "git+$REPO_URL#egg=$PACKAGE_NAME" || { echo "Error installing Git repo. Check the URL and package name."; exit 1; }

# Method 2 (cloning, then installing locally):  Use this if Method 1 has issues.
# rm -rf "$PACKAGE_NAME" # Remove previous clone if it exists
# git clone "$REPO_URL" || { echo "Error cloning repository."; exit 1; }
# pip install -e "$PROJECT_DIR/$PACKAGE_NAME" || { echo "Error installing package."; exit 1; }

# Install other dependencies (if any)
echo "Installing other dependencies (from requirements.txt)..."
pip install -r requirements.txt || { echo "requirements.txt not found, skipping."; } # Don't exit on missing requirements

# Open VS Code (optional)
#echo "Opening VS Code..."
#code. &  # The & runs VS Code in the background

echo "Setup complete!"