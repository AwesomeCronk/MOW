import argparse, hikari, psutil
from datetime import datetime

from utils import host
from utils import dbBotData, dbRules, dbWarnings
from utils import userHasPermission, redirectIO, userMentionedSelf, modLog


async def command_test(event, *rawArgs):
    channel= event.get_channel()
    sender = event.author
    await channel.send('test command fired')

async def command_info(event):
    channel = event.get_channel()
    info = [
        'Status: Online',
        'Host: {}@{}'.format(host[0], host[1]),
        'Battery: {}'.format('No battery' if psutil.sensors_battery() is None else psutil.sensors_battery().percent),
        'CPU Temperature: {} ({})'.format(psutil.sensors_temperatures()['coretemp'][0].current, ', '.join([str(t.current) for t in psutil.sensors_temperatures()['coretemp'][1:]])),
        'Source code: <https://github.com/AwesomeCronk/MOW>'
    ]
    await channel.send('\n'.join(info))

async def command_help(event):
    channel = event.get_channel()
    await channel.send('\n'.join(['`{}`: {}'.format(key, commands[key][1]) for key in commands.keys()]) + '\nFor help on a specific command, run that command with the argument `-h` or `--help`.')

async def command_rules(event, *rawArgs):
    sender = event.author
    channel = event.get_channel()

    try:
        with redirectIO() as (argparseOut, argparseErr):
            parser = argparse.ArgumentParser(prog='rules')
            group = parser.add_mutually_exclusive_group()
            group.add_argument(
                '-a',
                '--add',
                help='Add a rule to the list',
                nargs=1,
                type=str
            )
            group.add_argument(
                '-r',
                '--remove',
                help='Remove a rule from the list',
                nargs=1,
                type=int
            )
            parser.add_argument(
                '-c',
                '--channel',
                help='Channel for which to get/set rules (defaults to global)',
                nargs=1,
                type=str,
                default=['<everywhere>']
            )
            args = parser.parse_args(rawArgs)
    except BaseException as e:
        await channel.send('```\n' + argparseOut.getvalue() + argparseErr.getvalue() + '\n```')
        return
        
    # Command stuff goes here
    targetChannel = args.channel[0]

    rules = []
    if targetChannel in dbRules.nodeNames:
        dbRulesChannel = dbRules.node(targetChannel)
        for key in dbRulesChannel.keys:
            rules.append(dbRulesChannel.get(key).decode())
    
    if args.add:
        if userHasPermission(sender, event.get_guild(), hikari.permissions.Permissions.MANAGE_GUILD):
            rules.append(args.add[0])
            dbRulesChannel.mkKey(len(dbRulesChannel.keys))
            await channel.send('Added rule for {}.'.format(targetChannel))
        else:
            await channel.send('You need permission: MANAGE_GUILD to add rules')
    elif args.remove:
        if userHasPermission(sender, event.get_guild(), hikari.permissions.Permissions.MANAGE_GUILD):
            del(rules[args.remove[0] - 1])
            dbRulesChannel.rmKey(len(dbRulesChannel.keys) - 1)
            await channel.send('Removed rule for {}.'.format(targetChannel))
        else:
            await channel.send('You need permission: MANAGE_GUILD to remove rules')
    else:
        if targetChannel == '<everwhere>':
            response = 'Server rules:\n'
        else:
            response = 'Channel {} rules:\n'.format(targetChannel)
        if len(rules):
            response += '\n'.join(['{}. {}'.format(i + 1, rules[i]) for i in range(len(rules))])
        else:
            response += 'No rules listed.'
        await channel.send(response)

    for i, rule in enumerate(rules):
        dbRulesChannel.set(i, rule.encode())

