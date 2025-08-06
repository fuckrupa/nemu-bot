import asyncio
import os
import random
import time
import re
import threading
import logging
from datetime import datetime
from typing import Optional, Dict, any
from http.server import BaseHTTPRequestHandler, HTTPServer

import aiomysql
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    Message, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    CallbackQuery,
    BotCommand,
    BotCommandScopeDefault
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ParseMode, ChatType

# Color codes for logging
class Colors:
    BLUE = '\033[94m'      # INFO/WARNING
    GREEN = '\033[92m'     # DEBUG
    YELLOW = '\033[93m'    # INFO
    RED = '\033[91m'       # ERROR
    RESET = '\033[0m'      # Reset color
    BOLD = '\033[1m'       # Bold text

class ColoredFormatter(logging.Formatter):
    """Custom formatter to add colors to entire log messages"""

    COLORS = {
        'DEBUG': Colors.GREEN,
        'INFO': Colors.YELLOW,
        'WARNING': Colors.BLUE,
        'ERROR': Colors.RED,
    }

    def format(self, record):
        # Get the original formatted message
        original_format = super().format(record)

        # Get color based on log level
        color = self.COLORS.get(record.levelname, Colors.RESET)

        # Apply color to the entire message
        colored_format = f"{color}{original_format}{Colors.RESET}"

        return colored_format

