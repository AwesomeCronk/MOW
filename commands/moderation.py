import argparse, hikari
from datetime import datetime, timedelta, timezone

from utils import dbBotData, dbRules, dbWarnings, dbLanguage
from utils import redirectIO, modLog, publishInfraction, userHasPermission, userMentionedSelf, userMentionFromID, channelMentionFromID, getIDFromUserMention, getIDFromChannelMention

from . import descriptions


async def command_rules(event, *rawArgs):
    sender = event.author
    channel = event.get_channel()

    try:
        with redirectIO() as (argparseOut, argparseErr):
            parser = argparse.ArgumentParser(prog='rules', description=descriptions.rules)
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
        print('argparse exited')
        return
        
    # Command stuff goes here
    response = ''
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
            parser = argparse.ArgumentParser(prog='warn', description=descriptions.warn)
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
                help='Repeal the specified warning for a user',
                nargs=1,
                type=int
            )
            args = parser.parse_args(rawArgs)
    except BaseException as e:
        await channel.send('```\n' + argparseOut.getvalue() + argparseErr.getvalue() + '\n```')
        print('argparse exited')
        return
        
    # Command stuff goes here
    from __main__ import bot

    response = ''
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    warnings = []
    hasPermission = userHasPermission(sender, event.get_guild(), hikari.permissions.Permissions.MANAGE_MESSAGES)
    userID = getIDFromUserMention(args.user)
    ownUser = await bot.rest.fetch_my_user()

    if hasPermission:
        # Get target user object
        
        member = guild.get_member(userID)
        if member is None: member = await bot.rest.fetch_member(guild, userID)
    
    # Ensure this user has a database entry, even if they have no warnings (empty entry)
    # It's a lot simpler than checking every third stage of the command
    if not str(userID) in dbWarnings.nodeNames:
        # Fetch the first available node ID
        for id in range(len(dbWarnings.nodes) + 1):
            if not id in dbWarnings.nodes:
                break
        # Create a node with it
        dbWarnings.mkNode(id, str(userID))

    # Load warnings from database
    dbWarningsUser = dbWarnings.node(str(userID))
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
            warningRoleID = int(dbBotData.get('warningRole{}'.format(len(warnings) + 1)))
            if not member is None:
                await member.remove_role(warningRoleID)

        else:
            response += 'You do not have permission to repeal warnings.'
            await modLog(guild, '{}: {} tried to repeal warning {} for {}. (Note: {})'.format(timestamp, sender.mention, args.repeal[0], args.user, note))

    else:
        if hasPermission:
            if userID == ownUser.id:
                response += 'No.'
            else:
                warnings.append((timestamp, args.note[0]))
                dbWarningsUser.mkNode(len(dbWarningsUser.nodes))
                dbWarning = dbWarningsUser.node(len(dbWarningsUser.nodes) - 1)
                dbWarning.mkKey(0, 'timestamp')
                dbWarning.mkKey(1, 'note')
                response += 'Warned {}{}'.format(args.user, ' (' + args.note[0] + ')' if args.note[0] != 'None' else '')
                await modLog(guild, '{}: {} warned {}. (Note: {})'.format(timestamp, sender.mention, args.user, args.note[0]))
                await publishInfraction(guild, '{}: {} warned {}. (Note: {})\nTotal: {} warnings'.format(timestamp, sender.mention, args.user, args.note[0], len(warnings)))

        else:
            response += 'You do not have permission to issue warnings.'
            await modLog(guild, '{}: {} tried to warn {}. (Note: {})'.format(timestamp, sender.mention, args.user, args.note[0]))

    if hasPermission and userID != ownUser.id:
        # Record warnings in the database
        for i, warning in enumerate(warnings):
            timestamp, note = warning
            dbWarning = dbWarningsUser.node(i)
            dbWarning.set('timestamp', timestamp.encode())
            dbWarning.set('note', note.encode())

        # Set the warning roles
        if 0 < len(warnings) <= 3:
            warningRoleID = int(dbBotData.get('warningRole{}'.format(len(warnings))))
            if member is None:
                response += '\n*Cannot automatically modify roles due to a cache error, please do so manually.*'
            else:
                await member.add_role(warningRoleID)

        # Auto-kick / auto-ban
        if member is None:
            response += '\n*Cannot auto-kick or auto-ban due to a cache error, please kick or ban manually.*'
        else:
            if dbBotData.get('autoKickEnabled') == b'yes' and len(warnings) == 3:
                await member.kick()
                response += '\n{} was kicked automatically.'.format(args.user)
            if dbBotData.get('autoBanEnabled') == b'yes' and len(warnings) == 4:
                await member.ban()
                response += '\n{} was banned automatically.'.format(args.user)

    await channel.send(response)

