# DMV Breach Bot

A Telegram bot that helps search Lebanese vehicle records using:
- License Plate Number (with or without letter)
- Phone Number
- Car Make / Type
- Full Name (Arabic or phonetic transliteration)

> This is an educational project. Data and usage should comply with all applicable laws.

---

## Features

- Search vehicle info by plate, phone, car, or name
- Phonetic name matching (Arabic-English transliteration supported)
- Pagination for result navigation
- Access code-based protection
- Admin command to view recent logs and authorized users

---

## Installation

1. Clone the repository:

```bash
git clone https://github.com/baassiri/DMV-breach.git
cd DMV-breach
## Create a virtual environment:

python -m venv venv_nef3a
.\venv_nef3a\Scripts\Activate.ps1

## Install dependencies:

pip install -r requirements.txt
