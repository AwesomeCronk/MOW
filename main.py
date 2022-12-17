import shlex, traceback
from datetime import datetime

import hikari

from utils import dbBotData, updatePrefixStatus, modLog
from commands import commands
import language

runFlag = True
startupTime = datetime.now()
from uptime import StartUptimeTracking


bot = hikari.GatewayBot(
    token=dbBotData.get('token').decode(),
    intents=hikari.Intents.ALL_UNPRIVILEGED | hikari.Intents.MESSAGE_CONTENT
)

@bot.listen(hikari.events.lifetime_events.StartedEvent)
async def startup(event):
    await updatePrefixStatus()

@bot.listen(hikari.GuildMessageCreateEvent)
async def handleMessages(event):
    if event.content is None:
        return

    languageMatch = language.examineEvent(event)
    if languageMatch != None:
        try: await event.message.delete()
        except: pass
        await modLog(event.get_guild(), 'Language filter caught {} (keyword: `{}`):\n> {}'.format(event.author, languageMatch, event.content))
        return

    commandPrefix = dbBotData.get('prefix').decode()
    prefix = event.content.strip()[0:len(commandPrefix)]

    if prefix == commandPrefix:
        proceed = True
        success = False
        text = event.content.strip()[len(commandPrefix):]

        try: commandData = shlex.split(text.replace('“', '"').replace('”', '"')) # Replaces iOS quotes with normal quotes before splitting
        
        except Exception as e:
            await event.get_channel().send('```python\n{}\n```'.format(traceback.format_exc()))
            proceed = False
        
        if proceed:
            try: command, *args = commandData
                
            except ValueError:
                await event.get_channel().send('must enter a command')
                proceed = False

        if proceed:
            try: function = commands[command]
                
            except KeyError:
                await event.get_channel().send('invalid command: "{}"'.format(command))
                proceed = False
        
        if proceed:
            try: success = await function(event, *args)
                
            except BaseException as e:
                await event.get_channel().send('```python\n{}\n```'.format(traceback.format_exc()))

        
        record = '{}: ({}) {} | {}\n'.format(datetime.now().strftime('%Y-%m-%d %H:%M'), 'SUCCESS' if success else 'FAILURE', event.author, event.content.strip())
        print(record)
        with open('history.txt', 'a') as historyFile:
            historyFile.write(record)

StartUptimeTracking()

try:
    bot.run()
finally:
    runFlag = False