# Configure logging with colors
def setup_colored_logging():
    """Setup colored logging configuration"""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    # Create colored formatter with enhanced format
    formatter = ColoredFormatter(
        fmt='%(asctime)s - %(name)s - [%(levelname)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(console_handler)

    return logger

# Initialize colored logger
logger = setup_colored_logging()

def extract_user_info(msg: Message) -> Dict[str, any]:
    """Extract user and chat information from message"""
    logger.debug("🔍 Extracting user information from message")
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


def log_with_user_info(level: str, message: str, user_info: Dict[str, any]) -> None:
    """Log message with user information"""
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

# Environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
DATABASE_URL = os.getenv("DATABASE_URL", "")

logger.info(f"🚀 Bot initialization started with TOKEN: {'✅ Set' if BOT_TOKEN != 'YOUR_BOT_TOKEN_HERE' else '❌ Not Set'}")
logger.info(f"🗄️ Database URL: {'✅ Configured' if DATABASE_URL else '❌ Not Configured'}")

# Images for /start command
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

logger.info(f"📸 Loaded {len(IMAGES)} images for /start command")

# Initialize bot and dispatcher
try:
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    logger.info("🤖 Bot and Dispatcher initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize bot: {e}")
    raise

# Database connection pool
db_pool = None

# Help messages
HELP_SHORT = "🤖 Hi! I'm <b>Nemu</b>, a learning bot!\n\n💬 In groups, mention \"Nemu\" in your message to talk with me\n📚 I learn from conversations when you teach me by replying to my messages\n🧠 I remember everything you teach me and use it to help others\n\n✨ Just mention my name and chat naturally - I'll learn as we go!"

HELP_LONG = "🤖 <b>Meet Nemu - Your Learning Companion</b>\n\n<b>How to interact with me:</b>\n• In groups: Include \"Nemu\" in your message\n• In private: Just send messages normally\n• Reply to my messages to teach me new things\n\n<b>How I learn:</b>\n🧠 When I don't know something, I'll ask you to teach me\n📝 Reply to my \"I don't know\" messages to teach me\n💾 I remember everything and use it to help others\n🎯 I get smarter with every interaction\n\n<b>Commands Available:</b>\n/start - Meet me and see what I can do\n/help - Toggle this help information\n\n<b>Pro Tips:</b>\n• Teach me by replying when I ask\n• I work great in group conversations\n• The more you teach me, the smarter I become!"

# Nemu's learning requests - store message IDs waiting for teaching
learning_requests = {}

# Bot's own message tracking for replies
bot_messages = {}

logger.info("📝 Help messages and data structures initialized")

# HTTP SERVER FOR DEPLOYMENT
class DummyHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for keep-alive server"""

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Nemu bot is alive!")
        logger.debug("🌐 HTTP health check responded")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        # Suppress HTTP server logs
        pass

def start_dummy_server() -> None:
    """Start dummy HTTP server for deployment platforms"""
    try:
        port = int(os.environ.get("PORT", 10000))
        server = HTTPServer(("0.0.0.0", port), DummyHandler)
        logger.info(f"🌐 Dummy HTTP server started on port {port}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"❌ Failed to start HTTP server: {e}")

# Start HTTP server in background thread
try:
    threading.Thread(target=start_dummy_server, daemon=True).start()
    logger.info("🧵 HTTP server thread started successfully")
except Exception as e:
    logger.error(f"❌ Failed to start HTTP server thread: {e}")

async def init_database():
    """Initialize database connection pool"""
    global db_pool
    max_retries = 3
    retry_count = 0

    logger.info("🗄️ Initializing database connection...")

    while retry_count < max_retries:
        try:
            # Parse DATABASE_URL
            import urllib.parse as urlparse
            parsed = urlparse.urlparse(DATABASE_URL)

            logger.info(f"🔌 Attempting database connection (attempt {retry_count + 1}/{max_retries})...")
            logger.debug(f"🏠 Database host: {parsed.hostname}:{parsed.port}")
            logger.debug(f"👤 Database user: {parsed.username}")
            logger.debug(f"📦 Database name: {parsed.path[1:] if parsed.path else 'Not specified'}")

            db_pool = await aiomysql.create_pool(
                host=parsed.hostname,
                port=parsed.port,
                user=parsed.username,
                password=parsed.password,
                db=parsed.path[1:],  # Remove leading '/'
                ssl={'ssl': True} if 'ssl-mode=REQUIRED' in DATABASE_URL else None,
                autocommit=True,
                minsize=1,
                maxsize=10,
                connect_timeout=30
            )

            # Test the connection
            logger.debug("🧪 Testing database connection...")
            async with db_pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT 1")
                    result = await cursor.fetchone()
                    logger.debug(f"✅ Database test query result: {result}")

            # Create tables
            await create_tables()
            logger.info("🎉 Database connection established successfully!")
            return True

        except Exception as e:
            retry_count += 1
            logger.error(f"❌ Database connection error (attempt {retry_count}): {str(e)}")

            if retry_count < max_retries:
                logger.warning(f"⏳ Retrying database connection in 5 seconds...")
                await asyncio.sleep(5)
            else:
                logger.error("💀 Failed to establish database connection after all retries!")
                db_pool = None
                return False

async def create_tables():
    """Create necessary tables"""
    global db_pool
    
    logger.info("📋 Creating/verifying database tables...")
    
    if not db_pool:
        logger.warning("⚠️ Database pool not available for table creation")
        return

    try:
        async with db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                logger.debug("🏗️ Creating nemu_knowledge table...")
                # Nemu's knowledge base
                await cursor.execute("""
                    CREATE TABLE IF NOT EXISTS nemu_knowledge (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        chat_id BIGINT NOT NULL,
                        trigger_message TEXT NOT NULL,
                        response TEXT NOT NULL,
                        taught_by_user_id BIGINT NOT NULL,
                        taught_by_username VARCHAR(255),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        usage_count INT DEFAULT 0,
                        INDEX idx_chat_trigger (chat_id, trigger_message(100)),
                        FULLTEXT idx_message_fulltext (trigger_message, response)
                    )
                """)
                logger.debug("✅ nemu_knowledge table created/verified")

                logger.debug("🏗️ Creating nemu_interactions table...")
                # User interactions with Nemu
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

def contains_nemu_trigger(text: str) -> bool:
    """Check if message contains Nemu trigger word"""
    if not text:
        logger.debug("🔍 No text provided for trigger check")
        return False

    # Case-insensitive check for "nemu" as whole word or part of word
    text_lower = text.lower()
    contains_trigger = "nemu" in text_lower
    
    logger.debug(f"🔍 Trigger check for '{text[:50]}...': {'✅ Found' if contains_trigger else '❌ Not found'}")
    return contains_trigger

def extract_query_from_nemu_message(text: str) -> str:
    """Extract the actual query from a message containing Nemu"""
    original_text = text
    
    # Remove "nemu" and common prefixes/suffixes to get the actual question
    text = re.sub(r'\bnemu\b', '', text, flags=re.IGNORECASE).strip()
    text = re.sub(r'^[,\s]*', '', text)  # Remove leading commas and spaces
    text = re.sub(r'[,\s]*$', '', text)  # Remove trailing commas and spaces

    extracted_query = text.strip()
    logger.debug(f"🔤 Query extraction: '{original_text}' -> '{extracted_query}'")
    
    return extracted_query

async def learn_from_reply(chat_id: int, user_id: int, username: str, original_query: str, teaching_response: str):
    """Learn from user's reply to Nemu's learning request"""
    global db_pool

    logger.info(f"🎓 Learning attempt - User: {username} ({user_id}), Query: '{original_query}', Response: '{teaching_response[:50]}...'")

    if not db_pool:
        logger.warning("⚠️ Database not available for learning")
        return "failed"

    try:
        async with db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                logger.debug(f"🔍 Checking for existing knowledge for query: '{original_query}'")
                # Check if similar knowledge already exists
                await cursor.execute("""
                    SELECT id, response FROM nemu_knowledge 
                    WHERE chat_id = %s AND LOWER(trigger_message) = LOWER(%s)
                """, (chat_id, original_query))

                existing = await cursor.fetchone()

                if existing:
                    logger.info(f"🔄 Updating existing knowledge (ID: {existing[0]})")
                    # Update existing knowledge
                    await cursor.execute("""
                        UPDATE nemu_knowledge 
                        SET response = %s, taught_by_user_id = %s, taught_by_username = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (teaching_response, user_id, username, existing[0]))
                    action = "updated"
                else:
                    logger.info("➕ Adding new knowledge entry")
                    # Add new knowledge
                    await cursor.execute("""
                        INSERT INTO nemu_knowledge (chat_id, trigger_message, response, taught_by_user_id, taught_by_username)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (chat_id, original_query, teaching_response, user_id, username))
                    action = "learned"

                logger.debug(f"📊 Updating user interaction stats for user {user_id}")
                # Update user stats
                await cursor.execute("""
                    INSERT INTO nemu_interactions (user_id, username, times_taught_nemu)
                    VALUES (%s, %s, 1)
                    ON DUPLICATE KEY UPDATE
                    username = VALUES(username),
                    times_taught_nemu = times_taught_nemu + 1,
                    last_interaction = CURRENT_TIMESTAMP
                """, (user_id, username))

                logger.info(f"✅ Learning successful: {action}")
                return action
    except Exception as e:
        logger.error(f"❌ Error learning from reply: {str(e)}")
        return "failed"

async def find_nemu_response(chat_id: int, query: str) -> Optional[str]:
    """Find response from Nemu's knowledge base"""
    global db_pool

    logger.debug(f"🔍 Searching for response to query: '{query}' in chat {chat_id}")

    if not db_pool or not query.strip():
        logger.warning("⚠️ Database unavailable or empty query")
        return None

    try:
        async with db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                logger.debug("🎯 Attempting exact match search")
                # Try exact match first
                await cursor.execute("""
                    SELECT response, id FROM nemu_knowledge 
                    WHERE chat_id = %s AND LOWER(trigger_message) = LOWER(%s)
                    ORDER BY usage_count DESC, updated_at DESC
                    LIMIT 1
                """, (chat_id, query))

                result = await cursor.fetchone()

                if result and result[0]:
                    logger.info(f"✅ Exact match found (ID: {result[1]}), updating usage count")
                    # Update usage count
                    await cursor.execute("""
                        UPDATE nemu_knowledge SET usage_count = usage_count + 1 
                        WHERE id = %s
                    """, (result[1],))
                    return result[0]

                logger.debug("🔎 Exact match not found, trying fulltext search")
                # Try fulltext search for similar content
                if len(query.split()) >= 2:
                    await cursor.execute("""
                        SELECT response, id,
                        MATCH(trigger_message) AGAINST(%s IN NATURAL LANGUAGE MODE) as relevance
                        FROM nemu_knowledge 
                        WHERE chat_id = %s 
                        AND MATCH(trigger_message) AGAINST(%s IN NATURAL LANGUAGE MODE) > 0.3
                        ORDER BY relevance DESC, usage_count DESC
                        LIMIT 1
                    """, (query, chat_id, query))

                    result = await cursor.fetchone()

                    if result and result[0]:
                        logger.info(f"✅ Fulltext match found (ID: {result[1]}, relevance: {result[2]:.2f})")
                        # Update usage count
                        await cursor.execute("""
                            UPDATE nemu_knowledge SET usage_count = usage_count + 1 
                            WHERE id = %s
                        """, (result[1],))
                        return result[0]

                logger.debug("🔍 Fulltext search failed, trying partial matching")
                # Try partial matching
                await cursor.execute("""
                    SELECT response, id FROM nemu_knowledge 
                    WHERE chat_id = %s 
                    AND (LOWER(trigger_message) LIKE CONCAT('%%', LOWER(%s), '%%') 
                    OR LOWER(%s) LIKE CONCAT('%%', LOWER(trigger_message), '%%'))
                    ORDER BY usage_count DESC, updated_at DESC
                    LIMIT 1
                """, (chat_id, query, query))

                result = await cursor.fetchone()

                if result and result[0]:
                    logger.info(f"✅ Partial match found (ID: {result[1]})")
                    # Update usage count
                    await cursor.execute("""
                        UPDATE nemu_knowledge SET usage_count = usage_count + 1 
                        WHERE id = %s
                    """, (result[1],))
                    return result[0]
                    
                logger.debug("❌ No matches found in knowledge base")
    except Exception as e:
        logger.error(f"❌ Error finding response: {str(e)}")

    return None

async def update_user_interaction(user_id: int, username: str = None, first_name: str = None, helped_by_nemu: bool = False):
    """Update user interaction statistics"""
    global db_pool

    logger.debug(f"📊 Updating interaction stats for user {user_id} ({username})")

    if not db_pool:
        logger.warning("⚠️ Database unavailable for user interaction update")
        return

    try:
        async with db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                helped_count = 1 if helped_by_nemu else 0

                await cursor.execute("""
                    INSERT INTO nemu_interactions (user_id, username, first_name, total_messages, times_helped_by_nemu)
                    VALUES (%s, %s, %s, 1, %s)
                    ON DUPLICATE KEY UPDATE
                    username = VALUES(username),
                    first_name = VALUES(first_name),
                    total_messages = total_messages + 1,
                    times_helped_by_nemu = times_helped_by_nemu + VALUES(times_helped_by_nemu),
                    last_interaction = CURRENT_TIMESTAMP
                """, (user_id, username, first_name, helped_count))
                
                logger.debug(f"✅ User interaction updated (helped: {helped_by_nemu})")
    except Exception as e:
        logger.error(f"❌ Error updating user interaction: {str(e)}")

async def setup_commands():
    """Setup bot commands menu"""
    logger.info("⚙️ Setting up bot commands menu...")
    
    try:
        commands = [
            BotCommand(command="start", description="🚀 Meet Nemu"),
            BotCommand(command="help", description="❓ Learn about Nemu"),
        ]

        await bot.set_my_commands(commands, BotCommandScopeDefault())
        logger.info("✅ Bot commands menu set up successfully")
    except Exception as e:
        logger.error(f"❌ Failed to setup commands: {str(e)}")

@dp.message(CommandStart())
async def start_command(message: Message):
    """Handle /start command"""
    user_info = extract_user_info(message)
    log_with_user_info("INFO", "🚀 /start command triggered", user_info)
    
    try:
        user = message.from_user

        # Update user stats
        await update_user_interaction(user.id, user.username, user.first_name)

        # Create inline keyboard
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="📢 Updates", url="https://t.me/WorkGlows"),
            InlineKeyboardButton(text="💬 Support", url="https://t.me/SoulMeetsHQ")
        )

        # Get bot info for group add link
        bot_info = await bot.get_me()
        group_add_url = f"https://t.me/{bot_info.username}?startgroup=true"
        builder.row(
            InlineKeyboardButton(text="➕ Add Me To Your Group", url=group_add_url)
        )

        # Random image
        random_image = random.choice(IMAGES)
        logger.debug(f"🎲 Selected random image: {random_image}")

        welcome_text = f"""🎉 <b>Hi {user.first_name}! I'm Nemu!</b>

🤖 I'm a learning bot that gets smarter through conversations!

<b>How to interact with me:</b>
💬 <b>In groups:</b> Mention "Nemu" in your message
🗣️ <b>In private:</b> Just chat normally
📚 <b>To teach me:</b> Reply to my "I don't know" messages

<b>What makes me special:</b>
🧠 I learn from every conversation
💾 I remember what you teach me
🎯 I get smarter with each interaction
🌟 I help others using what you taught me

<b>Example:</b>
You: "Nemu, what is Python?"
Me: "I don't know that yet. Can you teach me?"
You: [Reply] "Python is a programming language"
Me: "Thanks! I learned something new! 🧠✨"

Start chatting with me! Mention my name in groups or just talk in private! 💕"""

        await message.answer_photo(
            photo=random_image,
            caption=welcome_text,
            reply_markup=builder.as_markup(),
            parse_mode=ParseMode.HTML
        )
        
        log_with_user_info("INFO", "✅ /start command completed successfully", user_info)
        
    except Exception as e:
        logger.error(f"❌ Error in start command: {str(e)}")
        log_with_user_info("ERROR", f"❌ /start command failed: {str(e)}", user_info)

