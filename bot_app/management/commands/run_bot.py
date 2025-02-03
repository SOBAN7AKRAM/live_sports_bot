from django.core.management.base import BaseCommand
from bot.bot import run_bot  # Import the run_bot function from your bot module
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

# Now you can import Django models
from bot_app.models import User

class Command(BaseCommand):
    help = "Runs the Telegram Bot"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Starting the Telegram bot..."))
        run_bot()