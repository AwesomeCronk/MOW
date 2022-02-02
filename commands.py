import argparse, re
from datetime import datetime

import hikari

from replit import db
from utils import backend, userHasPermission, redirectIO, userMentionedSelf


async def command_test(event, *rawArgs):
    channel= event.get_channel()
    sender = event.author
    await channel.send('test command fired')

async def command_info(event):
    channel = event.get_channel()
    info = [
        'Status: Online',
        'Backend: {}'.format(backend)
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
        await channel.send(argparseOut.getvalue() + argparseErr.getvalue())
        return
        
    # Command stuff goes here
    targetChannel = args.channel[0]
    try:
        rules = db.get('rules{}'.format(targetChannel))
    except:
        rules = []
    if rules is None:
        rules = []

    if args.add:
        if userHasPermission(sender, event.get_guild(), hikari.permissions.Permissions.MANAGE_GUILD):
            rules.append(args.add[0])
            await channel.send('Added rule for {}.'.format(targetChannel))
        else:
            await channel.send('You need permission: MANAGE_GUILD to add rules')
    elif args.remove:
        if userHasPermission(sender, event.get_guild(), hikari.permissions.Permissions.MANAGE_GUILD):
            del(rules[args.remove[0] - 1])
            await channel.send('Removed rule for {}.'.format(targetChannel))
        else:
            await channel.send('You need permission: MANAGE_GUILD to remove rules')
    else:
        await channel.send('Here are the rules for {}:\n{}'.format(targetChannel, '\n'.join(['{}. {}'.format(i + 1, rules[i]) for i in range(len(rules))])))

    db.set('rules{}'.format(targetChannel), rules)

async def command_warn(event, *rawArgs):
    sender = event.author
    channel = event.get_channel()

    try:
        with redirectIO() as (argparseOut, argparseErr):
            parser = argparse.ArgumentParser(prog='rules')
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
            group.add_argument(
                '-l',
                '--list',
                help='List a user\'s warnings',
                action='store_true'
            )
            args = parser.parse_args(rawArgs)
    except BaseException as e:
        await channel.send(argparseOut.getvalue() + argparseErr.getvalue())
        return
        
    # Command stuff goes here
    targetUser = args.user

    try:
        warnings = db.get('warnings{}'.format(targetUser))
    except:
        warnings = []
    if warnings is None:
        warnings = []

    hasPermission = userHasPermission(sender, event.get_guild(), hikari.permissions.Permissions.MANAGE_MESSAGES)

    if args.list:
        if userMentionedSelf(sender, args.user) or hasPermission:
            response = 'Warnings for {}:\n{}'.format(targetUser, '\n'.join(['{}. {} {}'.format(i + 1, warnings[i][0], warnings[i][1] if warnings[i][1] != 'None' else '') for i in range(len(warnings))]))
            if args.direct_messages:
                await sender.send(response)
                await channel.send('Warning list sent to your DMs.')
            else:
                await channel.send(response)
        else:
            await channel.send('You do not have permission view someone else\'s warnings.')

    elif args.repeal:
        if hasPermission:
            del(warnings[args.repeal[0] - 1])
            await channel.send('Repealed warning {} for {}'.format(args.repeal[0], targetUser))

            ### Need to send record to #modlogs
        else:
            await channel.send('You do not have permission repeal someone else\'s warnings.')

    else:
        if hasPermission:
            warnings.append((datetime.today().strftime('%Y-%m-%d'), args.note[0]))
            await channel.send('Warned {}{}'.format(args.user, ' (' + args.note[0] + ')' if args.note[0] != 'None' else ''))

            ### Need to send record to #modlogs
        else:
            await channel.send('You do not have permission warn someone else.')

    db.set('warnings{}'.format(targetUser), warnings)

commands = {
    'test': (command_test, 'Test command to make sure MOW is online'),
    'info': (command_info, 'Show bot info'),
    'help': (command_help, 'Show help for all commands'),
    'rules': (command_rules, 'Set/show rules'),
    'warn': (command_warn, 'Warn a user')
}