async def command_warnings(event, *rawArgs):
    sender = event.author
    channel = event.get_channel()

    try:
        with redirectIO() as (argparseOut, argparseErr):
            parser = argparse.ArgumentParser(prog='warnings', description=descriptions.warnings)
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
        print('argparse exited')
        return
        
    # Command stuff goes here
    response = ''
    userID = getIDFromUserMention(args.user)
    # print(targetUser)

    warnings = []
    if str(userID) in dbWarnings.nodeNames:
        dbWarningsUser = dbWarnings.node(str(userID))
        for node in dbWarningsUser.nodes:
            dbWarning = dbWarningsUser.node(node)
            warnings.append((dbWarning.get('timestamp').decode(), dbWarning.get('note').decode()))

    hasPermission = userHasPermission(sender, event.get_guild(), hikari.permissions.Permissions.MANAGE_MESSAGES)

    if userMentionedSelf(sender, args.user) or hasPermission:
        response = 'Warnings for {}:\n'.format(args.user)
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

async def command_kick(event, *rawArgs):
    sender = event.author
    channel = event.get_channel()
    guild = event.get_guild()

    try:
        with redirectIO() as (argparseOut, argparseErr):
            parser = argparse.ArgumentParser(prog='kick', description=descriptions.kick)
            group = parser.add_mutually_exclusive_group()
            parser.add_argument(
                'user',
                help='User to kick',
                type=str
            )
            args = parser.parse_args(rawArgs)
    except BaseException as e:
        await channel.send('```\n' + argparseOut.getvalue() + argparseErr.getvalue() + '\n```')
        print('argparse exited')
        return
        
    # Command stuff goes here
    response = ''
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')

    hasPermission = userHasPermission(sender, event.get_guild(), hikari.permissions.Permissions.MANAGE_MESSAGES)
    
    if hasPermission:
        from __main__ import bot

        # Get target user object
        id = getIDFromUserMention(args.user)
        member = guild.get_member(id)
        ownUser = await bot.rest.fetch_my_user()
        if member is None: member = await bot.rest.fetch_member(guild, id)
        
        if member is None:
            response += 'Could not kick {}.'.format(args.user)
        else:
            if id == ownUser.id:
                response += 'No.'
            else:
                await guild.kick(member.user)

                response += 'kicked {}'.format(args.user)
                await modLog(guild, '{}: {} kicked {}.'.format(timestamp, sender.mention, args.user))
                await publishInfraction(guild, '{}: {} kicked {}.'.format(timestamp, sender.mention, args.user))
    
    else:
        response += 'You do not have permission to kick users.'
        await modLog(guild, '{}: {} tried to kick {}.'.format(timestamp, sender.mention, args.user))
    
    await channel.send(response)

