import simplematrixbotlib as botlib
from tchap_bot.config.settings import Creds, Config


def create_bot(login_creds: Creds, bot_config: Config) -> botlib.Bot:
    creds = botlib.Creds(
        homeserver=login_creds.homeserver,
        username=login_creds.username,
        password=login_creds.password,
    )

    config = botlib.Config(
        emoji_verify=bot_config.emoji_verify,
        ignore_unverified_devices=bot_config.ignore_unverified_devices,
        encryption_enabled=bot_config.encryption_enabled
    )
    
    return botlib.Bot(creds, config)
