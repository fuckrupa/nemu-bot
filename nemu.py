import os
import re
import time
import asyncio
import random
import logging
import aiomysql
import threading
import urllib.parse as urlparse
from datetime import datetime
from typing import Optional, Dict, Any
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from http.server import BaseHTTPRequestHandler, HTTPServer
from aiogram.types import (
    Message, 
    CallbackQuery, 
    BotCommand,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BotCommandScopeDefault
)
from aiogram.enums import ParseMode, ChatType, ChatAction
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Bot token and database configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Array of image URLs
IMAGES = [
    "https://ik.imagekit.io/asadofc/Images1.png",
    "https://ik.imagekit.io/asadofc/Images2.png",
    "https://ik.imagekit.io/asadofc/Images3.png",
    "https://ik.imagekit.io/asadofc/Images4.png",
    "https://ik.imagekit.io/asadofc/Images5.png",
    "https://ik.imagekit.io/asadofc/Images6.png",
    "https://ik.imagekit.io/asadofc/Images7.png",
    "https://ik.imagekit.io/asadofc/Images8.png",
    "https://ik.imagekit.io/asadofc/Images9.png",
    "https://ik.imagekit.io/asadofc/Images10.png",
    "https://ik.imagekit.io/asadofc/Images11.png",
    "https://ik.imagekit.io/asadofc/Images12.png",
    "https://ik.imagekit.io/asadofc/Images13.png",
    "https://ik.imagekit.io/asadofc/Images14.png",
    "https://ik.imagekit.io/asadofc/Images15.png",
    "https://ik.imagekit.io/asadofc/Images16.png",
    "https://ik.imagekit.io/asadofc/Images17.png",
    "https://ik.imagekit.io/asadofc/Images18.png",
    "https://ik.imagekit.io/asadofc/Images19.png",
    "https://ik.imagekit.io/asadofc/Images20.png",
    "https://ik.imagekit.io/asadofc/Images21.png",
    "https://ik.imagekit.io/asadofc/Images22.png",
    "https://ik.imagekit.io/asadofc/Images23.png",
    "https://ik.imagekit.io/asadofc/Images24.png",
    "https://ik.imagekit.io/asadofc/Images25.png",
    "https://ik.imagekit.io/asadofc/Images26.png",
    "https://ik.imagekit.io/asadofc/Images27.png",
    "https://ik.imagekit.io/asadofc/Images28.png",
    "https://ik.imagekit.io/asadofc/Images29.png",
    "https://ik.imagekit.io/asadofc/Images30.png",
    "https://ik.imagekit.io/asadofc/Images31.png",
    "https://ik.imagekit.io/asadofc/Images32.png",
    "https://ik.imagekit.io/asadofc/Images33.png",
    "https://ik.imagekit.io/asadofc/Images34.png",
    "https://ik.imagekit.io/asadofc/Images35.png",
    "https://ik.imagekit.io/asadofc/Images36.png",
    "https://ik.imagekit.io/asadofc/Images37.png",
    "https://ik.imagekit.io/asadofc/Images38.png",
    "https://ik.imagekit.io/asadofc/Images39.png",
    "https://ik.imagekit.io/asadofc/Images40.png"
]

# Success messages for learning - SHORT AND STRAIGHTFORWARD
SUCCESS_LEARNING_MESSAGES = [
    "Got it!",
    "Learned!", 
    "Okay!",
    "Understood!"
]

# Failure messages for learning - SHORT AND STRAIGHTFORWARD
FAILURE_LEARNING_MESSAGES = [
    "Failed to learn!",
    "Learning error!",
    "Can't save now!",
    "Database busy!"
]

# Don't know response messages - SHORT AND STRAIGHTFORWARD
DONT_KNOW_MESSAGES = [
    "I don't know. Teach me.",
    "Help me learn.",
    "Unknown. Can you explain?",
    "New to me. Teach?",
    "Don't know. Help?"
]

# Personality prefixes for responses
PERSONALITY_PREFIXES = [
    "😶 ",
    "😌 "
]

# Logging color configuration
LOG_COLORS = {
    'DEBUG': '\033[92m',
    'INFO': '\033[93m', 
    'WARNING': '\033[94m',
    'ERROR': '\033[91m',
    'RESET': '\033[0m',
    'BOLD': '\033[1m'
}

# Start message template
START_MESSAGE = """🎉 <b>Hi {first_name}! I'm Nemu!</b>

😌 I learn how to talk by listening to my friends around me. Every chat helps me get a little smarter.

Just talk to me - I'll try my best!"""