async def command_ban(event, *rawArgs):
    sender = event.author
    channel = event.get_channel()
    guild = event.get_guild()

    try:
        with redirectIO() as (argparseOut, argparseErr):
            parser = argparse.ArgumentParser(prog='ban', description=descriptions.ban)
            parser.add_argument(
                'user',
                help='User to ban',
                type=str
            )
            args = parser.parse_args(rawArgs)
    except BaseException as e:
        await channel.send('```\n' + argparseOut.getvalue() + argparseErr.getvalue() + '\n```')
        print('argparse exited')
        return
        
    # Command stuff goes here
    response = ''
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')

    hasPermission = userHasPermission(sender, event.get_guild(), hikari.permissions.Permissions.MANAGE_MESSAGES)
    
    if hasPermission:
        from __main__ import bot

        # Get target user object
        id = getIDFromUserMention(args.user)
        member = guild.get_member(id)
        ownUser = await bot.rest.fetch_my_user()
        if member is None: member = await bot.rest.fetch_member(guild, id)
        
        if member is None:
            response += 'Could not ban {}.'.format(args.user)
        else:
            if id == ownUser.id:
                response += 'No.'
            else:
                await guild.ban(member.user)
                
                response += 'Banned {}'.format(args.user)
                await modLog(guild, '{}: {} banned {}.'.format(timestamp, sender.mention, args.user))
                await publishInfraction(guild, '{}: {} banned {}.'.format(timestamp, sender.mention, args.user))
    
    else:
        response += 'You do not have permission to ban users.'
        await modLog(guild, '{}: {} tried to ban {}.'.format(timestamp, sender.mention, args.user))
    
    await channel.send(response)

async def command_shush(event, *rawArgs):
    sender = event.author
    channel = event.get_channel()
    guild = event.get_guild()

    try:
        with redirectIO() as (argparseOut, argparseErr):
            parser = argparse.ArgumentParser(prog='shush', description=descriptions.shush)
            parser.add_argument(
                'user',
                help='User to shush',
                type=str
            )
            parser.add_argument(
                'time',
                help='how long to shush the user (1h = 1 hour, 5m = 5 minutes, 30s = 30 seconds)',
                type=str
            )
            args = parser.parse_args(rawArgs)
    except BaseException as e:
        await channel.send('```\n' + argparseOut.getvalue() + argparseErr.getvalue() + '\n```')
        print('argparse exited')
        return
        
    # Command stuff goes here
    response = ''
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')

    hasPermission = userHasPermission(sender, event.get_guild(), hikari.permissions.Permissions.MANAGE_MESSAGES)

    if hasPermission:
        id = getIDFromUserMention(args.user)
        member = guild.get_member(id)
        if member is None: from __main__ import bot; member = await bot.rest.fetch_member(guild, id)

        print(member)
        if member is None:
            response += 'Could not shush {}.'.format(args.user)
        else:
            # parse shush time
            if args.time == 'none':
                await member.edit(communication_disabled_until=None)
                await modLog(guild, '{}: {} unshushed {}'.format(timestamp, sender.mention, args.user))
            else:
                timeOk = True
                for char in args.time:
                    if not char in '0123456789hms':
                        timeOk = False
                if len(args.time) <= 1: timeOk = False
                try: timeNumber = int(args.time[0:-1])
                except ValueError: timeOk = False
                timeType = args.time[-1]
                if not timeType in 'hms': timeOk = False

                if not timeOk:
                    response += 'Invalid time value: `{}`'.format(args.time)
                else:
                    timeTypeExpanded = {'h': 'hours', 'm': 'minutes', 's': 'seconds'}[timeType]
                    delta = timedelta(**{timeTypeExpanded: timeNumber}); print(delta)
                    shushedUntil = datetime.now(timezone.utc) + delta; print(shushedUntil)
                    await member.edit(communication_disabled_until=shushedUntil)
                    response += 'Shushed {} for {} {}.'.format(args.user, timeNumber, timeTypeExpanded)
                    await modLog(guild, '{}: {} shushed {} for {} {}.'.format(timestamp, sender.mention, args.user, timeNumber, timeTypeExpanded))
                    await publishInfraction(guild, '{}: {} shushed {} for {} {}.'.format(timestamp, sender.mention, args.user, timeNumber, timeTypeExpanded))

    else:
        response += 'You do not have permission to shush users.'
        await modLog(guild, '{}: {} tried to shush {}.'.format(timestamp, sender.mention, args.user))

    await channel.send(response)

