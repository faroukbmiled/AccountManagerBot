#!/usr/bin/env python3
"""Telegram bot by AX_Ryuk"""
import logging
import os
from functools import wraps
from telegram.ext import CallbackContext
from telegram import __version__ as TG_VER
import time

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This Bot is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this Bot, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )
from telegram import ForceReply, Update, InputFile
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

ALLOWED_USER_ID = int("USERID")
FILE_NAME = "result.txt"
BOT_TOKEN = "BOTTOKEN"
ENCODING = "utf-8"

# admin checker => used as a decorator
def admin_only(func):
    @wraps(func)
    async def wrapper(update: Update, context: CallbackContext):
        user = update.effective_user
        if user.id == ALLOWED_USER_ID:
            return await func(update, context)
        else:
            await update.message.reply_text("You are not authorized to use this command.")
    return wrapper

# arguments checker => used as a decorator
def argument_required(func):
    @wraps(func)
    async def wrapper(update: Update, context: CallbackContext):
        query = ' '.join(update.message.text.split()[1:])
        if not query or '\n' in query:
            await update.message.reply_text("Please provide the correct argument, use /help for more info")
        else:
            return await func(update, context)
    return wrapper

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user

    await update.message.reply_html(f"Hi {user.mention_html()}!, Bot created by Ryuk!\nUse /help to check current available commands",)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    command_list = [
        ("/start", "", "Start the bot and get a welcome message."),
        ("/help or /h", "", "Display all available commands and their usage."),
        ("/find [query]", "-> Specify a search query", "Search for credentials based on a query and display them in Username Password format."),
        ("/findraw [query]", "-> Specify a search query", "Search for credentials based on a query and display them in raw format."),
        ("/update or /up", "", "Combine or update all text files in the current directory."),
        ("/downloadall or /dla", "", "Download all credentials as a file."),
        ("/download or /dl [query]", "-> Specify a search query", "Download all found credentials for a query as a file."),
        ("/downloadfile or /dlf [file_name]", "-> Specify a file name", "Download a specific file from the server."),
        ("/ls", "", "List all files in the current directory."),
    ]

    help_text = "Available commands:\n\n"
    for command, arguments, usage in command_list:
        help_text += f"{command} {arguments}\n{usage}\n\n"

    await update.message.reply_text(help_text)

@admin_only
@argument_required
async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process the search command."""
    try:
        query = ' '.join(update.message.text.split()[1:])
        with open(f'{FILE_NAME}', 'r', encoding=f"{ENCODING}") as file:
            data = file.read()

        lines = data.split("\n")
        resultfound = False
        response = []

        for line in lines:
            parts = line.split(":")
            if len(parts) >= 3 and query in parts[1]:
                resultfound = True
                username = parts[2].strip() if len(parts) > 2 and parts[2].strip() != "" else "index has no username"
                password = parts[3].strip() if len(parts) > 3 else "index has no password"
                response.append(f"\nUsername: {username}\nPassword: {password}")

        if resultfound:
            formatted_response = "\n".join(response)
            accounts_count = formatted_response.count("Username")
            message = f"Found {query.capitalize()} accounts [{accounts_count}]:\n{formatted_response}"
            await update.message.reply_text(message)
        else:
            await update.message.reply_text("No credentials found.")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

@admin_only
@argument_required
async def search_command_raw(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process the search command."""
    try:
        query = ' '.join(update.message.text.split()[1:])
        with open(f'{FILE_NAME}', 'r', encoding=f"{ENCODING}") as file:
            data = file.read()

        lines = data.split("\n")
        resultfound = False
        response = []

        for line in lines:
            parts = line.split(":")
            if len(parts) >= 3 and query in parts[1]:
                resultfound = True
                username_password = ":".join(parts[2:4])
                response.append(username_password)

        if resultfound:
            formatted_response = "\n".join(response)
            accounts_count = formatted_response.count("\n") + 1
            message = f"Found {query.capitalize()} accounts [{accounts_count}]:\n{formatted_response}"
            await update.message.reply_text(message)
        else:
            await update.message.reply_text("No credentials found.")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

