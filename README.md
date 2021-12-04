# NUSummiteers Telegram Bot
[This Telegram bot](https://t.me/nusummiteers_bot) was the main point of contact with participants for them to submit their video/photo proof of their ascent, and send any inquiries to us. Telegram was chosen for its unlimited storage, 2GB file size limits, and mature bot API.

This bot relies on Telegram-Python-Bot and `gspread` library. `gspread` was used as a database for graders to grade submissions. It is developed within a Docker container for ease of installation and deployment. Due to time constraints, it was created using the polling approach, ie `while True`. The bot is then deployed on heroku, which is free and easy to use.

## Getting Started
1. `.env` file
```dotenv
SHEET_URL=          # database for user ID, submissions, leaderboard, ... rows/cols hardcoded and should be changed. MUST BE non-xlsx
BOT_TOKEN=          # get from botfather
                    # Find the channel/grp ID with https://stackoverflow.com/questions/33858927/how-to-obtain-the-chat-id-of-a-private-telegram-channel
ANNOUNCE_CHANNEL=   # ^ for announcements to IDs saved in sheet
SUBMISSION_CHANNEL= # ^ for forwarded submissions to channel
ASK_GROUP=          # ^ for forwarded questions to group
TEST=true           # true = announce to self, false = announce to all

# App
TZ=Asia/Singapore
DEBUGGER_ID=                # announce to self
ANNOUNCE_PREFIX=Announce:   # used in ANNOUNCE_CHANNEL to prevent accidental broadcasts
START_TIMESTAMP=1638547200  # event start
END_TIMESTAMP=1639065600    # event end
```

2. `client_secret.json` file - follow https://docs.gspread.org/en/latest/oauth2.html#for-bots-using-service-account

### Deploy to Heroku
1. Create a heroku account. Then create an app to be linked to our container.
2. Install `heroku` CLI from https://devcenter.heroku.com/articles/heroku-cli
3. Change execute permissions with `sudo chmod +x deploy.sh`
4. Run `./deploy.sh` with the app name

### Development
1. You can run using `venv` or `docker-compose up` (https://docs.docker.com/compose/install/).
2. To change bot states, edit `bot.py`.
3. To change each state behavior, edit `handler.py`.
4. ~~To schedule announcements, edit `schedule.py`.~~ Anyone can schedule announcements in `ANNOUNCE_CHANNEL`! No need to wait for the developer.
5. To persistent data across restart, edit `db.py` to save in `SHEET_URL`.
6. If you make any changes to `Dockerfile` or `requirements.txt`, rebuild the image to see your changes, by running `docker-compose build`

## Lessons Learnt
- Credentials **MUST** be stored in `.env` which will be loaded in `docker-compose` and heroku. Access them using `os.getenv(NAME)`.
- Don't `print()`, use `logging.info()`
- No `@run_async` for critical states, eg submissions, questions
- `@sidecar` for state callbacks' lifecycle checks
- `escape_markdown(text, version=2)` for texts with `MarkdownV2`
- `Upper_case` for public functions
- `lower_case` for local functions
- `UPPER_CASE` for constants, eg states
- Annotate parameter types for sanity
- Design bot to be stateless for easier deployment
