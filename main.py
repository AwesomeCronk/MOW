import argparse
from tempfile import TemporaryFile

import hikari


with open('token.txt', 'r') as tokenFile:
    bot = hikari.GatewayBot(token=tokenFile.read())

## Commands ##
async def command_test(event):
    channel= event.get_channel()
    await channel.send('test command fired')

async def command_help(event):
    channel = event.get_channel()
    await channel.send('\n'.join(['{}: {}'.format(key, commands[key][1]) for key in commands.keys()]))

async def command_rules(event):
    pass


commands = {
    'test': (command_test, 'Test command to make sure MOW is online'),
    'help': (command_help, 'Show help for all commands'),
    'rules': (command_rules, 'Set/show rules')
}

@bot.listen(hikari.GuildMessageCreateEvent)
async def printMessages(event):
    text = event.content
    commandData = text.split()
    prefix = commandData[0]

    if prefix == 'mow':
        try:
            command, *args = commandData[1:]
        except IndexError:
            print('must enter a command')
        try:
            function = commands[command][0]
        except KeyError:
            print('invalid command: "{}"'.format(command))
            return
        try:
            await function(event, *args)
        except Exception as e:
            print('{}: {}'.format(type(e).__name__, e))

bot.run()
