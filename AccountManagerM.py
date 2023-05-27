#!/usr/bin/env python3
"""Telegram bot by AX_Ryuk"""
import logging
import os
from functools import wraps
from telegram.ext import CallbackContext
from threading import Thread
import codecs
import subprocess
from telegram import __version__ as TG_VER
from io import BytesIO
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
from telegram import ForceReply, Update, InputFile, BotCommand, Bot
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

ALLOWED_USER_ID = int("USERID")
BOT_TOKEN = "BOTTOKEN"
ENCODING = "utf-8"

bot_commands = [
    BotCommand("start", "Start the bot and get a welcome message."),
    BotCommand("help", "Display all available commands and their usage."),
    BotCommand("find", "ex: /find netflix"),
    BotCommand("findraw", "ex: /findraw netflix"),
    BotCommand("download", "ex: /download netflix"),
    BotCommand("downloadfile", "ex: /downloadfile netflix"),
    BotCommand("ls", "List all files in the current directory."),
    BotCommand("remove", "ex: /remove netflix.txt"),
    BotCommand("cmd", "Update the commands button (UI).")
]

# admin checker => used as a decorator
def admin_only(func):
    @wraps(func)
    async def wrapper(update: Update, context: CallbackContext):
        user = update.effective_user
        if user.id == ALLOWED_USER_ID:
            return await func(update, context)
        else:
            await update.message.reply_text("You are not authorized to use this command.", reply_to_message_id=update.message.message_id)
    return wrapper

# arguments checker => used as a decorator
def argument_required(func):
    @wraps(func)
    async def wrapper(update: Update, context: CallbackContext):
        query = ' '.join(update.message.text.split()[1:])
        if not query or '\n' in query:
            await update.message.reply_text("Please provide the correct argument, use /help for more info", reply_to_message_id=update.message.message_id)
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
        ("/find or /f [query]", "-> Specify a search query", "Search for credentials based on a query and display them in Username Password format."),
        ("/findraw or /fr [query]", "-> Specify a search query", "Search for credentials based on a query and display them in raw format."),
        ("/download or /dl [query]", "-> Specify a search query", "Download all found credentials for a query as a file."),
        ("/downloadfile or /dlf [file_name]", "-> Specify a file name", "Download a specific file from the server."),
        ("/ls", "", "List all files in the current directory."),
        ("/rm or /remove [query]", "-> Specify a file name", "delete a specific file names [query]."),
        ("/cmd", "", "Update the commands button (UI)."),
    ]

    help_text = "Available commands:\n\n"
    for command, arguments, usage in command_list:
        help_text += f"{command} {arguments}\n{usage}\n\n"

    await update.message.reply_text(help_text, reply_to_message_id=update.message.message_id)

@admin_only
@argument_required
async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process the search command."""
    try:
        query, *args = update.message.text.split()[1:]
        if len(args) > 0:
            num_lines = int(args[0])
        else:
            num_lines = 20
        filename = f"{query}.txt"

        if not os.path.isfile(filename):
            await update.message.reply_text(f"File {filename} does not exist. Use `/dl {query}` to generate the txt file first.", reply_to_message_id=update.message.message_id)
            return

        await update.message.reply_text(f"Search is being processed, please wait...")

        response = []
        resultfound = False
        lines_processed = 0

        with codecs.open(filename, 'r', encoding=ENCODING, errors='ignore') as file_handle:
            for line in file_handle:
                line = line.strip()
                parts = line.split(":")
                if len(parts) >= 4 and query in parts[1]:
                    resultfound = True
                    username = parts[2].strip() if len(parts) > 2 and parts[2].strip() != "" else "index has no username"
                    password = parts[3].strip() if len(parts) > 3 else "index has no password"
                    response.append(f"\nUsername: {username}\nPassword: {password}")

                    lines_processed += 1
                    if lines_processed == num_lines:
                        break

                    if len(response) == 20:
                        formatted_response = "\n".join(response)
                        accounts_count = formatted_response.count("Username")
                        message = f"Found {query.capitalize()} accounts [{accounts_count}]:\n{formatted_response}"
                        await update.message.reply_text(message, reply_to_message_id=update.message.message_id)

                        response = []

        if resultfound:
            if len(response) > 0:
                formatted_response = "\n".join(response)
                accounts_count = formatted_response.count("Username")
                message = f"Found {query.capitalize()} accounts [{accounts_count}]:\n{formatted_response}"
                await update.message.reply_text(message, reply_to_message_id=update.message.message_id)
        else:
            await update.message.reply_text("No credentials found.", reply_to_message_id=update.message.message_id)
    except Exception as e:
        await update.message.reply_text(f"Error: {e}", reply_to_message_id=update.message.message_id)


@admin_only
@argument_required
async def search_command_raw(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process the search command."""
    try:
        query, *args = update.message.text.split()[1:]
        if len(args) > 0:
            num_lines = int(args[0])
        else:
            num_lines = 20
        filename = f"{query}.txt"

        if not os.path.isfile(filename):
            await update.message.reply_text(f"File {filename} does not exist. Use `/dl {query}` to generate the txt file first.", reply_to_message_id=update.message.message_id)
            return

        await update.message.reply_text(f"Search is being processed, please wait...")

        response = []
        resultfound = False
        lines_processed = 0

        with codecs.open(filename, 'r', encoding=ENCODING, errors='ignore') as file_handle:
            for line in file_handle:
                line = line.strip()
                parts = line.split(":")
                if len(parts) >= 4 and query in parts[1]:
                    resultfound = True
                    username_password = ":".join(parts[2:4])
                    response.append(username_password)

                    lines_processed += 1
                    if lines_processed == num_lines:
                        break

                    if len(response) == 20:
                        formatted_response = "\n".join(response)
                        accounts_count = formatted_response.count("\n") + 1
                        message = f"Found {query.capitalize()} accounts [{accounts_count}]:\n{formatted_response}"
                        await update.message.reply_text(message, reply_to_message_id=update.message.message_id)

                        response = []

        if resultfound:
            if len(response) > 0:
                formatted_response = "\n".join(response)
                accounts_count = formatted_response.count("\n") + 1
                message = f"Found {query.capitalize()} accounts [{accounts_count}]:\n{formatted_response}"
                await update.message.reply_text(message, reply_to_message_id=update.message.message_id)
        else:
            await update.message.reply_text("No credentials found.", reply_to_message_id=update.message.message_id)
    except Exception as e:
        await update.message.reply_text(f"Error: {e}", reply_to_message_id=update.message.message_id)