# Short help message
HELP_SHORT_MESSAGE = """😶 Hi! I'm <b>Nemu</b>, a global learning bot!

💬 In groups, mention "Nemu" in your message to talk with me
📚 I learn from conversations when you teach me by replying to my messages
🌍 I remember everything globally and share knowledge across all chats

✨ Just mention my name and chat naturally - I'll learn as we go!"""

# Long help message
HELP_LONG_MESSAGE = """😶 <b>Meet Nemu - Your Global Learning Companion</b>

<b>How to interact with me:</b>
• In groups: Include "Nemu" in your message
• In private: Just send messages normally
• Reply to my messages to teach me new things

<b>How I learn globally:</b>
🧠 When I don't know something, I'll ask you to teach me
📝 Reply to my "I don't know" messages to teach me
🌍 I remember everything globally across all chats
🎯 Knowledge learned in one chat is available everywhere
💫 I get smarter with every interaction from anyone

<b>Commands Available:</b>
/start - Meet me and see what I can do
/help - Toggle this help information

<b>Pro Tips:</b>
• Teach me by replying when I ask
• I work great in group conversations
• Knowledge shared anywhere benefits everyone!"""

# Bot commands array
BOT_COMMANDS = [
    {"command": "start", "description": "💐 Wake me up"},
    {"command": "help", "description": "📙 Learn about Nemu"},
]

# Keyboard button configuration
KEYBOARD_BUTTONS = {
    "updates": {"text": "📢 Updates", "url": "https://t.me/WorkGlows"},
    "support": {"text": "💬 Support", "url": "https://t.me/SoulMeetsHQ"},
    "add_to_group": {"text": "➕ Add Me To Your Group"},
    "help_expand": {"text": "📖 Expand Help", "callback": "help_expand"},
    "help_minimize": {"text": "📕 Minimize Help", "callback": "help_minimize"}
}

# Database connection settings
DATABASE_CONFIG = {
    "minsize": 1,
    "maxsize": 10,
    "connect_timeout": 30,
    "echo": False
}

# Learning system configuration
LEARNING_CONFIG = {
    "max_learning_requests": 100,
    "max_bot_messages": 200,
    "personality_chance": 0.15,
    "max_retries": 3,
    "retry_delay": 5
}

# Color constants for logging
class Colors:
    BLUE = LOG_COLORS['WARNING']
    GREEN = LOG_COLORS['DEBUG'] 
    YELLOW = LOG_COLORS['INFO']
    RED = LOG_COLORS['ERROR']
    RESET = LOG_COLORS['RESET']
    BOLD = LOG_COLORS['BOLD']

# Custom colored logging formatter
class ColoredFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': Colors.GREEN,
        'INFO': Colors.YELLOW,
        'WARNING': Colors.BLUE,
        'ERROR': Colors.RED,
    }

    def format(self, record):
        original_format = super().format(record)
        color = self.COLORS.get(record.levelname, Colors.RESET)
        colored_format = f"{color}{original_format}{Colors.RESET}"
        return colored_format