async def command_language(event, *rawArgs):
    sender = event.author
    channel = event.get_channel()
    guild = event.get_guild()

    try:
        with redirectIO() as (argparseOut, argparseErr):
            parser = argparse.ArgumentParser(prog='language', description=descriptions.language)
            parser.add_argument(
                '-t',
                '--toggle',
                help='Toggle filter on/off',
                action='store_true'
            )
            parser.add_argument(
                '-l',
                '--list',
                help='List keywords and exclusions',
                action='store_true'
            )
            parser.add_argument(
                '-r',
                '--remove',
                help='Remove a keyword',
                nargs=1,
                type=int
            )
            parser.add_argument(
                '-a',
                '--add',
                help='Add a keyword',
                nargs=1,
                type=str
            )
            parser.add_argument(
                '-x',
                '--exclude',
                help='Change an exclusion',
                nargs=1,
                type=str
            )
            args = parser.parse_args(rawArgs)
    except BaseException as e:
        await channel.send('```\n' + argparseOut.getvalue() + argparseErr.getvalue() + '\n```')
        print('argparse exited')
        return

    response = ''
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    hasPermission = userHasPermission(sender, event.get_guild(), hikari.permissions.Permissions.MANAGE_MESSAGES)
    dbExcludeUsers = dbLanguage.node('excludeUsers')
    dbExcludeChannels = dbLanguage.node('excludeChannels')
    dbKeywords = dbLanguage.node('keywords')
    
    if hasPermission:
        # Print current keywords, status, etc
        response += 'Language filter status: {}'.format('on' if dbLanguage.get('active') != b'\x00' else 'off')

        if args.toggle:
            dbLanguage.set('active', b'\xff' if dbLanguage.get('active') == b'\x00' else b'\x00')
            response += '\nToggled language filter {}'.format('on' if dbLanguage.get('active') != b'\x00' else 'off')
            await modLog(guild, '{} toggled language filter {}'.format(sender.mention, 'on' if dbLanguage.get('active') != b'\x00' else 'off'))

        if args.list:
            response += '\nKeywords:\n{}'.format('\n'.join(['{}: `{}`'.format(k + 1, dbKeywords.get(key).decode()) for k, key in enumerate(dbKeywords.keys)]))
            response += '\nUser exclusions:\n{}'.format(', '.join([userMentionFromID(userID) for userID in dbExcludeUsers.keyNames.keys()]))
            response += '\nChannel exclusions:\n{}'.format(', '.join([channelMentionFromID(channelID) for channelID in dbExcludeChannels.keyNames.keys()]))

        if args.remove:
            dbKeywords.rmKey(args.remove[0] - 1)
            response += '\nRemoved keyword {}'.format(args.remove[0])
            await modLog(guild, '{} removed keyword `{}`'.format(sender.mention, args.remove[0]))

        if args.add:
            id = 0
            for key in dbKeywords.keys:
                if key >= id: id = key + 1

            dbKeywords.mkKey(id)
            dbKeywords.set(id, args.add[0].encode())
            response += '\nAdded keyword `{}`'.format(args.add[0])
            await modLog(guild, '{} added keyword `{}`'.format(sender.mention, args.add[0]))

        if args.exclude:
            try: userID = str(getIDFromUserMention(args.exclude[0]))
            except: userID = None
            try: channelID = str(getIDFromChannelMention(args.exclude[0]))
            except: channelID = None

            print(userID, channelID)

            if not userID is None:
                if str(userID) in dbExcludeUsers.keyNames.keys():
                    dbExcludeUsers.rmKey(str(userID))
                    response += '\nRemoved exclusion for {}'.format(args.exclude[0])
                else:
                    id = 0
                    for key in dbExcludeUsers.keys:
                        if key >= id: id = key + 1
                    dbExcludeUsers.mkKey(id, str(userID))
                    response += '\nAdded exclusion for {}'.format(args.exclude[0])

            elif not channelID is None:
                if str(channelID) in dbExcludeChannels.keyNames.keys():
                    dbExcludeChannels.rmKey(str(channelID))
                    response += '\nRemoved exclusion for {}'.format(args.exclude[0])
                else:
                    id = 0
                    for key in dbExcludeChannels.keys:
                        if key >= id: id = key + 1
                    dbExcludeChannels.mkKey(id, str(channelID))
                    response += '\nAdded exclusion for {}'.format(args.exclude[0])

    else:
        response += 'You do not have permission to configure the language filter.'

    await channel.send(response)