@dp.message(Command("help"))
async def help_command(message: Message):
    """Handle /help command with expand/minimize functionality"""
    user_info = extract_user_info(message)
    log_with_user_info("INFO", "❓ /help command triggered", user_info)
    
    try:
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="📖 Expand Help", callback_data="help_expand"))

        await message.answer(
            HELP_SHORT,
            reply_markup=builder.as_markup(),
            parse_mode=ParseMode.HTML
        )
        
        log_with_user_info("INFO", "✅ /help command completed successfully", user_info)
        
    except Exception as e:
        logger.error(f"❌ Error in help command: {str(e)}")
        log_with_user_info("ERROR", f"❌ /help command failed: {str(e)}", user_info)

@dp.callback_query(F.data == "help_expand")
async def expand_help(callback: CallbackQuery):
    """Expand help information"""
    user_info = extract_user_info(callback.message)
    log_with_user_info("INFO", "📖 Help expand callback triggered", user_info)
    
    try:
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="📕 Minimize Help", callback_data="help_minimize"))

        await callback.message.edit_text(
            HELP_LONG,
            reply_markup=builder.as_markup(),
            parse_mode=ParseMode.HTML
        )
        await callback.answer()
        
        log_with_user_info("INFO", "✅ Help expanded successfully", user_info)
        
    except Exception as e:
        logger.error(f"❌ Error expanding help: {str(e)}")
        log_with_user_info("ERROR", f"❌ Help expand failed: {str(e)}", user_info)