# Setup colored logging system
def setup_colored_logging():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    formatter = ColoredFormatter(
        fmt='%(asctime)s - %(name)s - [%(levelname)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    return logger

# Initialize logger instance
logger = setup_colored_logging()

# Initialize bot and dispatcher
try:
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    logger.info("🤖 Bot and Dispatcher initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize bot: {e}")
    raise

# Global variables initialization
db_pool = None
learning_requests = {}
bot_messages = {}

# Dummy HTTP server handler
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Nemu bot is alive!")
        logger.debug("🌐 HTTP health check responded")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        pass

# Start dummy HTTP server
def start_dummy_server() -> None:
    try:
        port = int(os.environ.get("PORT", 10000))
        server = HTTPServer(("0.0.0.0", port), DummyHandler)
        logger.info(f"🌐 Dummy HTTP server started on port {port}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"❌ Failed to start HTTP server: {e}")

# Extract user information from message
def extract_user_info(msg: Message) -> Dict[str, any]:
    logger.debug("🔍 Extracting user information")
    u = msg.from_user
    c = msg.chat
    info = {
        "user_id": u.id,
        "username": u.username,
        "full_name": u.full_name,
        "chat_id": c.id,
        "chat_type": c.type,
        "chat_title": c.title or c.first_name or "",
        "chat_username": f"@{c.username}" if c.username else "No Username",
        "chat_link": f"https://t.me/{c.username}" if c.username else "No Link",
    }
    logger.info(
        f"📑 User info extracted: {info['full_name']} (@{info['username']}) "
        f"[ID: {info['user_id']}] in {info['chat_title']} [{info['chat_id']}] {info['chat_link']}"
    )
    return info

# Log messages with user info
def log_with_user_info(level: str, message: str, user_info: Dict[str, any]) -> None:
    user_detail = (
        f"👤 {user_info['full_name']} (@{user_info['username']}) "
        f"[ID: {user_info['user_id']}] | "
        f"💬 {user_info['chat_title']} [{user_info['chat_id']}] "
        f"({user_info['chat_type']}) {user_info['chat_link']}"
    )
    full_message = f"{message} | {user_detail}"

    if level.upper() == "INFO":
        logger.info(full_message)
    elif level.upper() == "DEBUG":
        logger.debug(full_message)
    elif level.upper() == "WARNING":
        logger.warning(full_message)
    elif level.upper() == "ERROR":
        logger.error(full_message)
    else:
        logger.info(full_message)

# Validate database URL format
def validate_database_url(database_url: str) -> bool:
    if not database_url:
        logger.error("❌ DATABASE_URL is empty")
        return False
    
    try:
        parsed = urlparse.urlparse(database_url)
        
        logger.debug(f"🔍 DATABASE_URL validation:")
        logger.debug(f"  - Scheme: {parsed.scheme}")
        logger.debug(f"  - Hostname: {parsed.hostname}")
        logger.debug(f"  - Port: {parsed.port}")
        logger.debug(f"  - Username: {parsed.username}")
        logger.debug(f"  - Password: {'***' if parsed.password else 'None'}")
        logger.debug(f"  - Database: {parsed.path[1:] if parsed.path else 'None'}")
        logger.debug(f"  - Query params: {parsed.query}")
        
        if parsed.scheme not in ['mysql', 'mysql+pymysql']:
            logger.warning(f"⚠️ Unusual database scheme: {parsed.scheme}")
        
        if not parsed.hostname:
            logger.error("❌ Missing hostname in DATABASE_URL")
            return False
            
        if not parsed.username:
            logger.error("❌ Missing username in DATABASE_URL") 
            return False
            
        if not parsed.password:
            logger.warning("⚠️ No password specified")
            
        if not parsed.path or parsed.path == '/':
            logger.warning("⚠️ No database name specified")
        
        logger.info("✅ DATABASE_URL format appears valid")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error parsing DATABASE_URL: {str(e)}")
        return False

# Check for Nemu trigger word
def contains_nemu_trigger(text: str) -> bool:
    if not text:
        logger.debug("🔍 No text for trigger check")
        return False

    text_lower = text.lower()
    contains_trigger = "nemu" in text_lower
    
    logger.debug(f"🔍 Trigger check: {'✅ Found' if contains_trigger else '❌ Not found'}")
    return contains_trigger

# Extract query from Nemu message
def extract_query_from_nemu_message(text: str) -> str:
    original_text = text
    
    # Remove "nemu" from message text
    text = re.sub(r'\bnemu\b', '', text, flags=re.IGNORECASE).strip()
    text = re.sub(r'^[,\s]*', '', text)
    text = re.sub(r'[,\s]*$', '', text)

    extracted_query = text.strip()
    logger.debug(f"🔤 Query extraction: '{original_text}' -> '{extracted_query}'")
    
    return extracted_query

# Initialize database connection pool
async def init_database():
    global db_pool
    max_retries = LEARNING_CONFIG["max_retries"]
    retry_count = 0

    logger.info("🗄️ Initializing database connection...")
    
    if not validate_database_url(DATABASE_URL):
        logger.error("❌ Invalid DATABASE_URL, skipping database")
        return False

    while retry_count < max_retries:
        try:
            import urllib.parse as urlparse
            parsed = urlparse.urlparse(DATABASE_URL)

            if not parsed.hostname:
                logger.error("❌ Invalid DATABASE_URL: Missing hostname")
                return False
            
            if not parsed.username:
                logger.error("❌ Invalid DATABASE_URL: Missing username")
                return False

            logger.info(f"🔌 Attempting database connection (attempt {retry_count + 1}/{max_retries})...")
            logger.debug(f"🏠 Database host: {parsed.hostname}:{parsed.port or 3306}")
            logger.debug(f"👤 Database user: {parsed.username}")
            logger.debug(f"📦 Database name: {parsed.path[1:] if parsed.path else 'Not specified'}")

            # SSL configuration if needed
            ssl_config = None
            if 'ssl-mode=REQUIRED' in DATABASE_URL or 'sslmode=require' in DATABASE_URL:
                import ssl
                ssl_config = ssl.create_default_context()
                ssl_config.check_hostname = False
                ssl_config.verify_mode = ssl.CERT_NONE
                logger.debug("🔐 SSL configured for database")

            db_pool = await aiomysql.create_pool(
                host=parsed.hostname,
                port=parsed.port or 3306,
                user=parsed.username,
                password=parsed.password,
                db=parsed.path[1:] if parsed.path else None,
                ssl=ssl_config,
                autocommit=True,
                **DATABASE_CONFIG
            )

            logger.debug("🧪 Testing database connection...")
            async with db_pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT 1 AS test")
                    result = await cursor.fetchone()
                    logger.debug(f"✅ Database test result: {result}")

            await create_tables()
            logger.info("🎉 Database connection established successfully!")
            return True

        except aiomysql.Error as e:
            retry_count += 1
            logger.error(f"❌ MySQL error (attempt {retry_count}): {str(e)}")
        except Exception as e:
            retry_count += 1
            logger.error(f"❌ Database connection error (attempt {retry_count}): {str(e)}")

            if retry_count < max_retries:
                logger.warning(f"⏳ Retrying database connection in {LEARNING_CONFIG['retry_delay']} seconds...")
                await asyncio.sleep(LEARNING_CONFIG["retry_delay"])
            else:
                logger.error("💀 Failed to establish database connection after retries!")
                logger.error("💡 Check your DATABASE_URL format and credentials")
                db_pool = None
                return False

# Create database tables if needed
async def create_tables():
    global db_pool
    
    logger.info("📋 Creating/verifying database tables")
    
    if not db_pool:
        logger.warning("⚠️ Database pool not available")
        return

    try:
        async with db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                logger.debug("🏗️ Creating nemu_global_knowledge table...")
                await cursor.execute("""
                    CREATE TABLE IF NOT EXISTS nemu_global_knowledge (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        trigger_message TEXT NOT NULL,
                        response TEXT NOT NULL,
                        taught_by_user_id BIGINT NOT NULL,
                        taught_by_username VARCHAR(255),
                        taught_in_chat_id BIGINT NOT NULL,
                        taught_in_chat_title VARCHAR(255),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        usage_count INT DEFAULT 0,
                        global_usage_count INT DEFAULT 0,
                        INDEX idx_trigger (trigger_message(100)),
                        FULLTEXT idx_message_fulltext (trigger_message, response)
                    )
                """)
                logger.debug("✅ nemu_global_knowledge table created/verified")

                logger.debug("🏗️ Creating nemu_interactions table...")
                await cursor.execute("""
                    CREATE TABLE IF NOT EXISTS nemu_interactions (
                        user_id BIGINT PRIMARY KEY,
                        username VARCHAR(255),
                        first_name VARCHAR(255),
                        total_messages INT DEFAULT 0,
                        times_taught_nemu INT DEFAULT 0,
                        times_helped_by_nemu INT DEFAULT 0,
                        first_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    )
                """)
                logger.debug("✅ nemu_interactions table created/verified")
                
                logger.info("🎉 All database tables created/verified successfully!")
    except Exception as e:
        logger.error(f"❌ Error creating tables: {str(e)}")
        raise

# Learn from user reply to bot
async def learn_from_reply(chat_id: int, user_id: int, username: str, chat_title: str, original_query: str, teaching_response: str):
    global db_pool

    logger.info(f"🌍 GLOBAL learning attempt - User: {username} ({user_id})")

    if not db_pool:
        logger.warning("⚠️ Database not available for learning")
        return "failed"

    try:
        async with db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                logger.debug(f"🔍 Checking for existing GLOBAL knowledge")
                await cursor.execute("""
                    SELECT id, response FROM nemu_global_knowledge 
                    WHERE LOWER(trigger_message) = LOWER(%s)
                    ORDER BY global_usage_count DESC, updated_at DESC
                    LIMIT 1
                """, (original_query,))

                existing = await cursor.fetchone()

                if existing:
                    logger.info(f"🔄 Updating existing GLOBAL knowledge")
                    await cursor.execute("""
                        UPDATE nemu_global_knowledge 
                        SET response = %s, taught_by_user_id = %s, taught_by_username = %s, 
                            taught_in_chat_id = %s, taught_in_chat_title = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (teaching_response, user_id, username, chat_id, chat_title, existing[0]))
                    action = "updated"
                else:
                    logger.info("➕ Adding new GLOBAL knowledge")
                    await cursor.execute("""
                        INSERT INTO nemu_global_knowledge (trigger_message, response, taught_by_user_id, taught_by_username, taught_in_chat_id, taught_in_chat_title)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (original_query, teaching_response, user_id, username, chat_id, chat_title))
                    action = "learned"

                logger.debug(f"📊 Updating user interaction stats")
                await cursor.execute("""
                    INSERT INTO nemu_interactions (user_id, username, times_taught_nemu)
                    VALUES (%s, %s, 1) AS new_data
                    ON DUPLICATE KEY UPDATE
                    username = new_data.username,
                    times_taught_nemu = nemu_interactions.times_taught_nemu + 1,
                    last_interaction = CURRENT_TIMESTAMP
                """, (user_id, username))

                logger.info(f"✅ GLOBAL learning successful: {action}")
                return action
    except Exception as e:
        logger.error(f"❌ Error learning from reply: {str(e)}")
        return "failed"

# Find response in knowledge base
async def find_nemu_response(query: str) -> Optional[str]:
    global db_pool

    logger.debug(f"🌍 Searching GLOBAL knowledge")

    if not db_pool or not query.strip():
        logger.warning("⚠️ Database unavailable or empty query")
        return None

    try:
        async with db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                logger.debug("🎯 Attempting exact match search")
                await cursor.execute("""
                    SELECT response, id FROM nemu_global_knowledge 
                    WHERE LOWER(trigger_message) = LOWER(%s)
                    ORDER BY global_usage_count DESC, updated_at DESC
                    LIMIT 1
                """, (query,))

                result = await cursor.fetchone()

                if result and result[0]:
                    logger.info(f"✅ GLOBAL exact match found")
                    await cursor.execute("""
                        UPDATE nemu_global_knowledge 
                        SET usage_count = usage_count + 1, global_usage_count = global_usage_count + 1 
                        WHERE id = %s
                    """, (result[1],))
                    return result[0]

                # Try fulltext search if available
                logger.debug("🔎 Exact match not found, trying fulltext")
                if len(query.split()) >= 2:
                    await cursor.execute("""
                        SELECT response, id,
                        MATCH(trigger_message) AGAINST(%s IN NATURAL LANGUAGE MODE) as relevance
                        FROM nemu_global_knowledge 
                        WHERE MATCH(trigger_message) AGAINST(%s IN NATURAL LANGUAGE MODE) > 0.3
                        ORDER BY relevance DESC, global_usage_count DESC
                        LIMIT 1
                    """, (query, query))

                    result = await cursor.fetchone()

                    if result and result[0]:
                        logger.info(f"✅ GLOBAL fulltext match found")
                        await cursor.execute("""
                            UPDATE nemu_global_knowledge 
                            SET usage_count = usage_count + 1, global_usage_count = global_usage_count + 1 
                            WHERE id = %s
                        """, (result[1],))
                        return result[0]

                # Try partial matching as fallback
                logger.debug("🔍 Trying GLOBAL partial matching")
                await cursor.execute("""
                    SELECT response, id FROM nemu_global_knowledge 
                    WHERE LOWER(trigger_message) LIKE CONCAT('%%', LOWER(%s), '%%') 
                    OR LOWER(%s) LIKE CONCAT('%%', LOWER(trigger_message), '%%')
                    ORDER BY global_usage_count DESC, updated_at DESC
                    LIMIT 1
                """, (query, query))

                result = await cursor.fetchone()

                if result and result[0]:
                    logger.info(f"✅ GLOBAL partial match found")
                    await cursor.execute("""
                        UPDATE nemu_global_knowledge 
                        SET usage_count = usage_count + 1, global_usage_count = global_usage_count + 1 
                        WHERE id = %s
                    """, (result[1],))
                    return result[0]
                    
                logger.debug("❌ No matches found in knowledge")
    except Exception as e:
        logger.error(f"❌ Error finding response: {str(e)}")

    return None

# Update user interaction statistics
async def update_user_interaction(user_id: int, username: str = None, first_name: str = None, helped_by_nemu: bool = False):
    global db_pool

    logger.debug(f"📊 Updating interaction stats")

    if not db_pool:
        logger.warning("⚠️ Database unavailable for interaction update")
        return

    try:
        async with db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                helped_count = 1 if helped_by_nemu else 0

                await cursor.execute("""
                    INSERT INTO nemu_interactions (user_id, username, first_name, total_messages, times_helped_by_nemu)
                    VALUES (%s, %s, %s, 1, %s) AS new_data
                    ON DUPLICATE KEY UPDATE
                    username = new_data.username,
                    first_name = new_data.first_name,
                    total_messages = nemu_interactions.total_messages + 1,
                    times_helped_by_nemu = nemu_interactions.times_helped_by_nemu + new_data.times_helped_by_nemu,
                    last_interaction = CURRENT_TIMESTAMP
                """, (user_id, username, first_name, helped_count))
                
                logger.debug(f"✅ User interaction updated")
    except Exception as e:
        logger.error(f"❌ Error updating user interaction: {str(e)}")

# Setup bot commands menu
async def setup_commands():
    logger.info("⚙️ Setting up bot commands")
    
    try:
        commands = []
        for cmd in BOT_COMMANDS:
            commands.append(BotCommand(command=cmd["command"], description=cmd["description"]))

        await bot.set_my_commands(commands, BotCommandScopeDefault())
        logger.info("✅ Bot commands menu set")
    except Exception as e:
        logger.error(f"❌ Failed to setup commands: {str(e)}")

# Start HTTP server thread
try:
    threading.Thread(target=start_dummy_server, daemon=True).start()
    logger.info("🧵 HTTP server thread started")
except Exception as e:
    logger.error(f"❌ Failed to start HTTP thread: {e}")

# Log bot initialization status
logger.info(f"🚀 Bot initialization with TOKEN: {'✅ Set' if BOT_TOKEN != 'YOUR_BOT_TOKEN_HERE' else '❌ Not Set'}")
logger.info(f"🗄️ Database URL: {'✅ Configured' if DATABASE_URL else '❌ Not Configured'}")
logger.info(f"📸 Loaded {len(IMAGES)} images")
logger.info("📝 Help messages and data initialized")

# Handle /start command
@dp.message(CommandStart())
async def start_command(message: Message):
    user_info = extract_user_info(message)
    log_with_user_info("INFO", "🚀 /start command triggered", user_info)
    
    try:
        user = message.from_user

        # Update user interaction stats
        await update_user_interaction(user.id, user.username, user.first_name)

        # Build inline keyboard
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text=KEYBOARD_BUTTONS["updates"]["text"], url=KEYBOARD_BUTTONS["updates"]["url"]),
            InlineKeyboardButton(text=KEYBOARD_BUTTONS["support"]["text"], url=KEYBOARD_BUTTONS["support"]["url"])
        )

        # Add group button dynamically
        bot_info = await bot.get_me()
        group_add_url = f"https://t.me/{bot_info.username}?startgroup=true"
        builder.row(
            InlineKeyboardButton(text=KEYBOARD_BUTTONS["add_to_group"]["text"], url=group_add_url)
        )

        # Select random image
        random_image = random.choice(IMAGES)
        logger.debug(f"🎲 Selected random image: {random_image}")

        # Format welcome message
        welcome_text = START_MESSAGE.format(first_name=user.first_name)

        await message.answer_photo(
            photo=random_image,
            caption=welcome_text,
            reply_markup=builder.as_markup(),
            parse_mode=ParseMode.HTML
        )
        
        log_with_user_info("INFO", "✅ /start command completed", user_info)
        
    except Exception as e:
        logger.error(f"❌ Error in start command: {str(e)}")
        log_with_user_info("ERROR", f"❌ /start command failed: {str(e)}", user_info)