async def command_warn(event, *rawArgs):
    sender = event.author
    channel = event.get_channel()

    try:
        with redirectIO() as (argparseOut, argparseErr):
            parser = argparse.ArgumentParser(prog='warn')
            group = parser.add_mutually_exclusive_group()
            parser.add_argument(
                'user',
                help='User to warn',
                type=str
            )
            group.add_argument(
                '-n',
                '--note',
                help='Record a note for a warning',
                nargs=1,
                type=str,
                default=['None']
            )
            group.add_argument(
                '-r',
                '--repeal',
                help='Repeal the last warning for a user',
                nargs=1,
                type=int
            )
            parser.add_argument(
                '-d',
                '--direct-messages',
                help='Send the warning list to your DMs',
                action='store_true'
            )
            args = parser.parse_args(rawArgs)
    except BaseException as e:
        await channel.send('```\n' + argparseOut.getvalue() + argparseErr.getvalue() + '\n```')
        return
        
    # Command stuff goes here
    targetUser = args.user
    print(targetUser)

    warnings = []
    if targetUser in dbWarnings.nodeNames:
        dbWarningsUser = dbWarnings.node(targetUser)
        for key in dbWarningsUser.keys:
            warnings.append(dbWarningsUser.get(key).decode())

    hasPermission = userHasPermission(sender, event.get_guild(), hikari.permissions.Permissions.MANAGE_MESSAGES)

    if args.repeal:
        if hasPermission:
            del(warnings[args.repeal[0] - 1])
            dbWarningsUser.rmKey(len(dbWarningsUser.keys) - 1)
            await channel.send('Repealed warning {} for {}'.format(args.repeal[0], targetUser))

            ### Need to send record to #modlogs
        else:
            await channel.send('You do not have permission repeal warnings.')

    else:
        if hasPermission:
            warnings.append((datetime.today().strftime('%Y-%m-%d'), args.note[0]))
            dbWarningsUser.mkKey(len(dbWarningsUser.keys))
            await channel.send('Warned {}{}'.format(args.user, ' (' + args.note[0] + ')' if args.note[0] != 'None' else ''))

            ### Need to send record to #modlogs
        else:
            await channel.send('You do not have permission to issue warnings.')

    for i, warning in enumerate(warnings):
        dbWarningsUser.set(i, warning.encode())

async def command_warnings(event, *rawArgs):
    sender = event.author
    channel = event.get_channel()

    try:
        with redirectIO() as (argparseOut, argparseErr):
            parser = argparse.ArgumentParser(prog='warnings')
            parser.add_argument(
                'user',
                help='User for whom to view warnings',
                type=str
            )
            parser.add_argument(
                '-d',
                '--direct-messages',
                help='Send the warning list to your DMs',
                action='store_true'
            )
            args = parser.parse_args(rawArgs)
    except BaseException as e:
        await channel.send('```\n' + argparseOut.getvalue() + argparseErr.getvalue() + '\n```')
        return
        
    # Command stuff goes here
    targetUser = args.user
    print(targetUser)

    warnings = []
    if targetUser in dbWarnings.nodeNames:
        dbWarningsUser = dbWarnings.node(targetUser)
        for key in dbWarningsUser.keys:
            warnings.append(dbWarningsUser.get(key).decode())

    hasPermission = userHasPermission(sender, event.get_guild(), hikari.permissions.Permissions.MANAGE_MESSAGES)

    if userMentionedSelf(sender, args.user) or hasPermission:
        response = 'Warnings for {}:\n'.format(targetUser)
        if len(warnings):
            response += '\n'.join(['{}. {} - {}'.format(i + 1, warnings[i][0], warnings[i][1] if warnings[i][1] != 'None' else '') for i in range(len(warnings))])
        else:
            response += 'No warnings listed.'

        if args.direct_messages:
            await sender.send(response)
            await channel.send('Warning list sent to your DMs.')
        else:
            await channel.send(response)
    else:
        await channel.send('You do not have permission view someone else\'s warnings.')

async def command_config(event, *rawArgs):
    sender = event.author
    channel = event.get_channel()

    try:
        with redirectIO() as (argparseOut, argparseErr):
            parser = argparse.ArgumentParser(prog='config')
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
            args = parser.parse_args(rawArgs)
    except BaseException as e:
        await channel.send('```\n' + argparseOut.getvalue() + argparseErr.getvalue() + '\n```')
        return

    if args.key == 'token':
        response = 'Yeah nice try...'

    elif userHasPermission(sender, event.get_guild(), hikari.permissions.Permissions.MANAGE_GUILD):
        oldValue = dbBotData.get(args.key)
        response = 'Value of `{}` is `{}`'.format(args.key, oldValue.decode())
        if args.set:
            dbBotData.set(args.key, args.set[0].encode())
            newValue = dbBotData.get(args.key)
            response += '\nValue of `{}` changed to `{}`'.format(args.key, newValue.decode())

    else:
        response = 'You do not have permission to view or modify MOW configuration.'

    await channel.send(response)

commands = {
    'test': (command_test, 'Test command to make sure MOW is online'),
    'info': (command_info, 'Show bot info'),
    'help': (command_help, 'Show help for all commands'),
    'rules': (command_rules, 'Show or set rules'),
    'warn': (command_warn, 'Warn a user'),
    'warnings': (command_warnings, 'View a user\'s warnings'),
    'config': (command_config, 'View or change configuration')
}