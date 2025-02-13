import logging
import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
import asyncio
import django
from asgiref.sync import sync_to_async
from django.utils import timezone
# Load environment variables
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from bot_app.models import User

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Command Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ask the user for an access token before allowing access."""
     
    keyboard = [
        [InlineKeyboardButton("🔑 Enter Token", callback_data="enter_token")],
        [InlineKeyboardButton("💰 Subscribe", callback_data="subscribe")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔒 You need an access token to activate the bot.\n"
        "If you already have one, enter it now.\n"
        "Otherwise, subscribe to get a new token.",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button clicks for entering token or subscribe"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "enter_token":
        await query.message.reply_text("🔑 Please enter your access token:")
        context.user_data["awaiting_token"] = True
        
    elif query.data == "subscribe":
        await subscribe(update, context)

async def handle_token(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process the access token entered by the user and keep prompting if invalid."""
    if context.user_data.get("awaiting_token"):
        while True:
            token = update.message.text.strip()
            user = update.message.from_user
            user_id = user.id
            username = user.username if user.username else "No Username"
            
            obj, created = await sync_to_async(User.objects.get_or_create)(
                telegram_id=user_id,
                defaults={'username': username}
            )
            
            if created:
                await update.message.reply_text("🔔 New user detected. Redirecting to subscription...")
                await subscribe(update, context)
                return
            
            if obj.access_token == token and obj.expiration_date > timezone.now():
                await update.message.reply_text(
                    "✅ Welcome to the bot!\n\n"
                    "⚽ You will receive **pre-match** and **live match** odds 📊 for favorite teams of:\n"
                    "🎾 **Tennis**\n🏀 **Basketball**\n🤾 **Handball**"
                )
                break  # Exit loop if valid token
            else:
                keyboard = [
                    [InlineKeyboardButton("💰 Subscribe", callback_data="subscribe")],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text("❌ Invalid or Expired token! Please enter again or subscribe.", reply_markup=reply_markup)
                return  # Wait for the user to enter again
        
        del context.user_data["awaiting_token"]


async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message  # This ensures it works for both text & callback
    if message:
        await message.reply_text(
            "💰 To subscribe, choose a plan:\n"
            "1. Monthly - $5\n2. Yearly - $50\n\n"
            "Payment instructions coming soon!"
        )
    

def run_bot():
    # Create a new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Initialize your bot
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_token))
    
    print("Polling....")
    # Run the bot polling inside the new event loop
    loop.run_until_complete(application.run_polling(poll_interval=3))


