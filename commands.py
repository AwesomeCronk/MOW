import argparse, hikari, psutil
from datetime import datetime

from utils import host, publishInfraction
from utils import dbBotData, dbRules, dbWarnings
from utils import userHasPermission, redirectIO, userMentionedSelf, modLog, updatePrefixStatus

# Bot control/data commands
async def command_test(event, *rawArgs):
    channel= event.get_channel()
    sender = event.author
    await channel.send('test command fired')

async def command_info(event):
    channel = event.get_channel()
    batt = psutil.sensors_battery()
    info = [
        'Status: Online',
        'Host: {}@{}'.format(host[0], host[1]),
        'Battery: {}% {}'.format('No battery' if batt is None else round(batt.percent, 2), '(plugged in)' if batt.power_plugged else '(on battery)'),
        'CPU Temperature: {} ({})'.format(psutil.sensors_temperatures()['coretemp'][0].current, ', '.join([str(t.current) for t in psutil.sensors_temperatures()['coretemp'][1:]])),
        'Source code: <https://github.com/AwesomeCronk/MOW>'
    ]
    await channel.send('\n'.join(info))

async def command_help(event):
    channel = event.get_channel()
    await channel.send('\n'.join(['`{}`: {}'.format(key, commands[key][1]) for key in commands.keys()]) + '\nFor help on a specific command, run that command with the argument `-h` or `--help`.')

# Moderation commands
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
    response = '**WARNING: CURRENT DATABASE IS NOT MAIN DATABASE!!**\n' if host != ('botman', 'Inspiron15-3552') else ''
    targetChannel = args.channel[0]
    rules = []

    if not targetChannel in dbRules.nodeNames:
        # Fetch the first available node ID
        for id in range(len(dbRules.nodes) + 1):
            if not id in dbRules.nodes:
                break
        # Create a node with it
        dbRules.mkNode(id, targetChannel)
    
    dbRulesChannel = dbRules.node(targetChannel)
    for key in dbRulesChannel.keys:
        rules.append(dbRulesChannel.get(key).decode())
    
    if args.add:
        if userHasPermission(sender, event.get_guild(), hikari.permissions.Permissions.MANAGE_GUILD):
            rules.append(args.add[0])
            dbRulesChannel.mkKey(len(dbRulesChannel.keys))
            response += 'Added rule for {}.'.format('server' if targetChannel == '<everywhere>' else targetChannel)
        else:
            response += 'You need permission: MANAGE_GUILD to add rules'
    elif args.remove:
        if userHasPermission(sender, event.get_guild(), hikari.permissions.Permissions.MANAGE_GUILD):
            del(rules[args.remove[0] - 1])
            dbRulesChannel.rmKey(len(dbRulesChannel.keys) - 1)
            response += 'Removed rule for {}.'.format(targetChannel)
        else:
            response += 'You need permission: MANAGE_GUILD to remove rules'
    else:
        if targetChannel == '<everywhere>':
            response += 'Server rules:\n'
        else:
            response += 'Rules for channel {}:\n'.format(targetChannel)
        if len(rules):
            response += '\n'.join(['{}. {}'.format(i + 1, rules[i]) for i in range(len(rules))])
        else:
            response += 'No rules listed.'
    
    for i, rule in enumerate(rules):
        dbRulesChannel.set(i, rule.encode())
    await channel.send(response)

