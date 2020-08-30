# NUSummiteers Telegram Bot
Sign up for NUSummiteers where your elevation gained accumulates to reaching a mountain’s summit! [This Telegram bot](https://t.me/nusummiteers_bot) is the main point of contact with participants for them to submit their video/photo proof of their ascent, and send any inquiries to us. Telegram was chosen for its unlimited storage, 2GB file size limits, and mature bot API.

## Getting Started
This bot relies heavily on Telegram-Python-Bot library and is created within a Docker container for ease of installation and deployment. Due to time constraints, it was created using the polling approach, ie `while True`. The bot is then deployed on heroku, which is free and easy to use.

### Development
1. Install `docker` (https://docs.docker.com/get-docker/) and `docker-compose` (https://docs.docker.com/compose/install/).
1. In a terminal, run `docker-compose up`. This terminal window must not be closed while the program is running. You can use it to view outputs from `logging`.
1. To access the docker container directly, open another terminal window and run `docker exec -it bot bash`.
1. If you make any changes to `Dockerfile`, you have to rebuild the image to see your changes, by running `docker-compose build`. You can enter the container (previous step) and save the python dependencies by running `pip freeze > requirements.txt`.
1. To reload the bot after making changes (eg to `*.py` or `.env`), go to the terminal running the program and press `Ctrl+c` or `Cmd+c` twice. Then, run `docker-compose up` again. I'm open to suggestions for easy hot reload setup.

### Deployment
1. Install `heroku` CLI from https://devcenter.heroku.com/articles/heroku-cli
1. Create a heroku account. Then create an app to be linked to our container.
1. On a terminal, set `APP_NAME={YOUR_APP_NAME}`, then run `. ./deploy.sh`
1. Test if bot is deployed by giving `/start` command to https://t.me/nusummiteers_bot

## Coding Conventions
- Credentials *MUST* be stored in `config.env`. Access them via `os.getenv(NAME)`.
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
    - [ ] Create ability to PM using bot to specific person quickly.
- [x] *Submissions*
    - [x] Forward submissions to private Telegram channel, since Telegram API does not allow download of videos >20MB. If you are using Telegramm Desktop, it will automatically download files on your computer.
    - [ ] Rename forwarded files to `<Telegram Handler>:<Name>:<Time>`
- [x] *Enquiries*
    - [x] Forward enquiries to private Slack channel for ease of access (and notifications). Using POST request rather than bloating dependencies with Slack python libraries.
- [ ] *Updates*
    - [ ] Send scheduled updates on progress, FAQ, interesting facts.
