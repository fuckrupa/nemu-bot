import asyncio
import os
import random
import time
import re
import threading
from datetime import datetime
from typing import Optional
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

# Environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
DATABASE_URL = os.getenv("DATABASE_URL", "")

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

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Database connection pool
db_pool = None

# Help messages
HELP_SHORT = "🤖 Hi! I'm <b>Nemu</b>, a learning bot!\n\n💬 In groups, mention \"Nemu\" in your message to talk with me\n📚 I learn from conversations when you teach me by replying to my messages\n🧠 I remember everything you teach me and use it to help others\n\n✨ Just mention my name and chat naturally - I'll learn as we go!"

HELP_LONG = "🤖 <b>Meet Nemu - Your Learning Companion</b>\n\n<b>How to interact with me:</b>\n• In groups: Include \"Nemu\" in your message\n• In private: Just send messages normally\n• Reply to my messages to teach me new things\n\n<b>How I learn:</b>\n🧠 When I don't know something, I'll ask you to teach me\n📝 Reply to my \"I don't know\" messages to teach me\n💾 I remember everything and use it to help others\n🎯 I get smarter with every interaction\n\n<b>Commands Available:</b>\n/start - Meet me and see what I can do\n/help - Toggle this help information\n\n<b>Pro Tips:</b>\n• Teach me by replying when I ask\n• I work great in group conversations\n• The more you teach me, the smarter I become!"

# Nemu's learning requests - store message IDs waiting for teaching
learning_requests = {}

# Bot's own message tracking for replies
bot_messages = {}

