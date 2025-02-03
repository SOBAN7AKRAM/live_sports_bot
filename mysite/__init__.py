# import threading
# from bot.bot import run_bot

# def start_bot():
#     threading.Thread(target=run_bot, daemon=True).start()

# start_bot()

import threading
import logging
from django.apps import apps
from django.core.wsgi import get_wsgi_application

def start_bot():
    logging.info("Preparing to start the bot in a separate thread...")

    def run():
        from bot.bot import run_bot
        run_bot()

    # Ensure Django apps are loaded before starting the bot
    if apps.ready:
        logging.info("Django apps are ready, starting the bot...")
        bot_thread = threading.Thread(target=run)
        bot_thread.daemon = True  # Ensures the bot stops when Django stops
        bot_thread.start()
    else:
        logging.error("Django apps are not ready. Bot will not start.")

start_bot()


