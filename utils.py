import sys, contextlib, io, os, re

import hikari

backend = 'Replit' if 'REPL_OWNER' in os.environ else 'Local test'

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
        if permission & rolePermissions or rolePermissions & hikari.permissions.Permissions.ADMINISTRATOR:
            return True     # Return True if a role with the desired permission is found among the user's roles in this guild
    return False

def userMentionedSelf(sender, mention):
    if re.match("""^<@!?(\d+)>$""", str(mention)):
        return re.findall('\d+', sender.mention) == re.findall('\d+', mention)
