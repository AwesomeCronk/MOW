import os, shlex, traceback

import hikari


# This lets me use Replit's secrets system and database and still run test builds locally
if not 'TOKEN' in os.environ:
    with open('token.txt', 'r') as environFile:
        os.environ['TOKEN'] = environFile.read()
if not 'REPLIT_DB_URL' in os.environ:
    with open('replit_db_url.txt', 'r') as environFile:
        os.environ['REPLIT_DB_URL'] = environFile.read()

from replit import db
from keepAlive import startKeepAlive
from utils import backend
from commands import commands

bot = hikari.GatewayBot(token=os.environ['TOKEN'])
if backend == 'Replit':
    startKeepAlive()


@bot.listen(hikari.GuildMessageCreateEvent)
async def handleMessages(event):
    text = event.content.strip()[4:]
    prefix = event.content.strip()[0:4]

    if prefix == 'mow ':
        try:
            commandData = shlex.split(text)
        except Exception as e:
            await event.get_channel().send('```python\n{}\n```'.format(traceback.format_exc()))
            return
        
        try:
            command, *args = commandData
        except ValueError:
            await event.get_channel().send('must enter a command')
            return

        try:
            function = commands[command][0]
        except KeyError:
            await event.get_channel().send('invalid command: "{}"'.format(command))
            return
        
        try:
            await function(event, *args)
        except Exception as e:
            await event.get_channel().send('```python\n{}\n```'.format(traceback.format_exc()))
            return

bot.run()