# HTTP SERVER FOR DEPLOYMENT
class DummyHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for keep-alive server"""

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Nemu bot is alive!")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        # Suppress HTTP server logs
        pass

def start_dummy_server() -> None:
    """Start dummy HTTP server for deployment platforms"""
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), DummyHandler)
    print(f"🌐 Dummy server listening on port {port}")
    server.serve_forever()

# Start HTTP server in background thread
threading.Thread(target=start_dummy_server, daemon=True).start()

async def init_database():
    """Initialize database connection pool"""
    global db_pool
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Parse DATABASE_URL
            import urllib.parse as urlparse
            parsed = urlparse.urlparse(DATABASE_URL)
            
            print(f"Attempting to connect to database (attempt {retry_count + 1}/{max_retries})...")
            
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
            async with db_pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT 1")
            
            # Create tables
            await create_tables()
            print("Nemu's database connection established successfully!")
            return True
            
        except Exception as e:
            retry_count += 1
            print(f"Database connection error (attempt {retry_count}): {e}")
            
            if retry_count < max_retries:
                print(f"Retrying in 5 seconds...")
                await asyncio.sleep(5)
            else:
                print("Failed to establish database connection after all retries!")
                db_pool = None
                return False

async def create_tables():
    """Create necessary tables"""
    global db_pool
    if not db_pool:
        print("Warning: Database pool not available for table creation")
        return
        
    try:
        async with db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
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
                print("Database tables created/verified successfully!")
    except Exception as e:
        print(f"Error creating tables: {e}")

def contains_nemu_trigger(text: str) -> bool:
    """Check if message contains Nemu trigger word"""
    if not text:
        return False
    
    # Case-insensitive check for "nemu" as whole word or part of word
    text_lower = text.lower()
    return "nemu" in text_lower

def extract_query_from_nemu_message(text: str) -> str:
    """Extract the actual query from a message containing Nemu"""
    # Remove "nemu" and common prefixes/suffixes to get the actual question
    text = re.sub(r'\bnemu\b', '', text, flags=re.IGNORECASE).strip()
    text = re.sub(r'^[,\s]*', '', text)  # Remove leading commas and spaces
    text = re.sub(r'[,\s]*$', '', text)  # Remove trailing commas and spaces
    
    return text.strip()

async def learn_from_reply(chat_id: int, user_id: int, username: str, original_query: str, teaching_response: str):
    """Learn from user's reply to Nemu's learning request"""
    global db_pool
    
    if not db_pool:
        print("Warning: Database not available for learning")
        return "failed"
    
    try:
        async with db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Check if similar knowledge already exists
                await cursor.execute("""
                    SELECT id, response FROM nemu_knowledge 
                    WHERE chat_id = %s AND LOWER(trigger_message) = LOWER(%s)
                """, (chat_id, original_query))
                
                existing = await cursor.fetchone()
                
                if existing:
                    # Update existing knowledge
                    await cursor.execute("""
                        UPDATE nemu_knowledge 
                        SET response = %s, taught_by_user_id = %s, taught_by_username = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (teaching_response, user_id, username, existing[0]))
                    action = "updated"
                else:
                    # Add new knowledge
                    await cursor.execute("""
                        INSERT INTO nemu_knowledge (chat_id, trigger_message, response, taught_by_user_id, taught_by_username)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (chat_id, original_query, teaching_response, user_id, username))
                    action = "learned"
                
                # Update user stats
                await cursor.execute("""
                    INSERT INTO nemu_interactions (user_id, username, times_taught_nemu)
                    VALUES (%s, %s, 1)
                    ON DUPLICATE KEY UPDATE
                    username = VALUES(username),
                    times_taught_nemu = times_taught_nemu + 1,
                    last_interaction = CURRENT_TIMESTAMP
                """, (user_id, username))
                
                return action
    except Exception as e:
        print(f"Error learning from reply: {e}")
        return "failed"

async def find_nemu_response(chat_id: int, query: str) -> Optional[str]:
    """Find response from Nemu's knowledge base"""
    global db_pool
    
    if not db_pool or not query.strip():
        return None
    
    try:
        async with db_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Try exact match first
                await cursor.execute("""
                    SELECT response, id FROM nemu_knowledge 
                    WHERE chat_id = %s AND LOWER(trigger_message) = LOWER(%s)
                    ORDER BY usage_count DESC, updated_at DESC
                    LIMIT 1
                """, (chat_id, query))
                
                result = await cursor.fetchone()
                
                if result and result[0]:
                    # Update usage count
                    await cursor.execute("""
                        UPDATE nemu_knowledge SET usage_count = usage_count + 1 
                        WHERE id = %s
                    """, (result[1],))
                    return result[0]
                
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
                        # Update usage count
                        await cursor.execute("""
                            UPDATE nemu_knowledge SET usage_count = usage_count + 1 
                            WHERE id = %s
                        """, (result[1],))
                        return result[0]
                
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
                    # Update usage count
                    await cursor.execute("""
                        UPDATE nemu_knowledge SET usage_count = usage_count + 1 
                        WHERE id = %s
                    """, (result[1],))
                    return result[0]
    except Exception as e:
        print(f"Error finding response: {e}")
    
    return None

async def update_user_interaction(user_id: int, username: str = None, first_name: str = None, helped_by_nemu: bool = False):
    """Update user interaction statistics"""
    global db_pool
    
    if not db_pool:
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
    except Exception as e:
        print(f"Error updating user interaction: {e}")

async def setup_commands():
    """Setup bot commands menu"""
    commands = [
        BotCommand(command="start", description="🚀 Meet Nemu"),
        BotCommand(command="help", description="❓ Learn about Nemu"),
    ]
    
    await bot.set_my_commands(commands, BotCommandScopeDefault())

@dp.message(CommandStart())
async def start_command(message: Message):
    """Handle /start command"""
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

@dp.message(Command("help"))
async def help_command(message: Message):
    """Handle /help command with expand/minimize functionality"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📖 Expand Help", callback_data="help_expand"))
    
    await message.answer(
        HELP_SHORT,
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.HTML
    )

@dp.callback_query(F.data == "help_expand")
async def expand_help(callback: CallbackQuery):
    """Expand help information"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📕 Minimize Help", callback_data="help_minimize"))
    
    await callback.message.edit_text(
        HELP_LONG,
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.HTML
    )
    await callback.answer()

