import os, argparse, contextlib, io, shlex, sys, traceback

import hikari
from replit import db


# This lets me use Replit's secrets system and database and still run test builds locally
if not 'TOKEN' in os.environ:
    with open('token.txt', 'r') as environFile:
        os.environ['TOKEN'] = environFile.read()
if not 'REPLIT_DB_URL' in os.environ:
    with open('replit_db_url.txt', 'r') as environFile:
        os.environ['REPLIT_DB_URL'] = environFile.read()

bot = hikari.GatewayBot(token=os.environ['TOKEN'])

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
async def command_test(event):
    channel= event.get_channel()
    sender = event.author
    await channel.send('test command fired')

async def command_help(event):
    channel = event.get_channel()
    await channel.send('\n'.join(['`{}`: {}'.format(key, commands[key][1]) for key in commands.keys()]) + '\nFor help on a specific command, run that command with the argument `-h` or `--help`.')

async def command_rules(event, *rawArgs):
    sender = event.author
    channel = event.get_channel()

    print('checking args')
    try:
        argsFailed = False
        with redirectIO() as (argparseOut, argparseErr):
            parser = argparse.ArgumentParser(prog='rules')
            group = parser.add_mutually_exclusive_group()
            group.add_argument(
                '-a',
                '--add',
                help='Add a rule to the list',
                nargs=2
            )
            group.add_argument(
                '-r',
                '--remove',
                help='Remove a rule from the list',
                nargs=1
            )
            parser.add_argument(
                '-c',
                '--channel',
                help='Channel for which to get/set rules (defaults to global)',
                nargs=1,
                default='global'
            )
            args = parser.parse_args(rawArgs)
    except BaseException as e:
        argsFailed = True

    if argsFailed:
        await channel.send(argparseOut.getvalue() + argparseErr.getvalue())
    else:
        # Command stuff goes here
        if args.add:
            if userHasPermission(sender, event.get_guild(), hikari.permissions.Permissions.MANAGE_GUILD):
                await channel.send('Added rule.')
            else:
                await channel.send('You need permission: MANAGE_SERVER to add rules')


commands = {
    'test': (command_test, 'Test command to make sure MOW is online'),
    'help': (command_help, 'Show help for all commands'),
    'rules': (command_rules, 'Set/show rules')
}

@bot.listen(hikari.GuildMessageCreateEvent)
async def printMessages(event):
    text = event.content
    try:
        commandData = shlex.split(text)
    except Exception as e:
        await event.get_channel().send(str(e))
    prefix = commandData[0]

    if prefix == 'mow':
        try:
            command, *args = commandData[1:]
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
