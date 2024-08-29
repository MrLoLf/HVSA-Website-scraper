#!/bin/bash
cd /home/server/HVSA-Website-scraper
/usr/bin/python3 main.py
if [ ! -d ".venv" ]; then
    # Create a virtual environment
    /usr/bin/python3 -m venv .venv
fi

# Activate the virtual environment
source .venv/bin/activate

# Install the requirements
pip install -r requirements.txt

# Run the Python script
python main.py

# Deactivate the virtual environment
deactivate
