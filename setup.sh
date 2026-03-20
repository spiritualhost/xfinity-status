#!/bin/bash
echo "Setting up environment for script."
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
playwright install chromium