# Handle /help command
@dp.message(Command("help"))
async def help_command(message: Message):
    user_info = extract_user_info(message)
    log_with_user_info("INFO", "❓ /help command triggered", user_info)
    
    try:
        # Build help keyboard
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text=KEYBOARD_BUTTONS["help_expand"]["text"], callback_data=KEYBOARD_BUTTONS["help_expand"]["callback"]))

        await message.answer(
            HELP_SHORT_MESSAGE,
            reply_markup=builder.as_markup(),
            parse_mode=ParseMode.HTML
        )
        
        log_with_user_info("INFO", "✅ /help command completed", user_info)
        
    except Exception as e:
        logger.error(f"❌ Error in help command: {str(e)}")
        log_with_user_info("ERROR", f"❌ /help command failed: {str(e)}", user_info)

# Handle help expand callback
@dp.callback_query(F.data == "help_expand")
async def expand_help(callback: CallbackQuery):
    user_info = extract_user_info(callback.message)
    log_with_user_info("INFO", "📖 Help expand callback triggered", user_info)
    
    try:
        # Build minimize keyboard
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text=KEYBOARD_BUTTONS["help_minimize"]["text"], callback_data=KEYBOARD_BUTTONS["help_minimize"]["callback"]))

        await callback.message.edit_text(
            HELP_LONG_MESSAGE,
            reply_markup=builder.as_markup(),
            parse_mode=ParseMode.HTML
        )
        await callback.answer()
        
        log_with_user_info("INFO", "✅ Help expanded successfully", user_info)
        
    except Exception as e:
        logger.error(f"❌ Error expanding help: {str(e)}")
        log_with_user_info("ERROR", f"❌ Help expand failed: {str(e)}", user_info)

