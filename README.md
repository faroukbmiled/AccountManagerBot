# AccountManagerBot
Telegram bot that manage accounts and more

# Usage:
* ```pip install -r .\requirements.txt```
* fill in your information such as ```ALLOWED_USER_ID=```, ```BOT_TOKEN=```, ```FILE_NAME=```
* ```python AccountManager.py```
* use /cmd to register commands for the ui button

# Available commands:
``` xml
/start 
Start the bot and get a welcome message.

/help or /h 
Display all available commands and their usage.

/find [query] -> Specify a search query
Search for credentials based on a query and display them in Username Password format.

/findraw [query] -> Specify a search query
Search for credentials based on a query and display them in raw format.

/update or /up 
Combine or update all text files in the current directory.

/downloadall or /dla 
Download all credentials as a file.

/download or /dl [query] -> Specify a search query
Download all found credentials for a query as a file.

/downloadfile or /dlf [file_name] -> Specify a file name
Download a specific file from the server.

/ls 
List all files in the current directory.

/cmd 
Update the commands boutton (UI).
```
