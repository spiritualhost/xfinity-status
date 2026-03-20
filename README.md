# Xfinity Status Monitor

A lightweight CLI tool that monitors Xfinity service status at a given address and alerts you to outages without manual checks. No API key required.

[![Python](https://img.shields.io/badge/python-3.10+-blue)](https://www.python.org/)
![Platform](https://img.shields.io/badge/platform-linux%20%7C%20windows%20%7C%20mac-lightgrey)
[![Playwright](https://img.shields.io/badge/playwright-automated-green)](https://playwright.dev/python/)


## Requirements

- Python 3.10+
- Git Bash (Windows) or any bash-compatible shell (Mac/Linux)

## Setup

1) Clone the repo

```bash
git clone https://github.com/spiritualhost/xfinity-status
cd xfinity_status/
```

2) Run the setup script to create a virtual environment and install dependencies

```bash
./setup.sh
```

3) Activate the venv and run the script

```bash
source venv/Scripts/activate
python xfinity_status.py
```

On first run you will be prompted to enter your service address. This is validated against the Xfinity portal and saved to `config.ini` for future runs.

## Usage

Run interactively:

```bash
python xfinity_status.py
```

Pipe output to a log file:

```bash
python xfinity_status.py > log.txt
```

Status is checked every 30 minutes by default. This can be changed by editing the `sleep` value in `config.ini`, which is measured in seconds.

## Notes

- `config.ini` is generated on first run and stores your service address and poll interval
- The browser runs headlessly and defaults to chromium
- Press `Ctrl+C` to exit cleanly