# Handle help minimize callback
@dp.callback_query(F.data == "help_minimize")
async def minimize_help(callback: CallbackQuery):
    user_info = extract_user_info(callback.message)
    log_with_user_info("INFO", "📕 Help minimize callback triggered", user_info)
    
    try:
        # Build expand keyboard
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text=KEYBOARD_BUTTONS["help_expand"]["text"], callback_data=KEYBOARD_BUTTONS["help_expand"]["callback"]))

        await callback.message.edit_text(
            HELP_SHORT_MESSAGE,
            reply_markup=builder.as_markup(),
            parse_mode=ParseMode.HTML
        )
        await callback.answer()
        
        log_with_user_info("INFO", "✅ Help minimized successfully", user_info)
        
    except Exception as e:
        logger.error(f"❌ Error minimizing help: {str(e)}")
        log_with_user_info("ERROR", f"❌ Help minimize failed: {str(e)}", user_info)

# Handle /ping command
@dp.message(Command("ping"))
async def ping_command(message: Message):
    user_info = extract_user_info(message)
    log_with_user_info("INFO", "🏓 /ping command triggered", user_info)
    
    try:
        # Calculate ping time
        start_time = time.time()

        if message.chat.type == ChatType.PRIVATE:
            ping_msg = await message.answer("🛰️ Pinging...")
        else:
            ping_msg = await message.reply("🛰️ Pinging...")

        end_time = time.time()
        ping_time = round((end_time - start_time) * 1000, 2)

        logger.debug(f"🏓 Ping calculated: {ping_time}ms")

        # Format pong response
        pong_text = f'🏓 <a href="https://t.me/SoulMeetsHQ">Pong!</a> {ping_time}ms'

        await ping_msg.edit_text(
            pong_text,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        
        log_with_user_info("INFO", f"✅ /ping completed: {ping_time}ms", user_info)
        
    except Exception as e:
        logger.error(f"❌ Error in ping command: {str(e)}")
        log_with_user_info("ERROR", f"❌ /ping command failed: {str(e)}", user_info)

# Handle all other messages
@dp.message()
async def handle_nemu_conversation(message: Message):
    if not message.text:
        logger.debug("📝 Ignoring non-text message")
        return

    # Extract message information
    user_info = extract_user_info(message)
    user_id = message.from_user.id
    chat_id = message.chat.id
    text = message.text.strip()
    user = message.from_user
    chat_title = message.chat.title or message.chat.first_name or f"Chat {chat_id}"

    log_with_user_info("DEBUG", f"📨 Processing message: '{text[:100]}...'", user_info)

    try:
        # Check if replying to learning request
        if message.reply_to_message and message.reply_to_message.message_id in learning_requests:
            original_query = learning_requests[message.reply_to_message.message_id]
            
            log_with_user_info("INFO", f"🌍 User teaching Nemu GLOBALLY", user_info)

            # Learn from the reply
            action = await learn_from_reply(chat_id, user_id, user.username or user.first_name, chat_title, original_query, text)

            # Remove learning request
            del learning_requests[message.reply_to_message.message_id]
            logger.debug(f"🗑️ Removed learning request")

            # Send appropriate response with typing indicator
            if action == "failed":
                selected_message = random.choice(FAILURE_LEARNING_MESSAGES)
            else:
                selected_message = random.choice(SUCCESS_LEARNING_MESSAGES)

            logger.debug(f"💬 Selected response message")

            # Show typing indicator
            await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
            await asyncio.sleep(2)  # Brief pause for typing effect

            response_msg = await message.reply(selected_message, parse_mode=ParseMode.HTML)
            bot_messages[response_msg.message_id] = True

            log_with_user_info("INFO", f"✅ GLOBAL learning completed: {action}", user_info)
            return

        # Check if replying to bot
        if message.reply_to_message and message.reply_to_message.message_id in bot_messages:
            should_respond = True
            query = text
            log_with_user_info("DEBUG", "🔄 Reply to Nemu detected", user_info)
        else:
            # Check for trigger in groups
            if message.chat.type != ChatType.PRIVATE:
                if not contains_nemu_trigger(text):
                    logger.debug("🚫 No Nemu trigger found")
                    return
                should_respond = True
                query = extract_query_from_nemu_message(text)
                log_with_user_info("DEBUG", f"🎯 Nemu trigger found", user_info)
            else:
                # Always respond in private
                should_respond = True
                query = text
                log_with_user_info("DEBUG", "💬 Private chat message", user_info)

        if not should_respond:
            logger.debug("🚫 Should not respond")
            return

        # Update interaction statistics
        await update_user_interaction(user_id, user.username, user.first_name)

        # Validate query length
        if not query or len(query.strip()) < 2:
            log_with_user_info("WARNING", f"⚠️ Query too short", user_info)
            return

        # Search for existing response
        logger.debug(f"🌍 Searching GLOBAL knowledge base")
        response = await find_nemu_response(query)

        if response:
            # Found response in knowledge base
            log_with_user_info("INFO", f"🧠 GLOBAL knowledge found", user_info)
            await update_user_interaction(user_id, user.username, user.first_name, helped_by_nemu=True)

            # Add personality prefix randomly
            if random.random() < LEARNING_CONFIG["personality_chance"]:
                personality_prefix = random.choice(PERSONALITY_PREFIXES)
                response = personality_prefix + response
                logger.debug(f"✨ Added personality prefix")

            # Show typing indicator
            await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
            await asyncio.sleep(2)  # Brief pause for typing effect

            response_msg = await message.reply(response, parse_mode=ParseMode.HTML)
            bot_messages[response_msg.message_id] = True

            log_with_user_info("INFO", "✅ GLOBAL response sent", user_info)

        else:
            # No knowledge found, ask for teaching
            log_with_user_info("INFO", f"❓ No GLOBAL knowledge found", user_info)
            
            learning_response = random.choice(DONT_KNOW_MESSAGES)
            logger.debug(f"📚 Selected global learning request")
            
            # Show typing indicator
            await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
            await asyncio.sleep(2)  # Brief pause for typing effect
            
            response_msg = await message.reply(learning_response, parse_mode=ParseMode.HTML)

            # Store learning request
            learning_requests[response_msg.message_id] = query
            bot_messages[response_msg.message_id] = True
            
            logger.debug(f"📝 Stored GLOBAL learning request")

            # Clean up old requests
            if len(learning_requests) > LEARNING_CONFIG["max_learning_requests"]:
                oldest_keys = list(learning_requests.keys())[:-LEARNING_CONFIG["max_learning_requests"]]
                for key in oldest_keys:
                    del learning_requests[key]
                logger.debug(f"🧹 Cleaned up old learning requests")

            # Clean up old messages
            if len(bot_messages) > LEARNING_CONFIG["max_bot_messages"]:
                oldest_keys = list(bot_messages.keys())[:-LEARNING_CONFIG["max_bot_messages"]]
                for key in oldest_keys:
                    del bot_messages[key]
                logger.debug(f"🧹 Cleaned up old bot messages")

            log_with_user_info("INFO", "✅ GLOBAL learning request sent", user_info)

    except Exception as e:
        logger.error(f"❌ Error in conversation handler: {str(e)}")
        log_with_user_info("ERROR", f"❌ Conversation handling failed: {str(e)}", user_info)
        
        # Send error message to user
        try:
            await message.reply("😅 Sorry, I encountered an error. Please try again!")
        except Exception as reply_error:
            logger.error(f"❌ Failed to send error message: {str(reply_error)}")

# Main bot execution function
async def main():
    logger.info("🚀 Nemu GLOBAL LEARNING initialization started...")

    try:
        # Initialize database connection
        logger.info("🗄️ Initializing database for global learning...")
        db_success = await init_database()

        if not db_success:
            logger.warning("⚠️ Starting Nemu without database connection!")
            logger.warning("⚠️ Nemu will work with limited functionality")

        # Setup bot commands
        logger.info("⚙️ Setting up commands...")
        await setup_commands()

        logger.info("🎉 Nemu GLOBAL LEARNING ready and starting...")

        # Start polling for messages
        await dp.start_polling(bot)
        
    except KeyboardInterrupt:
        logger.info("⏹️ Received interrupt signal, shutting down...")
    except Exception as e:
        logger.error(f"💀 Critical error in main: {str(e)}")
        raise
    finally:
        # Clean up resources
        logger.info("🔧 Cleaning up resources...")
        if db_pool:
            try:
                db_pool.close()
                await db_pool.wait_closed()
                logger.info("✅ Database pool closed")
            except Exception as e:
                logger.error(f"❌ Error closing database pool: {str(e)}")
        
        logger.info("👋 Nemu GLOBAL LEARNING shutdown complete")

# Entry point for bot execution
if __name__ == "__main__":
    try:
        logger.info("=" * 60)
        logger.info("🤖 NEMU BOT - GLOBAL LEARNING MODE - STARTING UP")
        logger.info("=" * 60)
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⏹️ Bot stopped by user")
    except Exception as e:
        logger.error(f"💀 Fatal error: {str(e)}")
        raise