@dp.callback_query(F.data == "help_minimize")
async def minimize_help(callback: CallbackQuery):
    """Minimize help information"""
    user_info = extract_user_info(callback.message)
    log_with_user_info("INFO", "📕 Help minimize callback triggered", user_info)
    
    try:
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="📖 Expand Help", callback_data="help_expand"))

        await callback.message.edit_text(
            HELP_SHORT,
            reply_markup=builder.as_markup(),
            parse_mode=ParseMode.HTML
        )
        await callback.answer()
        
        log_with_user_info("INFO", "✅ Help minimized successfully", user_info)
        
    except Exception as e:
        logger.error(f"❌ Error minimizing help: {str(e)}")
        log_with_user_info("ERROR", f"❌ Help minimize failed: {str(e)}", user_info)

@dp.message(Command("ping"))
async def ping_command(message: Message):
    """Handle /ping command"""
    user_info = extract_user_info(message)
    log_with_user_info("INFO", "🏓 /ping command triggered", user_info)
    
    try:
        start_time = time.time()

        # Send initial ping message
        if message.chat.type == ChatType.PRIVATE:
            ping_msg = await message.answer("🛰️ Pinging...")
        else:
            ping_msg = await message.reply("🛰️ Pinging...")

        # Calculate ping time
        end_time = time.time()
        ping_time = round((end_time - start_time) * 1000, 2)

        logger.debug(f"🏓 Ping calculated: {ping_time}ms")

        # Edit message with pong result
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

