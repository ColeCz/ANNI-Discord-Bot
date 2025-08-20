# Weekly Report Software Suite

## Overview:
This repository contains the entire pipeline for interns to submit their weekly reports. This suite initializes a database, loads the frontend form for users to input their weekly report data, sends the data to the database with a Django backend, and scrapes the data with a Discord.py bot, which then periodically messages said data to managers.   
The future of this project is somewhat murky, we may end up seperating the `bot/` directory when we deploy the software. So for now, we are trying to keep the subdirectories modular, like having seperate .env files. This README also does not cover running the bot, as it's covered thoroughly in the README in the `bot/` directory and the backend and bot cannot be run together conventionally (from the same terminal window). Generally, we will not need both running at the same time. If you do, consider using tmux or your own approach. 

## Directories:
`./database/`   contains the initialization scripts to set up the PostgreSQL DB.  
`./webapp/`     contains the frontend and backend of the webpage that allows users to write to the DB.  
`./bot/`        contains the Discord.py bot that scrapes data from the DB and sends it to managers periodically.

## Setup and Requirements (UNIX):
1. Clone the repository with `git clone https://github.com/ColeCz/ANNI-Discord-Bot.git`
2. Change branch to the form site feature branch with `git checkout feature/add-form-app`
3. Create a Python virtual environment in the root directory with `python -m venv .venv`
4. Stay in the root directory, activate virtual environment with `. .venv/bin/activate`

5. Update advanced packaging tool 'apt' with `sudo apt update`
6. Download PostgreSQL 16.9 or later with `sudo apt install postgresql`

7. Navigate to the `ANNI-Discord-Bot/webapp/` directory and run `pip install -r requirements.txt`
8. Create a file named `.env` in the same `ANNI-Discord-Bot/webapp/` directory, ask your PM for the contents of this file
9. Run the run.sh script in the same `ANNI-Discord-Bot/webapp/` directory with `./run.sh`
You have now run the database and site. Note that the bot is not running, and will either need to be ran/tested seperately or using something like tmux if you need to test all features at once. To run the bot, see the README.md in the `bot/` repository.

## Installing PgAdmin:
PgAdmin is a graphical user interface for PostgreSQL databases. It allows you to see what you are doing with the database and is a great sanity check during database development. This is not a requirement, but is strongly recommended if you are working on the database or database related features. Here are the steps to set it up...
1. Install the PgAdmin desktop app from their site: https://www.pgadmin.org/download/
2. Open the PgAdmin desktop app
3. Right click the 'Servers' tab, select 'Register' tab and then finally the 'Server...' tab
4. In the new window that opened, under the 'General' tab, fill in the 'Name' field with the 'DB_NAME' value from the .env file you got for the `webapp/` directory
5. Under the 'Connection' tab in the same window as step 4, input the following...
   - Fill in the 'Host Name / Address' field with the 'DB_HOST' value from the .env
   - Fill in the 'Port' field with the 'DB_PORT' value from the .env
   - Fill in the 'Username' field with the 'DB_USER' value from the .env
   - Fill in the 'Password' field with the 'DB_PASS' value from the .env