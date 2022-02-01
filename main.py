import os, argparse, contextlib, io, shlex, sys, traceback

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

bot = hikari.GatewayBot(token=os.environ['TOKEN'])
backend = 'Replit' if 'REPL_OWNER' in os.environ else 'Local test'
if backend == 'Replit':
    startKeepAlive()

## Helpers ##
@contextlib.contextmanager
def redirectIO():
    stdoutOld = sys.stdout
    stderrOld = sys.stderr
    stdoutNew = io.StringIO()
    stderrNew = io.StringIO()
    sys.stdout = stdoutNew
    sys.stderr = stderrNew
    try:
        yield stdoutNew, stderrNew
    finally:
        stdoutOld = sys.stdout
        stderrOld = sys.stderr

def userHasPermission(user, guild, permission):
    member = guild.get_member(user)
    memberRoles = member.role_ids
    for roleID in memberRoles:
        role = guild.get_role(roleID)
        rolePermissions = role.permissions
        if permission & rolePermissions:
            return True     # Return True if a role with the desired permission is found among the user's roles in this guild
    return False


## Commands ##
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


commands = {
    'test': (command_test, 'Test command to make sure MOW is online'),
    'info': (command_info, 'Show bot info'),
    'help': (command_help, 'Show help for all commands'),
    'rules': (command_rules, 'Set/show rules')
}

@bot.listen(hikari.GuildMessageCreateEvent)
async def handleMessages(event):
    text = event.content
    prefix = text[0:4]

    if prefix == 'mow ':
        try:
            commandData = shlex.split(text[4:])
        except Exception as e:
            await event.get_channel().send(str(e))
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
            await event.get_channel().send('```\n{}\n```'.format(traceback.format_exc()))
            return

bot.run()