@dp.callback_query(F.data == "help_minimize")
async def minimize_help(callback: CallbackQuery):
    """Minimize help information"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📖 Expand Help", callback_data="help_expand"))
    
    await callback.message.edit_text(
        HELP_SHORT,
        reply_markup=builder.as_markup(),
        parse_mode=ParseMode.HTML
    )
    await callback.answer()

@dp.message(Command("ping"))
async def ping_command(message: Message):
    """Handle /ping command"""
    start_time = time.time()
    
    # Send initial ping message
    if message.chat.type == ChatType.PRIVATE:
        ping_msg = await message.answer("🛰️ Pinging...")
    else:
        ping_msg = await message.reply("🛰️ Pinging...")
    
    # Calculate ping time
    end_time = time.time()
    ping_time = round((end_time - start_time) * 1000, 2)
    
    # Edit message with pong result
    pong_text = f'🏓 <a href="https://t.me/SoulMeetsHQ">Pong!</a> {ping_time}ms'
    
    await ping_msg.edit_text(
        pong_text,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )

@dp.message()
async def handle_nemu_conversation(message: Message):
    """Handle Nemu's conversations and learning"""
    if not message.text:
        return
    
    user_id = message.from_user.id
    chat_id = message.chat.id
    text = message.text.strip()
    user = message.from_user
    
    # Check if this is a reply to Nemu's learning request
    if message.reply_to_message and message.reply_to_message.message_id in learning_requests:
        original_query = learning_requests[message.reply_to_message.message_id]
        
        # Learn from the reply
        action = await learn_from_reply(chat_id, user_id, user.username or user.first_name, original_query, text)
        
        # Remove from learning requests
        del learning_requests[message.reply_to_message.message_id]
        
        # Thank the user for teaching
        thank_messages = [
            f"Thanks {user.first_name}! I {action} something new! 🧠✨",
            f"Awesome {user.first_name}! I've {action} that. Thanks for teaching me! 💕",
            f"Great! I {action} that information. Thank you {user.first_name}! 🎉",
            f"Perfect! I've {action} that knowledge. Thanks for helping me learn! 🌟"
        ]
        
        response_msg = await message.reply(random.choice(thank_messages), parse_mode=ParseMode.HTML)
        bot_messages[response_msg.message_id] = True
        
        return
    
    # Check if this is a reply to any of Nemu's messages
    if message.reply_to_message and message.reply_to_message.message_id in bot_messages:
        # This is a reply to Nemu, so respond regardless of trigger word
        should_respond = True
        query = text
    else:
        # In groups, only respond if "nemu" is mentioned
        if message.chat.type != ChatType.PRIVATE:
            if not contains_nemu_trigger(text):
                return
            should_respond = True
            query = extract_query_from_nemu_message(text)
        else:
            # In private chat, always respond
            should_respond = True
            query = text
    
    if not should_respond:
        return
    
    # Update user interaction stats
    await update_user_interaction(user_id, user.username, user.first_name)
    
    # Skip if query is too short or empty
    if not query or len(query.strip()) < 2:
        return
    
    # Try to find a response
    response = await find_nemu_response(chat_id, query)
    
    if response:
        # Nemu knows the answer!
        await update_user_interaction(user_id, user.username, user.first_name, helped_by_nemu=True)
        
        # Add some personality to responses occasionally
        if random.random() < 0.1:  # 10% chance
            personality_prefixes = [
                "😊 ",
                "✨ ",
                "🌟 ",
                "💫 "
            ]
            response = random.choice(personality_prefixes) + response
        
        response_msg = await message.reply(response, parse_mode=ParseMode.HTML)
        bot_messages[response_msg.message_id] = True
        
    else:
        # Nemu doesn't know - ask for teaching
        learning_messages = [
            f"I don't know that yet. Can you teach me? 🤔",
            f"Hmm, I haven't learned about that. Can you help me learn? 📚",
            f"I'm not sure about that. Could you teach me? 🧠",
            f"That's new to me! Can you explain it to me? ✨",
            f"I don't have that information yet. Would you like to teach me? 💭"
        ]
        
        learning_response = random.choice(learning_messages)
        response_msg = await message.reply(learning_response, parse_mode=ParseMode.HTML)
        
        # Store this as a learning request
        learning_requests[response_msg.message_id] = query
        bot_messages[response_msg.message_id] = True
        
        # Clean up old learning requests (keep only last 100)
        if len(learning_requests) > 100:
            oldest_keys = list(learning_requests.keys())[:-100]
            for key in oldest_keys:
                del learning_requests[key]
        
        # Clean up old bot message tracking
        if len(bot_messages) > 200:
            oldest_keys = list(bot_messages.keys())[:-200]
            for key in oldest_keys:
                del bot_messages[key]

async def main():
    """Main function to run the bot"""
    print("Initializing Nemu...")
    
    # Initialize database with retry logic
    db_success = await init_database()
    
    if not db_success:
        print("WARNING: Starting Nemu without database connection!")
        print("Nemu will work with limited functionality (no learning/memory)")
    
    # Setup commands menu
    await setup_commands()
    
    print("Nemu is starting...")
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        print(f"Nemu error: {e}")
    finally:
        if db_pool:
            db_pool.close()
            await db_pool.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())