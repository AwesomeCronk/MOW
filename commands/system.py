import argparse, platform, psutil, hikari
from datetime import datetime

from utils import dbBotData, host
from utils import userHasPermission, redirectIO, updatePrefixStatus

from . import descriptions


commandPrefix = dbBotData.get('prefix').decode()


async def command_info(event, *rawArgs):
    channel = event.get_channel()
    
    # I'm leaving the argparse section as a comment because I may add it back later
    # try:
    #     with redirectIO() as (argparseOut, argparseErr):
    #         parser = argparse.ArgumentParser(prog='info', description=descriptions.info)
    #         args = parser.parse_args(rawArgs)
    # except BaseException as e:
    #     await channel.send('Problem while parsing arguments:\n```\n' + argparseOut.getvalue() + argparseErr.getvalue() + '\n```')
    #     return False

    from __main__ import startupTime

    batt = psutil.sensors_battery()
    bootTime = psutil.boot_time()
    now = datetime.now()
    info = [
        'Status: Online',
        'Python version: {}'.format(platform.python_version()),
        'Hikari version: {}'.format(hikari.__version__),
        'Bot uptime: ' + str(now - startupTime),
        'Host uptime: ' + str(now - datetime.fromtimestamp(bootTime)),
        'Host: {}@{}'.format(host[0], host[1]),
        'Battery: {}% {}'.format('0' if batt is None else round(batt.percent, 2), '(no battery)' if batt is None else '(plugged in)' if batt.power_plugged else '(on battery)'),
        'CPU Temperature: {} ({})'.format(psutil.sensors_temperatures()['coretemp'][0].current, ', '.join([str(t.current) for t in psutil.sensors_temperatures()['coretemp'][1:]])),
        'Source code: <https://github.com/AwesomeCronk/MOW>'
    ]
    await channel.send('\n'.join(info))
    return True


async def command_config(event, *rawArgs):
    sender = event.author
    channel = event.get_channel()

    try:
        with redirectIO() as (argparseOut, argparseErr):
            parser = argparse.ArgumentParser(prog='config', description=descriptions.config)
            parser.add_argument(
                'key',
                help='Key to view or modify',
                type=str
            )
            parser.add_argument(
                '-s',
                '--set',
                help='Set the value of the key',
                nargs=1,
                action='store'
            )
            parser.add_argument(
                '-c',
                '--create',
                help='Create the key',
                action='store_true'
            )
            parser.add_argument(
                '-r',
                '--remove',
                help='Remove the key',
                action='store_true'
            )
            args = parser.parse_args(rawArgs)
    except BaseException as e:
        await channel.send('Problem while parsing arguments:\n```\n' + argparseOut.getvalue() + argparseErr.getvalue() + '\n```')
        return False

    if not userHasPermission(sender, event.get_guild(), hikari.permissions.Permissions.MANAGE_GUILD):
        await channel.send('You do not have permission to view or modify Maintenance of Way configuration.')
        return False

    if args.key == 'token':
        response = 'Value of `token` is `Cronk\'s token. Property of Cronk. Do not use except for Cronk.`'
    elif args.key == '*':
        response = 'Values of all keys:'
        for id in dbBotData.keys:
            name = dbBotData.getKeyName(id)
            if name == 'token': value = 'Cronk\'s token. Property of Cronk. Do not use except for Cronk.'
            else: value = dbBotData.get(id).decode()
            response += '\n{} - "{}": `{}`'.format(id, name, value)
    else:
        response = ''

        if args.create:
            # Get the first available key ID
            for id in range(len(dbBotData.keys) + 1):
                if not id in dbBotData.keys:
                    break
            # Create a key with it
            dbBotData.mkKey(id, args.key)
            response += 'Created `{}`\n'.format(args.key)

        oldValue = dbBotData.get(args.key)
        response += 'Value of `{}` is `{}`'.format(args.key, oldValue.decode() if oldValue else ' ')

        if args.set:
            dbBotData.set(args.key, args.set[0].encode())
            newValue = dbBotData.get(args.key)
            response += '\nValue of `{}` changed to `{}`'.format(args.key, newValue.decode())

        if args.remove:
            if args.key == 'prefix':    # Fail-safe to keep the bot from breaking entirely.
                response += '\nYou cannot remove the prefix.'
            else:
                dbBotData.rmKey(args.key)
                response += '\nRemoved `{}`'.format(args.key)

        if args.key == 'prefix':
            await updatePrefixStatus()

    await channel.send(response)
    return True


async def command_help(event, *rawArgs):
    channel = event.get_channel()

    # I'm leaving the argparse section as a comment because I may add it back later
    # try:
    #     with redirectIO() as (argparseOut, argparseErr):
    #         parser = argparse.ArgumentParser(prog='help', description=descriptions.help)
    #         args = parser.parse_args(rawArgs)
    # except BaseException as e:
    #     await channel.send('Problem while parsing arguments:\n```\n' + argparseOut.getvalue() + argparseErr.getvalue() + '\n```')
    #     return False

    await channel.send(
        '\n'.join(
            ['`{}{}` - {}'.format(commandPrefix, command, getattr(descriptions, command.replace('-', '_'))) for command in [
                'info', 'config', 'help', 'history',
                'rules', 'warn', 'warnings', 'kick', 'ban', 'mute', 'unmute', 'shush', 'language', 'embed-verify', 'clear', 'clear-alike',
                'speak'
                ]
            ]
        )
        + '\nFor help on a specific command, run that command with the argument `-h` or `--help`.'
    )
    return True


async def command_history(event, *rawArgs):
    sender = event.author
    channel = event.get_channel()
    guild = event.get_guild()

    messageLengthLimit = int(dbBotData.get('messageLengthLimit').decode())
    
    # I'm leaving the argparse section as a comment because I may add it back later
    # try:
    #     with redirectIO() as (argparseOut, argparseErr):
    #         parser = argparse.ArgumentParser(prog='history', description=descriptions.history)
    #         args = parser.parse_args(rawArgs)
    # except BaseException as e:
    #     await channel.send('Problem while parsing arguments:\n```\n' + argparseOut.getvalue() + argparseErr.getvalue() + '\n```')
    #     return False

    if not userHasPermission(sender, guild, hikari.permissions.Permissions.MANAGE_MESSAGES):
        await channel.send('You must have permission: MANAGE_MESSAGES to read off command history')
        return False

    await channel.send('Reading history file in {} character batches'.format(messageLengthLimit))
    with open('history.txt', 'r') as historyFile:
        batch = ''
        while True:
            nextEntry = historyFile.readline()
            if nextEntry == '': break
            if len(batch) + len(nextEntry) <= messageLengthLimit: batch += nextEntry
            else:
                await channel.send(batch)
                batch = ''
                batch += nextEntry
        if batch != '':
            await channel.send(batch)
    return True
