from socket import gethostname
import sys, contextlib, io, os, re

import filesystem_database as fs_db
import hikari

host = (os.getlogin(), gethostname())

dbRoot = fs_db.dbNode('./database')
dbRules = dbRoot.node('rules')
dbWarnings = dbRoot.node('warnings')
dbBotData = dbRoot.node('botData')

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
        sys.stdout = stdoutOld
        sys.stderr = stderrOld

def userHasPermission(user, guild, permission):
    member = guild.get_member(user)
    memberRoles = member.role_ids
    for roleID in memberRoles:
        role = guild.get_role(roleID)
        rolePermissions = role.permissions
        # `return True` is in an if statement so that it doesn't return the first False
        if permission & rolePermissions or rolePermissions & hikari.permissions.Permissions.ADMINISTRATOR:
            return True     # Return True if a role with the desired permission is found among the user's roles in this guild
    return False

def userMentionedSelf(sender, mention):
    if re.match("""^<@!?(\d+)>$""", str(mention)):
        return re.findall('\d+', sender.mention) == re.findall('\d+', mention)

def getIDFromMention(mention):
    if re.match('<@!?[0-9]{18}>$', mention):
        return int(''.join(re.findall('[0-9]', mention)))
    else:
        raise ValueError('Malformed mention: "{}"'.format(mention))

async def modLog(guild, message):
    await guild.get_channel(int(dbBotData.get('modLogsChannel').decode())).send(message)

async def publishInfraction(guild, message):
    await guild.get_channel(int(dbBotData.get('serverInfractionsChannel').decode())).send(message)

async def updatePrefixStatus():
    from __main__ import bot
    await bot.update_presence(
        status=hikari.Status.ONLINE,
        activity=hikari.Activity(
            name='for "{}"'.format(dbBotData.get('prefix').decode()),
            type=hikari.ActivityType.WATCHING
        )
    )
