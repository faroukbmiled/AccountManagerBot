#!/usr/bin/env python3
"""Telegram bot by AX_Ryuk"""
import logging
import os
import asyncio
import time
import sys
from functools import wraps
import codecs
import random
import subprocess
from telegram import __version__ as TG_VER
import secrets
import string
import json
import psutil
import re

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
from telegram import ReplyKeyboardRemove, Update, InputFile, BotCommand, Bot, error, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, CallbackContext
from telethon.sync import TelegramClient, events
from telethon.tl.types import Channel

# logging.basicConfig(filename='ryukerr.log', level=logging.DEBUG,
#                     format='%(asctime)s %(levelname)s %(name)s %(message)s')
# logger = logging.getLogger(__name__)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)
CURR_DIR = os.path.dirname(os.path.abspath(__file__))

try:
    with open('config.conf', 'r') as configfile:
        lines = configfile.readlines()
except FileNotFoundError:
    lines = [
        'api_id=\n',
        'api_hash=\n',
        'phone_number=+\n',
        'password=\n'
    ]
    with open('config.conf', 'w') as configfile:
        configfile.writelines(lines)

API_ID = lines[0].strip().split('=')[1]
API_HASH = lines[1].strip().split('=')[1]
PHONE_NUMBER = lines[2].strip().split('=')[1]
IIFA_PASSWORD = lines[3].strip().split('=')[1]
ALLOWED_USER_ID = int("")
BOT_TOKEN = ""
ENCODING = "utf-8"
DEFAULT_CHANNEL_ID =
CHANNEL_ID_FILE = "channel_id"
WORKERS_FOLDER = "worker"
FOLDER_NAME = os.path.join(CURR_DIR, WORKERS_FOLDER)
KEYWORDS = []
KEYWORDS_FILE = "keywords.json"
SESSION_NAME = "ryuk_sess"
CLIENT = TelegramClient(SESSION_NAME, API_ID, API_HASH)
BOT = Bot(token=BOT_TOKEN)

bot_commands = [
    BotCommand("start", "Start the bot and get a welcome message."),
    BotCommand("help", "Display all available commands and their usage."),
    BotCommand("find", "ex: /find netflix"),
    BotCommand("findraw", "ex: /findraw netflix"),
    BotCommand("download", "ex: /download netflix"),
    BotCommand("downloadfile", "ex: /downloadfile netflix"),
    BotCommand("ls or ls [dirname]", "List all files in the current directory."),
    BotCommand("remove", "ex: /remove netflix.txt"),
    BotCommand("rename", "ex: /rename netflix.txt, /rn all"),
    BotCommand("password", "ex: /password, /pass 50"),
    BotCommand("execute", "ex: /exec mv filename, /exec ls"),
    BotCommand("getatt", "ex: /getatt -923987905 2, /getatt 100"),
    BotCommand("getchats", "ex: /gc s group/chatname, /getchats all"),
    BotCommand("keyword", "ex: /keyword add/remove example, /keyword show/status"),
    BotCommand("cmd", "Update the commands button (UI).")
]

# load keywords from file (i cant be arsed to make the json funcs into one)
def load_keywords():
    global KEYWORDS
    if os.path.exists(KEYWORDS_FILE):
        with open(KEYWORDS_FILE, "r") as file:
            KEYWORDS = json.load(file)

# save keywords to file
def save_keywords():
    with open(KEYWORDS_FILE, "w") as file:
        json.dump(KEYWORDS, file)

# json saver
def save_channel_id(channel_id):
    with open(CHANNEL_ID_FILE, "w") as file:
        json.dump(channel_id, file)

# json loader
def load_channel_id():
    if os.path.exists(CHANNEL_ID_FILE):
        with open(CHANNEL_ID_FILE, "r") as file:
            return json.load(file)
    else:
        return DEFAULT_CHANNEL_ID