@dp.message()
async def handle_nemu_conversation(message: Message):
    """Handle Nemu's conversations and learning"""
    if not message.text:
        logger.debug("📝 Ignoring non-text message")
        return

    user_info = extract_user_info(message)
    user_id = message.from_user.id
    chat_id = message.chat.id
    text = message.text.strip()
    user = message.from_user

    log_with_user_info("DEBUG", f"📨 Processing message: '{text[:100]}...'", user_info)

    try:
        # Check if this is a reply to Nemu's learning request
        if message.reply_to_message and message.reply_to_message.message_id in learning_requests:
            original_query = learning_requests[message.reply_to_message.message_id]
            
            log_with_user_info("INFO", f"🎓 User teaching Nemu - Query: '{original_query}', Teaching: '{text[:50]}...'", user_info)

            # Learn from the reply
            action = await learn_from_reply(chat_id, user_id, user.username or user.first_name, original_query, text)

            # Remove from learning requests
            del learning_requests[message.reply_to_message.message_id]
            logger.debug(f"🗑️ Removed learning request for message ID: {message.reply_to_message.message_id}")

            # Thank the user for teaching
            thank_messages = [
                f"Thanks {user.first_name}! I {action} something new! 🧠✨",
                f"Awesome {user.first_name}! I've {action} that. Thanks for teaching me! 💕",
                f"Great! I {action} that information. Thank you {user.first_name}! 🎉",
                f"Perfect! I've {action} that knowledge. Thanks for helping me learn! 🌟"
            ]

            selected_message = random.choice(thank_messages)
            logger.debug(f"💬 Selected thank you message: '{selected_message}'")

            response_msg = await message.reply(selected_message, parse_mode=ParseMode.HTML)
            bot_messages[response_msg.message_id] = True

            log_with_user_info("INFO", f"✅ Learning completed: {action}", user_info)
            return

        # Check if this is a reply to any of Nemu's messages
        if message.reply_to_message and message.reply_to_message.message_id in bot_messages:
            # This is a reply to Nemu, so respond regardless of trigger word
            should_respond = True
            query = text
            log_with_user_info("DEBUG", "🔄 Reply to Nemu detected, responding", user_info)
        else:
            # In groups, only respond if "nemu" is mentioned
            if message.chat.type != ChatType.PRIVATE:
                if not contains_nemu_trigger(text):
                    logger.debug("🚫 No Nemu trigger found in group message")
                    return
                should_respond = True
                query = extract_query_from_nemu_message(text)
                log_with_user_info("DEBUG", f"🎯 Nemu trigger found in group, query: '{query}'", user_info)
            else:
                # In private chat, always respond
                should_respond = True
                query = text
                log_with_user_info("DEBUG", "💬 Private chat message, responding", user_info)

        if not should_respond:
            logger.debug("🚫 Should not respond to this message")
            return

        # Update user interaction stats
        await update_user_interaction(user_id, user.username, user.first_name)

        # Skip if query is too short or empty
        if not query or len(query.strip()) < 2:
            log_with_user_info("WARNING", f"⚠️ Query too short or empty: '{query}'", user_info)
            return

        # Try to find a response
        logger.debug(f"🔍 Searching knowledge base for query: '{query}'")
        response = await find_nemu_response(chat_id, query)

        if response:
            # Nemu knows the answer!
            log_with_user_info("INFO", f"🧠 Knowledge found, responding: '{response[:50]}...'", user_info)
            await update_user_interaction(user_id, user.username, user.first_name, helped_by_nemu=True)

            # Add some personality to responses occasionally
            if random.random() < 0.1:  # 10% chance
                personality_prefixes = [
                    "😊 ",
                    "✨ ",
                    "🌟 ",
                    "💫 "
                ]
                personality_prefix = random.choice(personality_prefixes)
                response = personality_prefix + response
                logger.debug(f"✨ Added personality prefix: '{personality_prefix}'")

            response_msg = await message.reply(response, parse_mode=ParseMode.HTML)
            bot_messages[response_msg.message_id] = True

            log_with_user_info("INFO", "✅ Response sent successfully", user_info)

        else:
            # Nemu doesn't know - ask for teaching
            log_with_user_info("INFO", f"❓ No knowledge found, requesting teaching for: '{query}'", user_info)
            
            learning_messages = [
                f"I don't know that yet. Can you teach me? 🤔",
                f"Hmm, I haven't learned about that. Can you help me learn? 📚",
                f"I'm not sure about that. Could you teach me? 🧠",
                f"That's new to me! Can you explain it to me? ✨",
                f"I don't have that information yet. Would you like to teach me? 💭"
            ]

            learning_response = random.choice(learning_messages)
            logger.debug(f"📚 Selected learning request: '{learning_response}'")
            
            response_msg = await message.reply(learning_response, parse_mode=ParseMode.HTML)

            # Store this as a learning request
            learning_requests[response_msg.message_id] = query
            bot_messages[response_msg.message_id] = True
            
            logger.debug(f"📝 Stored learning request - Message ID: {response_msg.message_id}, Query: '{query}'")

            # Clean up old learning requests (keep only last 100)
            if len(learning_requests) > 100:
                oldest_keys = list(learning_requests.keys())[:-100]
                for key in oldest_keys:
                    del learning_requests[key]
                logger.debug(f"🧹 Cleaned up {len(oldest_keys)} old learning requests")

            # Clean up old bot message tracking
            if len(bot_messages) > 200:
                oldest_keys = list(bot_messages.keys())[:-200]
                for key in oldest_keys:
                    del bot_messages[key]
                logger.debug(f"🧹 Cleaned up {len(oldest_keys)} old bot message tracking entries")

            log_with_user_info("INFO", "✅ Learning request sent successfully", user_info)

    except Exception as e:
        logger.error(f"❌ Error in conversation handler: {str(e)}")
        log_with_user_info("ERROR", f"❌ Conversation handling failed: {str(e)}", user_info)
        
        try:
            # Send error message to user
            await message.reply("😅 Sorry, I encountered an error. Please try again!")
        except Exception as reply_error:
            logger.error(f"❌ Failed to send error message to user: {str(reply_error)}")

