import shlex, traceback
from datetime import datetime

import hikari

from utils import dbBotData, updatePrefixStatus
from commands import commands

runFlag = True
startupTime = datetime.now()
from uptime import StartUptimeTracking


bot = hikari.GatewayBot(token=dbBotData.get('token').decode())

@bot.listen(hikari.events.lifetime_events.StartedEvent)
async def startup(event):
    await updatePrefixStatus()

@bot.listen(hikari.GuildMessageCreateEvent)
async def handleMessages(event):
    if event.content is None:
        return

    commandPrefix = dbBotData.get('prefix').decode()
    prefix = event.content.strip()[0:len(commandPrefix)]

    # print(repr(commandPrefix), repr(prefix))

    if prefix == commandPrefix:
        proceed = True
        success = False
        text = event.content.strip()[len(commandPrefix):]

        try:
            commandData = shlex.split(text.replace('“', '"').replace('”', '"')) # Replaces iOS quotes with normal quotes before splitting
            # print('split')
        except Exception as e:
            await event.get_channel().send('```python\n{}\n```'.format(traceback.format_exc()))
            proceed = False
        
        if proceed:
            try:
                command, *args = commandData
                # print('parsed')
            except ValueError:
                await event.get_channel().send('must enter a command')
                proceed = False

        if proceed:
            try:
                function = commands[command][0]
                # print('fetched')
            except KeyError:
                await event.get_channel().send('invalid command: "{}"'.format(command))
                proceed = False
        
        if proceed:
            try:
                await function(event, *args)
                success = True
                # print('executed')
            except BaseException as e:
                await event.get_channel().send('```python\n{}\n```'.format(traceback.format_exc()))

        
        record = '{}: ({}) {} issued command:\n{}\n'.format(datetime.now().strftime('%Y-%m-%d %H:%M'), 'SUCCESS' if success else 'FAILURE', event.author, event.content.strip())
        print(record)
        with open('history.txt', 'a') as historyFile:
            historyFile.write(record)

StartUptimeTracking()

try:
    bot.run()
finally:
    runFlag = False
