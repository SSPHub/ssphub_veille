from config import bot

if __name__ == "__main__":
    # Importer les modules de listeners pour enregistrer les décorateurs
    import listeners.echo
    import listeners.parser

    # Démarrer le bot
    bot.run()