@admin_only
async def update_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process the update command."""
    try:
        combined_lines = set()

        for file in os.listdir():
            if '.txt' in file:
                with open(file, 'r', encoding=f"{ENCODING}") as file_handle:
                    for line in file_handle:
                        combined_lines.add(line.strip())

        if len(combined_lines) > 0:
            with open(f'{FILE_NAME}', 'w', encoding=f"{ENCODING}") as f:
                for line in combined_lines:
                    f.write(line + '\n')
            await update.message.reply_text("All text files are combined or updated successfully.")
        else:
            await update.message.reply_text("All text files are empty.")

    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

@admin_only
async def downloadall_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process the downloadall command."""
    try:
        file_path = f"{FILE_NAME}"
        with open(file_path, 'rb') as file:
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=InputFile(file),
                filename=f"{FILE_NAME}",
                caption="Download all crediantials."
            )
    except Exception as e:
        update.message.reply_text(f"Error: {e}")

@admin_only
@argument_required
async def download_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process the download command."""
    try:
        query = ' '.join(update.message.text.split()[1:])
        with open(f'{FILE_NAME}', 'r', encoding="utf8") as file:
            data = file.read()

        lines = data.split("\n")
        resultfound = False
        response = []

        for line in lines:
            parts = line.split(":")
            if len(parts) >= 3 and query in parts[1]:
                resultfound = True
                username_password = ":".join(parts[2:4])
                response.append(username_password)

        if resultfound:
            formatted_response = "\n".join(response)
            file_path = f"{query}.txt"
            with open(file_path, 'w', encoding=f"{ENCODING}") as file:
                file.write(formatted_response)

            with open(file_path, 'rb') as file:
                await context.bot.send_document(
                    chat_id=update.effective_chat.id,
                    document=InputFile(file),
                    filename=f"{FILE_NAME}",
                    caption=f"Download all found credentials for {query.capitalize()}"
                )

            cached_file_name = os.path.splitext(file_path)[0]
            max_retries = 5
            retry_delay = 1
            for _ in range(max_retries):
                try:
                    if os.path.exists(cached_file_name):
                        os.remove(cached_file_name)
                    os.rename(file_path, cached_file_name)
                    break
                except OSError as e:
                    if "used by another process" in str(e):
                        time.sleep(retry_delay)
                    else:
                        raise
            else:
                await update.message.reply_text("Failed to rename the file due to it still being used.")
        else:
            await update.message.reply_text("No credentials found.")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

@admin_only
async def ls_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process the ls command to list all files in the current directory."""
    try:
        file_list = os.listdir()
        file_list_formatted = '\n'.join(file_list)
        await update.message.reply_text(f"Files in current directory:\n{file_list_formatted}")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

@admin_only
@argument_required
async def download_file_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process the download command to download a specific file."""
    try:
        query = ' '.join(update.message.text.split()[1:])
        file_path = query

        if os.path.exists(file_path):
            with open(file_path, 'rb') as file:
                await context.bot.send_document(
                    chat_id=update.effective_chat.id,
                    document=InputFile(file),
                    filename=os.path.basename(file_path),
                    caption=f"Download file {query} from server"
                )
        else:
            await update.message.reply_text("File not found, use /ls to see all files.")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

def main() -> None:
    application = Application.builder().token(f"{BOT_TOKEN}").build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler(["help", "h"], help_command))
    application.add_handler(CommandHandler(["find", "f"], search_command))
    application.add_handler(CommandHandler(["findraw", "fr"], search_command_raw))
    application.add_handler(CommandHandler(["update", "up"], update_command))
    application.add_handler(CommandHandler(["downloadall", "dla"], downloadall_command))
    application.add_handler(CommandHandler(["download", "dl"], download_command))
    application.add_handler(CommandHandler(["downloadfile", "dlf"], download_file_name))
    application.add_handler(CommandHandler("ls", ls_command))
    application.run_polling()


if __name__ == "__main__":
    main()
