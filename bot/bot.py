import logging
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import asyncio
import django
from asgiref.sync import sync_to_async
from .extract import fetch_live_games, extract_match_details
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
    user = update.message.from_user
    user_id = user.id
    username = user.username if user.username else "No Username"
    obj, created = await sync_to_async(User.objects.get_or_create)(
        telegram_id=user_id,
        defaults={'username': username, 'access_token': "ghdjkjGdkf124GhkfhE"}
    )


    # Log the user ID and username
    logger.info(f"New user started the bot: ID={user_id}, Username={username}")
    print(f"New user started the bot: ID={user_id}, Username={username}")
    
    await update.message.reply_text(
       "🏆 Welcome to the Ultimate Sports Tracking Bot! 🏀🎾🤾‍♂️ Stay updated with real-time scores, custom alerts for your favorite teams, and live betting odds across basketball, tennis, and handball. 🌍 Covering all major leagues, this bot ensures you never miss a key moment. Ready for more? Subscribe for exclusive access and take control of your game day experience! 💰"
    )
    await update.message.reply_text(
        "You can get updates of following games:\n\n"
        "1. Basketball\n2. Handball\n3. Tennis\n\n"
        "You can control me with these commands:\n\n"
        "Note:............."
        "If you are getting error in live_scores, Please subscribe to premium features\n\n"
        "/subscribe - 💰 Subscribe to premium features\n\n\n"
        "/livescores <game_name> - 📊 Get all live scores of selected game\n"
        "/livescore <game_name> <team_name> - 📊 Get live score of selected team\n"
        "/addfavorite <game_name> <team_name> - ⭐ Add a team to favorites\n"
        "/myfavorites - 📋 View your favorites\n"
        "/removefavorite <game_name> <team_name> - ❌ Remove a team from favorites\n"
    )

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "💰 To subscribe, choose a plan:\n"
        "1. Monthly - $5\n2. Yearly - $50\n\n"
        "Payment instructions coming soon!"
    )

async def select_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🏆 Select a game:\n1. Basketball\n2. Handball\n3. Tennis\n\n"
        "Use /selectgame <game_name>"
    )

async def add_favorite(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("❗ Usage: /addfavorite <game_name> <team_name>")
        return
    game_name, team_name = args[0], " ".join(args[1:])
    await update.message.reply_text(f"⭐ Added to favorites: {game_name} - {team_name}")

async def remove_favorite(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("❗ Usage: /removefavorite <game_name> <team_name>")
        return
    game_name, team_name = args[0], " ".join(args[1:])
    await update.message.reply_text(f"❌ Removed from favorites: {game_name} - {team_name}")

async def my_favorites(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    favorites = ["Basketball: Lakers", "Handball: Barcelona", "Tennis: Rafael Nadal"]
    await update.message.reply_text(f"📋 Your favorites:\n" + "\n".join(favorites))

# async def live_scores(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     if len(context.args) == 0:
#         await update.message.reply_text("❗ Usage: /livescores <game_name>")
#         return
#     game_name = context.args[0].lower()
#     if game_name in ["basketball", "handball", "tennis"]:
#         if game_name == "tennis":
#             await update.message.reply_text(f"📊 Fetching live scores for {game_name.capitalize()}... (Feature in development)")
#     else:
#         await update.message.reply_text("❗ Please select a valid game: Basketball, Handball, or Tennis.")

async def live_scores(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) == 0:
        await update.message.reply_text("❗ Usage: /livescores <game_name>")
        return
    game_name = context.args[0].lower()
    if game_name in ["basketball", "handball", "tennis"]:
        if game_name == "tennis":
            # Fetch live games from the extract.py functions
            live_games = fetch_live_games()
            if live_games:
                matches = extract_match_details(live_games)
                if matches:
                    response = "📊 Live scores for Tennis:\n"
                    for match in matches[:5]:
                        response += f"Match: {match['match']}\n"
                        response += f"Score: {match['score']}\n"
                        response += f"Set Scores: {match['sets']}\n"
                        response += f"Result: {match['result']}\n"
                        response += f"Status: {match['status'].capitalize()}\n\n"
                    await update.message.reply_text(response)
                else:
                    await update.message.reply_text("No live matches found.")
            else:
                await update.message.reply_text("Error fetching live games.")
    else:
        await update.message.reply_text("❗ Please select a valid game: Basketball, Handball, or Tennis.")


async def live_score(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) < 2:
        await update.message.reply_text("❗ Usage: /livescore <game_name> <team_name>")
        return
    game_name, team_name = context.args[0].lower(), " ".join(context.args[1:])
    if game_name in ["basketball", "handball", "tennis"]:
        await update.message.reply_text(f"📊 Fetching live score for {team_name} in {game_name.capitalize()}... (Feature in development)")
    else:
        await update.message.reply_text("❗ Please select a valid game: Basketball, Handball, or Tennis.")

def run_bot():
    # Create a new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Initialize your bot
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("selectgame", select_game))
    application.add_handler(CommandHandler("addfavorite", add_favorite))
    application.add_handler(CommandHandler("removefavorite", remove_favorite))
    application.add_handler(CommandHandler("myfavorites", my_favorites))
    application.add_handler(CommandHandler("livescores", live_scores))
    application.add_handler(CommandHandler("livescore", live_score))

    print("Polling....")
    
    # Run the bot polling inside the new event loop
    loop.run_until_complete(application.run_polling(poll_interval=3))