# unknown command handler
async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.forward_from or update.message.forward_from_chat or update.message.text == "stop":
        return
    if update.message.document:
        await update.message.reply_text("Your file is ready!", reply_to_message_id=update.message.message_id)
        return
    await update.message.reply_text("Sorry, I don't understand, use /help to check all commands", reply_to_message_id=update.message.message_id)

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

# helper function to send msgs in chunks avoiding telegram limitations
async def send_chunks(update: Update, context: CallbackContext, chunks: list[str], delay: int) -> None:
    for chunk in chunks:
        await update.message.reply_text(chunk)
        await asyncio.sleep(delay)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user

    await update.message.reply_html(f"Hi {user.mention_html()}!, Bot created by Ryuk!\nUse /help to check current available commands",)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    command_list = [
        ("/start", "", "Start the bot and get a welcome message."),
        ("/help or /h", "", "Display all available commands and their usage."),
        ("/find or /f [query]", "➡ Specify a search query", "Search for credentials based on a query and display them in Username Password format."),
        ("/findraw or /fr [query]", "➡ Specify a search query", "Search for credentials based on a query and display them in raw format."),
        ("/download or /dl [query]", "➡ Specify a search query", "Download all found credentials for a query as a file."),
        ("/downloadfile or /dlf [file_name]", "➡ Specify a file name", "Download a specific file from the server."),
        ("ls or ls [dirname]", "➡ Optionally specify a dir name", "List all files in the current directory."),
        ("/rm or /remove [file_name]", "➡ Specify a file name", "Delete a specific file."),
        ("/rn or /rename [file_name new_name] or [all|all name]", "➡ Specify a file name", "Rename a specific file or all files."),
        ("/execute or /exec [command]", "➡ Specify system command", "Execute a system command."),
        ("/getatt or /dla [channel_id and or limit]", "➡ Specify channel_id and or limit", "Downloads attachments from desired chat id."),
        ("/getchats or /gc [all or s/seach chat/group name]", "➡ Specify group/chat name", "Retrives all/specied group/chat name(s)/id(s)."),
        ("/keyword or /kw [show/add/remove/status]", "➡ Specify a keyword", "adds/removes/shows keywords that the bot will be catching"),
        ("/password or /pass [length|default(10)] (-s) for no special characters", "➡ Specify pass length", "Generate a random password."),
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

        if not os.path.isfile(f"{FOLDER_NAME}/{filename}"):
            await update.message.reply_text(f"File {filename} does not exist. Use `/dl {query}` to generate the txt file first.", reply_to_message_id=update.message.message_id)
            return

        await update.message.reply_text(f"Search is being processed, please wait...")

        response = []
        resultfound = False
        lines_processed = 0

        with codecs.open(f"{FOLDER_NAME}/{filename}", 'r', encoding=ENCODING, errors='ignore') as file_handle:
            lines = file_handle.readlines()
            random.shuffle(lines)

            for line in lines:
                line = line.strip()
                parts = line.split(":")
                if len(parts) >= 3:
                    resultfound = True
                    if "password" in parts[0].lower():
                        username = parts[1].strip() if len(parts) > 1 and parts[2].strip() != "" else "index has no username"
                        password = parts[2].strip() if len(parts) > 2 else "index has no password"
                    if len(parts) == 4:
                        if "http" in parts[0].lower() or "android" in parts[0].lower() or "ftp" in parts[0].lower() or "password" in parts[0].lower():
                            username = parts[2].strip() if len(parts) > 2 and parts[2].strip() != "" else "index has no username"
                            password = parts[3].strip() if len(parts) > 3 else "index has no password"
                        else:
                            username = parts[0].strip() if len(parts) > 2 and parts[2].strip() != "" else "index has no username"
                            password = parts[1].strip() if len(parts) > 3 else "index has no password"

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

        if not os.path.isfile(f"{FOLDER_NAME}/{filename}"):
            await update.message.reply_text(f"File {filename} does not exist. Use `/dl {query}` to generate the txt file first.", reply_to_message_id=update.message.message_id)
            return

        await update.message.reply_text(f"Search is being processed, please wait...")

        response = []
        resultfound = False
        lines_processed = 0

        with codecs.open(f"{FOLDER_NAME}/{filename}", 'r', encoding=ENCODING, errors='ignore') as file_handle:
            lines = file_handle.readlines()
            random.shuffle(lines)

            for line in lines:
                line = line.strip()
                parts = line.split(":")
                if len(parts) >= 3:
                    resultfound = True
                    if "password" in parts[0].lower():
                        username_password = ":".join(parts[1:3])
                    if len(parts) == 4:
                        if "http" in parts[0].lower() or "android" in parts[0].lower() or "ftp" in parts[0].lower() or "password" in parts[0].lower():
                            username_password = ":".join(parts[2:4])
                        else:
                            username_password = ":".join(parts[0:2])
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
        NoUpload = None
        args = context.args
        if len(args) >=1:
            query = args[0]
        if len(args) >= 2:
            NoUpload = args[1]

        if not os.path.exists(f"{FOLDER_NAME}"):
            os.makedirs(f"{FOLDER_NAME}")
        try:
            os.remove(f"{FOLDER_NAME}/{query}.txt")
        except:
            pass

        await update.message.reply_text(f"This may take a while, please wait...")

        program_path = os.path.join(CURR_DIR, "FileFetcher.exe")
        if 'linux' in sys.platform:
            program_path = os.path.join(CURR_DIR, "FileFetcher")

        arguments = [program_path, query, FOLDER_NAME]

        try:
            process = await asyncio.create_subprocess_exec(*arguments, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            output, error = await process.communicate()

            output = output.decode()
            error = error.decode()

            output_filename = f"{query}.txt"
            f_path = f"{FOLDER_NAME}/{output_filename}"
            if output:
                if os.path.exists(f_path):
                    with open(f_path, 'rb') as file:
                        await update.message.reply_text(f"{output}")
                        if os.path.getsize(f_path) > 0:
                            if NoUpload == "-nu":
                                await update.message.reply_text("File will not be uploaded.", reply_to_message_id=update.message.message_id)
                            else:
                                file_size = os.path.getsize(f_path)
                                file_size_mb = file_size / (1024 * 1024)
                                if file_size_mb > 50:
                                    await update.message.reply_text("File is too large to upload, so telethon will be uploading it, please wait...", reply_to_message_id=update.message.message_id)
                                    u_file = await CLIENT.upload_file(f_path)
                                    await CLIENT.send_file(context.bot.id, u_file, force_document=True)
                                else:
                                    await update.message.reply_text("Uploading in progress...")
                                    await context.bot.send_document(
                                        chat_id=update.message.chat_id,
                                        document=file,
                                        filename=output_filename,
                                        caption=f"Download all found credentials for {query.capitalize()}",
                                        reply_to_message_id=update.message.message_id
                                    )
                        else:
                            await update.message.reply_text("File is empty. No credentials found.", reply_to_message_id=update.message.message_id)
                else:
                    await update.message.reply_text("No credentials found.", reply_to_message_id=update.message.message_id)
            elif error:
                await update.message.reply_text(f"Error: {error}", reply_to_message_id=update.message.message_id)
            else:
                for filename in os.listdir(FOLDER_NAME):
                    if re.match(r"log\d+\.txt$", filename):
                        file_path = os.path.join(FOLDER_NAME, filename)
                        os.remove(file_path)
                await update.message.reply_text("❗ Process has been stopped")

        except Exception as e:
            await update.message.reply_text(f"Error: {e}", reply_to_message_id=update.message.message_id)

    except Exception as e:
        await update.message.reply_text(f"Error: {e}", reply_to_message_id=update.message.message_id)

@admin_only
async def ls_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process the ls command to list all files in the current directory."""
    try:
        try:
            ls_dir = context.args[0]
        except:
            ls_dir = "."
        file_list = os.listdir(ls_dir)
        file_list_with_dir = [f"{item} => Dir" if os.path.isdir(os.path.join(ls_dir, item)) else item for item in file_list]

        file_list_formatted = '\n'.join(file_list_with_dir)
        await update.message.reply_text(f"Files in current directory:\n{file_list_formatted}", reply_to_message_id=update.message.message_id)
    except Exception as e:
        await update.message.reply_text(f"Error: {e}", reply_to_message_id=update.message.message_id)

@admin_only
@argument_required
async def download_file_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process the download command to download a specific file."""
    try:
        query = ' '.join(update.message.text.split()[1:])
        file_path = f"{FOLDER_NAME}/{query}"

        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            file_size_mb = file_size / (1024 * 1024)
            if file_size_mb > 50:
                await update.message.reply_text("File is too large to upload, so telethon will be uploading it, please wait...", reply_to_message_id=update.message.message_id)
                u_file = await CLIENT.upload_file(file_path)
                await CLIENT.send_file(context.bot.id, u_file, force_document=True)
            else:
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
        file_path = f"{FOLDER_NAME}/{query}"

        if os.path.exists(file_path):
            os.remove(file_path)
            await update.message.reply_text(f"File '{query}' has been deleted.", reply_to_message_id=update.message.message_id)
        else:
            await update.message.reply_text("File not found, use /ls to see all files.", reply_to_message_id=update.message.message_id)
    except Exception as e:
        await update.message.reply_text(f"Error: {e}", reply_to_message_id=update.message.message_id)

@admin_only
@argument_required
async def rename_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process the rename command to rename all/ a specific file(s)."""
    try:
        query, *args = update.message.text.split()[1:]
        try:
            arg1 = args[0]
        except IndexError:
            arg1 = None
        if query == "all" and arg1 is None:
            count = 1
            for file_name in os.listdir(FOLDER_NAME):
                if file_name.endswith(".txt"):
                    full_path = os.path.join(FOLDER_NAME, file_name)
                    new_file_name = f"combo{count}.txt"
                    while os.path.exists(os.path.join(FOLDER_NAME, new_file_name)):
                        count += 1
                        new_file_name = f"combo{count}.txt"
                    os.rename(full_path, os.path.join(FOLDER_NAME, new_file_name))
                    count += 1
            await update.message.reply_text("All txt files have been renamed combo#.txt", reply_to_message_id=update.message.message_id)
        if query == "all" and arg1 is not None:
            count = 1
            for file_name in os.listdir(FOLDER_NAME):
                if file_name.endswith(".txt"):
                    full_path = os.path.join(FOLDER_NAME, file_name)
                    new_file_name = f"{arg1}{count}.txt"
                    while os.path.exists(os.path.join(FOLDER_NAME, new_file_name)):
                        count += 1
                        new_file_name = f"{arg1}{count}.txt"
                    os.rename(full_path, os.path.join(FOLDER_NAME, new_file_name))
                    count += 1
            await update.message.reply_text(f"All txt files have been renamed {arg1}#.txt", reply_to_message_id=update.message.message_id)
        elif arg1 is not None:
            if os.path.exists(os.path.join(FOLDER_NAME, query)):
                full_path = os.path.join(FOLDER_NAME, query)
                new_file_name = os.path.join(FOLDER_NAME, arg1)
                os.rename(full_path, new_file_name)
                await update.message.reply_text(f"{query} just got renamed to {arg1}", reply_to_message_id=update.message.message_id)
            else:
                await update.message.reply_text(f"Error: {query} doesn't exist.", reply_to_message_id=update.message.message_id)
        elif query != "all" and arg1 is None:
            await update.message.reply_text(f"Unknown argument or invalid file name, use /help.", reply_to_message_id=update.message.message_id)
    except Exception as e:
        await update.message.reply_text(f"Error: {e}", reply_to_message_id=update.message.message_id)

@admin_only
@argument_required
async def execute_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process the execute command to execute a system command."""
    try:
        command = ' '.join(update.message.text.split()[1:])
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        output, error = process.communicate()

        output = output.decode(ENCODING)
        error = error.decode(ENCODING)

        if output:
            await update.message.reply_text(f"{command}: \n{output}", reply_to_message_id=update.message.message_id)
        if error:
            await update.message.reply_text(f"Error! \n{error}", reply_to_message_id=update.message.message_id)
    except Exception as e:
        await update.message.reply_text(f"Error: {e}", reply_to_message_id=update.message.message_id)

@admin_only
async def cmdbutton_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        if ' '.join(update.message.text.split()[1:]) == "kb":
            reply_markup = ReplyKeyboardRemove()
            await update.message.reply_text('Custom button hidden.', reply_markup=reply_markup)
        else:
            bot = Bot(token=BOT_TOKEN)
            await bot.set_my_commands(bot_commands)
            await update.message.reply_text("Coammnds button has been updated!",reply_to_message_id=update.message.message_id)
    except Exception as e:
        await update.message.reply_text(f"Error {e}",reply_to_message_id=update.message.message_id)

async def generate_password_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate a random password."""
    length = 15
    include_special_chars = True

    try:
        first_arg, *args = update.message.text.split()[1:]
        second_arg = args[0]
        if "-s" in first_arg and second_arg:
            include_special_chars = False
            length = int(second_arg)
        elif "-s" in second_arg:
            include_special_chars = False
            length = int(first_arg)
    except:
        try:
            first_arg, *args = update.message.text.split()[1:]
            second_arg = None
            if "-s" in first_arg:
                include_special_chars = False
            else:
                length = int(first_arg)
        except:
            pass

    if include_special_chars:
        characters = string.ascii_letters + string.digits + string.punctuation
    else:
        characters = string.ascii_letters + string.digits

    password = ''.join(secrets.choice(characters) for _ in range(int(length)))

    await update.message.reply_text(f"{password}", reply_to_message_id=update.message.message_id)

@admin_only
@argument_required
async def get_chats(update: Update, context: CallbackContext) -> None:
    try:
        dialog_iterator = CLIENT.iter_dialogs()
        chat_list = "Chat List:\n"
        line_counter = 0
        search_query = None
        search_id = None
        LINE_COUNT_LIMIT = 60

        if len(context.args) > 0:
            if context.args[0] == 'all':
                async for dialog in dialog_iterator:
                    id_str = dialog.entity.id
                    chat_list += f"Title: {dialog.title} | ID: {id_str}\n"
                    line_counter += 1
                    if line_counter == LINE_COUNT_LIMIT:
                        await update.message.reply_text(chat_list)
                        chat_list = ""
                        line_counter = 0
                await update.message.reply_text(chat_list)

            elif context.args[0] in ['s', 'search']:
                if len(context.args) > 1:
                    search_query = context.args[1]
                    chat_found = False
                    try:
                        search_id = int(search_query)
                    except ValueError:
                        search_id = None

                    async for dialog in dialog_iterator:
                        id_str = dialog.entity.id
                        if (search_id and search_id == dialog.id) or \
                                (search_query and (search_query in dialog.title.lower() or search_query in str(dialog.id))):
                            chat_list += f"Title: {dialog.title} | ID: {id_str}\n"
                            line_counter += 1
                            chat_found = True
                            if line_counter == LINE_COUNT_LIMIT:
                                await update.message.reply_text(chat_list)
                                chat_list = ""
                                line_counter = 0
                    if chat_found:
                        await update.message.reply_text(chat_list)
                    else:
                        await update.message.reply_text(f'Search: "{search_query}" not found')

                else:
                    await update.message.reply_text("Please provide a search query.")
            else:
                await update.message.reply_text("Invalid argument. Please use 'all' or 'search'.")
        else:
            await update.message.reply_text("Please provide an argument.")

    except Exception as e:
        await update.message.reply_text(f"Error: {e}", reply_to_message_id=update.message.message_id)


@admin_only
async def get_attachments(update: Update, context: CallbackContext) -> None:
    LOG_DELAY = 25 # Not seconds just iterations
    try:
        args = context.args
        if len(args) == 1:
            if len(args[0]) > 5:
                channel_id = int(args[0])
                limit = 100
            else:
                limit = int(args[0])
                channel_id = int(load_channel_id())
        if len(args) >= 2:
            channel_id = int(args[0])
            limit = int(args[1])
        if len(args) == 0:
            limit = 100
            channel_id = int(load_channel_id())
        save_channel_id(channel_id)

        program_path = os.path.join(CURR_DIR, "RyukDotnetBot.dll")
        process = subprocess.Popen(
            ["dotnet", program_path, str(channel_id), str(limit), str(WORKERS_FOLDER)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        await update.message.reply_text(f'Spawning worker to download files from id "{channel_id}"')
        message = await update.message.reply_text("🔄 Loading...", reply_to_message_id=update.message.message_id)
        current_output = ""
        update_delay = 0
        shittysolution = 0  # to make sure edit_message_text finishes sending all outputs

        while True:
            output = process.stdout.readline().rstrip()
            if update_delay == LOG_DELAY:
                update_delay = 0
            if output != current_output:
                if output.strip():
                    current_output = output
                    try:
                        if update_delay == 0:
                            message = await context.bot.edit_message_text(
                                chat_id=update.effective_chat.id,
                                message_id=message.message_id,
                                text=output
                            )

                        update_delay += 1
                    except error.BadRequest as e:
                        if message.message_id != update.message.message_id:
                            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=message.message_id)
                        message = await update.message.reply_text(output, reply_to_message_id=update.message.message_id)
                    except Exception as e:
                        logger.error(e)
                        continue
            if process.poll() is not None:
                shittysolution += 1
                if shittysolution == 15:
                    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=message.message_id)
                    message = await update.message.reply_text(current_output, reply_to_message_id=update.message.message_id)
                    if process.returncode == -9:
                        await update.message.reply_text(f"❗ Process has been stopped")
                    elif  process.returncode != 0:
                        await update.message.reply_text(f"❗ Error: {process.returncode}",
                                                        reply_to_message_id=update.message.message_id)
                    else:
                        await update.message.reply_text(f'✅ Done!')
                    break
                else:
                    update_delay = 0
                    continue
    except Exception as e:
        await update.message.reply_text(f"Error: {e}", reply_to_message_id=update.message.message_id)

@admin_only
@argument_required
async def handle_keyword_command(update: Update, context: CallbackContext):
    global KEYWORDS
    message = update.message.text
    command, *args = message.split()[1:]

    if command == 'add':
        keyword = args[0]
        if keyword in KEYWORDS:
            await update.message.reply_text(f"⚠️ Keyword '{keyword}' is already added!")
        else:
            KEYWORDS.append(keyword)
            await update.message.reply_text(f"✅ Keyword '{keyword}' added successfully!")
            save_keywords()
    elif command == 'remove':
        keyword = args[0]
        if keyword in KEYWORDS:
            KEYWORDS.remove(keyword)
            await update.message.reply_text(f"✅ Keyword '{keyword}' removed successfully!")
            save_keywords()
        else:
            await update.message.reply_text(f"❗ Keyword '{keyword}' not found.")
    elif command == 'show':
        if len(KEYWORDS) == 0:
            await update.message.reply_text("❗ No keywords found, use /kw add keyword")
            return
        keywords_str = '\n'.join(KEYWORDS)
        await update.message.reply_text(f"Keywords ➡️:\n{keywords_str}")
    elif command == 'status':
        if is_handler_enabled:
            await update.message.reply_text("✅ Bot is currently capturing keywords")
        if not is_handler_enabled:
            await update.message.reply_text("❌ Event handler is disabled, use /kw enable")
    elif command == 'disable':
        await toggle_event("disable")
        await update.message.reply_text("❌ Event handler disabled.")
    elif command == 'enable':
        await toggle_event("enable")
        await update.message.reply_text("✅ Event handler enabled.")
    else:
        await update.message.reply_text(f"❗ Invalid command. Usage: /keyword [add|remove|show]")

#telethon post event handler, poorly factored but who gives a fk
async def handle_message(event):
    sender = await event.get_sender()
    message = event.message.message.lower()
    bot_info = await BOT.get_me()
    bot_id = bot_info.id

    # testing! only for linux
    if sender.id == ALLOWED_USER_ID and message == "stop":
        for proc in psutil.process_iter():
            if proc.name() == "dotnet":
                proc.kill()
            elif proc.name() == "FileFetcher":
                proc.kill()

    if sender.id == bot_id or event.chat_id == bot_id:
        return

    for keyword in KEYWORDS:
        if keyword in message:
            chat_entity = await event.client.get_entity(event.chat_id)
            try:
                chat_username = chat_entity.username
            except AttributeError:
                chat_username = None
            username = sender.username
            if event.is_private:
                phone_number = sender.phone
            else:
                phone_number = None
            if event.is_channel and not event.is_group:
                group_id = str(sender.id).replace("-", "")
            else:
                group_id = str(chat_entity.id).replace("-", "")

            if chat_username is not None:
                url = f"t.me/{chat_username}/{event.message.id}"
                link_text = f"<a href='{url}'>View!</a>"
            elif phone_number is not None:
                url = f"t.me/+{phone_number}/{event.message.id}"
                link_text = f"<a href='{url}'>View!</a>"
            elif username is None:
                url = f"t.me/c/{group_id}/{event.message.id}"
                link_text = f"<a href='{url}'>View!</a>"
                username = f"@{sender.id}"
            else:
                url = f"t.me/c/{group_id}/{event.message.id}"
                link_text = f"<a href='{url}'>View!</a>"

            final = f"⚠️: Keyword detected!\n\nMessage ➡️: 🟢 {message} 🔴 \n\nFrom: <code>{username} ({sender.id})</code>"

            button = InlineKeyboardButton("Go to Message", url=url)
            keyboard = InlineKeyboardMarkup([[button]])

            await BOT.send_message(chat_id=ALLOWED_USER_ID, text=f"{final}\n{link_text}", reply_markup=keyboard, parse_mode='html')

#telethon event handler
@CLIENT.on(events.NewMessage)
async def new_message_handler(event):
    if is_handler_enabled:
        await handle_message(event)

# telethon connector
async def telethon_setup():
    await CLIENT.run_until_disconnected()

async def toggle_event(option):
    global is_handler_enabled
    if option == "enable":
        is_handler_enabled = True
    if option == "disable":
        is_handler_enabled = False

def main() -> None:
    application = Application.builder().token(f"{BOT_TOKEN}").build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler(["help", "h"], help_command))
    application.add_handler(CommandHandler(["find", "f"], search_command))
    application.add_handler(CommandHandler(["findraw", "fr"], search_command_raw))
    application.add_handler(CommandHandler(["download", "dl"], download_command))
    application.add_handler(CommandHandler(["downloadfile", "dlf"], download_file_name))
    application.add_handler(CommandHandler(["remove", "rm"], delete_file))
    application.add_handler(CommandHandler(["rename", "rn"], rename_file))
    application.add_handler(CommandHandler(["execute", "exec"], execute_command))
    application.add_handler(CommandHandler(["password", "pass"], generate_password_command))
    application.add_handler(CommandHandler("cmd", cmdbutton_command))
    application.add_handler(CommandHandler("ls", ls_command))
    application.add_handler(CommandHandler(["getatt", "dla"], get_attachments))
    application.add_handler(CommandHandler(["getchats", "gc"], get_chats))
    application.add_handler(CommandHandler(["keyword", "kw"], handle_keyword_command))
    application.add_handler(MessageHandler(None, unknown_command))
    application.run_polling()

def Start_Bots():
    asyncio.gather(
        telethon_setup(),
        main(),
    )

if __name__ == "__main__":
    print("Starting...")
    load_keywords()
    global is_handler_enabled
    is_handler_enabled = True
    CLIENT.start(PHONE_NUMBER, IIFA_PASSWORD)
    asyncio.run(Start_Bots())
