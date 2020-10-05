# NUSummiteers Telegram Bot
[This Telegram bot](https://t.me/nusummiteers_bot) was the main point of contact with participants for them to submit their video/photo proof of their ascent, and send any inquiries to us. Telegram was chosen for its unlimited storage, 2GB file size limits, and mature bot API.

## Getting Started
This bot relies heavily on Telegram-Python-Bot and `gspread` library. `gspread` was used as a database for graders to grade submissions. It is developed within a Docker container for ease of installation and deployment. Due to time constraints, it was created using the polling approach, ie `while True`. The bot is then deployed on heroku, which is free and easy to use.

### Development
1. You will need `client_secret.json` for Google service account and `.env`ironment variables. PM me or setup for yourself.
1. Install `docker` (https://docs.docker.com/get-docker/) and `docker-compose` (https://docs.docker.com/compose/install/).
1. Start a container instance on a new terminal with `docker-compose up -d`.
1. Run `docker exec -it bot bash` to enter the container, then `./run.sh` to run the bot.
1. To change overall state automata, edit `bot.py`.
1. To change state behaviour, edit `handler.py`.
1. To schedule announcements, edit `schedule.py`.
1. To save important event data or persistent data across restart, edit `db.py`. You can think of it as a Persistence Object --> View Object.
1. After making changes (eg to `*.py` or `.env`), go to the terminal running the container, and stop the bot by pressing `Ctrl+c` or `Cmd+c`. Then, run `./run.sh` again to run the bot.
1. If you make any changes to `Dockerfile` (eg python `requirements.txt`), you have to rebuild the image to see your changes, by running `docker-compose build`

### Deployment
1. Install `heroku` CLI from https://devcenter.heroku.com/articles/heroku-cli
1. Create a heroku account. Then create an app to be linked to our container.
1. On a terminal, set `APP_NAME={YOUR_APP_NAME}`, then run `. ./deploy.sh`
1. Test if bot is deployed by giving `/start` command to https://t.me/nusummiteers_bot

## Coding Conventions
- Credentials *MUST* be stored in `.env` which will be loaded in `docker-compose`. Access them via `os.getenv(NAME)`.
- `bot.py` is for a high-level state flow.
- `handler.py` is for states, ie stateless endpoints (eg `/start`).
- Don't stutter, eg exported functions `handler.StartHandler`
- Don't `print()`, use `logging.info()`
- `PascalCase` for exported functions
- `camelCase` for local functions
- `UPPER_CASE` for constants, eg states

## Features
- [x] Telegram Bot
    - [x] Working overall flow
    - [x] Create ability to PM using bot to specific person quickly.
    - [x] Add poll feature
    - [x] Add leaderboard
    - [x] Add progress
- [x] *Submissions*
    - [x] Forward submissions to private Telegram channel, since Telegram API does not allow download of videos >20MB. If you are using Telegramm Desktop, it will automatically download files on your computer.
    - [x] Append submissions to google sheets for points tabulation.
    - [x] Prevent unregistered users from submitting.
- [x] *Enquiries*
    - [x] Forward enquiries to private Slack channel for ease of access (and notifications). Using POST request rather than bloating dependencies with Slack python libraries.
- [x] *Updates*
    - [x] Send scheduled updates on progress, FAQ, interesting facts.
    - [x] Read schedules from `.yaml` so as to minimise repeated code.
