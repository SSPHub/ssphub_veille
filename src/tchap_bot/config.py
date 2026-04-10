import simplematrixbotlib as botlib
import os

creds = botlib.Creds(
    "https://matrix.agent.finances.tchap.gouv.fr", 
    os.environ["TCHAP_BOT_SSPHUB_MATRIX_ID"], 
    os.environ["TCHAP_BOT_SSPHUB_PWD"],
    session_stored_file="session.txt")

config = botlib.Config()
config.emoji_verify = True
config.ignore_unverified_devices = True
config.encryption_enabled = True

bot = botlib.Bot(creds, config)