@admin_only
@argument_required
async def download_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process the download command."""
    try:
        query = ' '.join(update.message.text.split()[1:])
        await update.message.reply_text(f"This may take a while, please wait...")
        try:
            os.remove(f"{query}.txt")
        except:
            pass

        program_path = 'FileFetcher.exe'
        arguments = [program_path, query]

        try:
            process = subprocess.Popen(arguments, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, error = process.communicate()

            output = output.decode()
            error = error.decode()

            output_filename = f"{query}.txt"
            if output:
                if os.path.exists(output_filename):
                    with open(output_filename, 'rb') as file:
                        await update.message.reply_text(f"{output}")
                        if os.path.getsize(output_filename) > 0:
                            await context.bot.send_document(
                                chat_id=update.effective_chat.id,
                                document=file,
                                filename=output_filename,
                                caption=f"Download all found credentials for {query.capitalize()}",
                                reply_to_message_id=update.message.message_id
                            )
                        else:
                            await update.message.reply_text("File is empty. No credentials found.", reply_to_message_id=update.message.message_id)
                            os.remove(f"{query}.txt")
                else:
                    await update.message.reply_text("No credentials found.", reply_to_message_id=update.message.message_id)
            elif error:
                await update.message.reply_text(f"Error: {error}", reply_to_message_id=update.message.message_id)
            else:
                await update.message.reply_text("No output received.", reply_to_message_id=update.message.message_id)

        except Exception as e:
            await update.message.reply_text(f"Error: {e}", reply_to_message_id=update.message.message_id)

    except Exception as e:
        await update.message.reply_text(f"Error: {e}", reply_to_message_id=update.message.message_id)


@admin_only
async def ls_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process the ls command to list all files in the current directory."""
    try:
        file_list = os.listdir()
        file_list_formatted = '\n'.join(file_list)
        await update.message.reply_text(f"Files in current directory:\n{file_list_formatted}",reply_to_message_id=update.message.message_id)
    except Exception as e:
        await update.message.reply_text(f"Error: {e}",reply_to_message_id=update.message.message_id)

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
                    caption=f"Download file {query} from server",
                    reply_to_message_id=update.message.message_id
                )
        else:
            await update.message.reply_text("File not found, use /ls to see all files.",reply_to_message_id=update.message.message_id)
    except Exception as e:
        await update.message.reply_text(f"Error: {e}",reply_to_message_id=update.message.message_id)

@admin_only
@argument_required
async def delete_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process the delete command to delete a specific file."""
    try:
        query = ' '.join(update.message.text.split()[1:])
        file_path = query

        if os.path.exists(file_path):
            os.remove(file_path)
            await update.message.reply_text(f"File '{query}' has been deleted.", reply_to_message_id=update.message.message_id)
        else:
            await update.message.reply_text("File not found, use /ls to see all files.", reply_to_message_id=update.message.message_id)
    except Exception as e:
        await update.message.reply_text(f"Error: {e}", reply_to_message_id=update.message.message_id)

@admin_only
async def cmdbutton_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        bot = Bot(token=BOT_TOKEN)
        await bot.set_my_commands(bot_commands)
        await update.message.reply_text("Coammnds button has been updated!",reply_to_message_id=update.message.message_id)
    except Exception as e:
        await update.message.reply_text(f"Error: {e}",reply_to_message_id=update.message.message_id)

def main() -> None:
    application = Application.builder().token(f"{BOT_TOKEN}").build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler(["help", "h"], help_command))
    application.add_handler(CommandHandler(["find", "f"], search_command))
    application.add_handler(CommandHandler(["findraw", "fr"], search_command_raw))
    application.add_handler(CommandHandler(["download", "dl"], download_command))
    application.add_handler(CommandHandler(["downloadfile", "dlf"], download_file_name))
    application.add_handler(CommandHandler(["remove", "rm"], delete_file))
    application.add_handler(CommandHandler("ls", ls_command))
    application.add_handler(CommandHandler("cmd", cmdbutton_command))
    application.run_polling()


if __name__ == "__main__":
    main()
