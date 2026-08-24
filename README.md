# Schedule bot
### About
This is the repository of telegram bot application that provides schedule of lessons for SPbSEU university.

### Installation
To run the application you need to clone the repository:

`git clone https://github.com/smart7even/schedule-bot.git`

Then install all dependencies:

`pip3 install -r requirements.txt`

Now you need to create `.env` file in root of the project and specify key `DATABASE_URL` with your database url and key `SCHEDULE_BOT_TOKEN` with telegram bot token.

Open project root in console and make database migrations entering command `alembic upgrade head` and then fill your database running `bot_init.py` script.

Now you can use application running `main.py` script.

### Server run
To run api server in dev mode use following command

`uvicorn server:app --env-file .env --reload --host 0.0.0.0`

### Runtime feature flags

Feature flags are stored in the database and evaluated on every request, so a
change does not require an API restart. They default to `false` if configuration
storage is unavailable.

The public read-only configuration is available at `GET /app/config`. Change a
flag from an authenticated server shell instead of exposing an admin web page:

```sh
python3 manage_feature_flags.py list
python3 manage_feature_flags.py set room_map_button_enabled false
python3 manage_feature_flags.py set room_map_caption_enabled false
```

Only the flags listed by the command are accepted. Each write records its
database update time.