async def main():
    """Main function to run the bot"""
    logger.info("🚀 Nemu initialization started...")

    try:
        # Initialize database with retry logic
        logger.info("🗄️ Initializing database...")
        db_success = await init_database()

        if not db_success:
            logger.warning("⚠️ Starting Nemu without database connection!")
            logger.warning("⚠️ Nemu will work with limited functionality (no learning/memory)")

        # Setup commands menu
        logger.info("⚙️ Setting up commands...")
        await setup_commands()

        logger.info("🎉 Nemu is ready and starting polling...")

        # Start polling
        await dp.start_polling(bot)
        
    except KeyboardInterrupt:
        logger.info("⏹️ Received interrupt signal, shutting down...")
    except Exception as e:
        logger.error(f"💀 Critical error in main: {str(e)}")
        raise
    finally:
        logger.info("🔧 Cleaning up resources...")
        if db_pool:
            try:
                db_pool.close()
                await db_pool.wait_closed()
                logger.info("✅ Database pool closed successfully")
            except Exception as e:
                logger.error(f"❌ Error closing database pool: {str(e)}")
        
        logger.info("👋 Nemu shutdown complete")

if __name__ == "__main__":
    try:
        logger.info("=" * 50)
        logger.info("🤖 NEMU BOT STARTING UP")
        logger.info("=" * 50)
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⏹️ Bot stopped by user")
    except Exception as e:
        logger.error(f"💀 Fatal error: {str(e)}")
        raise