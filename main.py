import shlex, traceback

import hikari

from utils import dbBotData, updatePrefixStatus
from commands import commands

runFlag = True
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
        text = event.content.strip()[len(commandPrefix):]
        print('Command "{}"'.format(text))
        # print(repr(text))
        try:
            commandData = shlex.split(text.replace('“', '"').replace('”', '"')) # Replaces iOS quotes with normal quotes before splitting
            # print('split')
        except Exception as e:
            await event.get_channel().send('```python\n{}\n```'.format(traceback.format_exc()))
            return
        
        try:
            command, *args = commandData
            # print('parsed')
        except ValueError:
            await event.get_channel().send('must enter a command')
            return

        try:
            function = commands[command][0]
            # print('fetched')
        except KeyError:
            await event.get_channel().send('invalid command: "{}"'.format(command))
            return
        
        try:
            await function(event, *args)
            # print('executed')
        except Exception as e:
            await event.get_channel().send('```python\n{}\n```'.format(traceback.format_exc()))
            print('Command "{}" failed.'.format(text))
            return


StartUptimeTracking()

try:
    bot.run()
finally:
    runFlag = False