async def command_warn(event, *rawArgs):
    sender = event.author
    channel = event.get_channel()
    guild = event.get_guild()

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
    response = '**WARNING: CURRENT DATABASE IS NOT MAIN DATABASE!!**\n' if host != ('botman', 'Inspiron15-3552') else ''
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    warnings = []
    hasPermission = userHasPermission(sender, event.get_guild(), hikari.permissions.Permissions.MANAGE_MESSAGES)
    
    # Ensure this user has a database entry, even if they have no warnings (empty entry)
    # It's a lot simpler than checking every third stage of the command
    if not args.user in dbWarnings.nodeNames:
        # Fetch the first available node ID
        for id in range(len(dbWarnings.nodes) + 1):
            if not id in dbWarnings.nodes:
                break
        # Create a node with it
        dbWarnings.mkNode(id, args.user)

    # Load warnings from database
    dbWarningsUser = dbWarnings.node(args.user)
    for node in dbWarningsUser.nodes:
        dbWarning = dbWarningsUser.node(node)
        warnings.append((dbWarning.get('timestamp').decode(), dbWarning.get('note').decode()))

    if args.repeal:
        note = dbWarningsUser.node(args.repeal[0] - 1).get('note').decode()
        if hasPermission:
            del(warnings[args.repeal[0] - 1])   # Remove that item from the list
            dbWarningsUser.rmNode(len(dbWarningsUser.nodes) - 1)  # Remove the last key (warnings will be rewritten in the proper order)
            response += 'Repealed warning {} for {}'.format(args.repeal[0], args.user)
            await modLog(guild, '{}: {} repealed warning {} for {}. (Note: {})'.format(timestamp, sender.mention, args.repeal[0], args.user, note))

        else:
            response += 'You do not have permission repeal warnings.'
            await modLog(guild, '{}: {} tried to repeal warning {} for {}. (Note: {})'.format(timestamp, sender.mention, args.repeal[0], args.user, note))

    else:
        if hasPermission:
            warnings.append((timestamp, args.note[0]))
            dbWarningsUser.mkNode(len(dbWarningsUser.nodes))
            dbWarning = dbWarningsUser.node(len(dbWarningsUser.nodes) - 1)
            dbWarning.mkKey(0, 'timestamp')
            dbWarning.mkKey(1, 'note')
            response += 'Warned {}{}'.format(args.user, ' (' + args.note[0] + ')' if args.note[0] != 'None' else '')
            await modLog(guild, '{}: {} warned {}. (Note: {})'.format(timestamp, sender.mention, args.user, args.note[0]))
            await publishInfraction(guild, '{}: {} warned {}. (Note: {})'.format(timestamp, sender.mention, args.user, args.note[0]))

        else:
            response += 'You do not have permission to issue warnings.'
            await modLog(guild, '{}: {} tried to warn {}. (Note: {})'.format(timestamp, sender.mention, args.user, args.note[0]))

    # Record warnings in the database
    for i, warning in enumerate(warnings):
        timestamp, note = warning
        dbWarning = dbWarningsUser.node(i)
        dbWarning.set('timestamp', timestamp.encode())
        dbWarning.set('note', note.encode())
    await channel.send(response)

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
    response = '**WARNING: CURRENT DATABASE IS NOT MAIN DATABASE!!**\n' if host != ('botman', 'Inspiron15-3552') else ''
    targetUser = args.user
    # print(targetUser)

    warnings = []
    if targetUser in dbWarnings.nodeNames:
        dbWarningsUser = dbWarnings.node(targetUser)
        for node in dbWarningsUser.nodes:
            dbWarning = dbWarningsUser.node(node)
            warnings.append((dbWarning.get('timestamp').decode(), dbWarning.get('note').decode()))

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
        response += 'You do not have permission view someone else\'s warnings.'
        await channel.send(response)

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
        await channel.send('```\n' + argparseOut.getvalue() + argparseErr.getvalue() + '\n```')
        return

    if args.key == 'token':
        response = 'Value of `token` is `Cronk\'s token. Property of Cronk. Do not use except for Cronk.`'

    elif userHasPermission(sender, event.get_guild(), hikari.permissions.Permissions.MANAGE_GUILD):
        response = ''

        if args.create:
            # Get the first available key ID
            for id in range(len(dbBotData.keys) + 1):
                if not id in dbBotData.keys:
                    break
            # Create a key with it
            dbBotData.mkKey(id, args.key)
            response += 'Created {}\n'.format(args.key)


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

    else:
        response = 'You do not have permission to view or modify Maintenance of Way configuration.'

    if args.key == 'prefix':
        await updatePrefixStatus()

    await channel.send(response)

commands = {
    'test': (command_test, 'Test command to check if Maintenance of Way is online'),
    'info': (command_info, 'Show bot info'),
    'help': (command_help, 'Show help for all commands'),

    'rules': (command_rules, 'Show or set rules'),
    'warn': (command_warn, 'Warn a user'),
    'warnings': (command_warnings, 'View a user\'s warnings'),
    'config': (command_config, 'View or change configuration')
}