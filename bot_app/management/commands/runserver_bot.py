# bot_app/management/commands/runserver_bot.py
import os
import threading
from django.core.management.commands.runserver import Command as RunserverCommand
from django.conf import settings
from bot.bot import run_bot

class Command(RunserverCommand):
    help = 'Runs server with Telegram bot'

    def handle(self, *args, **options):
        # Check if this is the main server process (not auto-reloader)
        if os.environ.get('RUN_MAIN') == 'true':
            bot_thread = threading.Thread(target=run_bot, daemon=True)
            bot_thread.start()
            self.stdout.write(self.style.SUCCESS("Telegram bot started"))
        
        # Run the server
        super().handle(*args, **options)