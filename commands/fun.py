import argparse
from datetime import datetime, timezone

import hikari

import language
from qotd import askQOTD
from utils import dbBotData, dbQOTD, getIDFromChannelMention, redirectIO, userHasPermission


from . import descriptions


async def command_speak(event, *rawArgs):
    sender = event.author
    channel = event.get_channel()
    guild = event.get_guild()

    try:
        with redirectIO() as (argparseOut, argparseErr):
            parser = argparse.ArgumentParser(prog='speak', description=descriptions.speak)
            parser.add_argument(
                'message',
                help='What to say',
                type=str
            )
            parser.add_argument(
                '--channel',
                '-c',
                help='Channel to speak in',
                type=str,
                default='current'
            )
            args = parser.parse_args(rawArgs)
    except BaseException as e:
        await channel.send('```\n' + argparseOut.getvalue() + argparseErr.getvalue() + '\n```')
        print('argparse exited')
        return False

    if not sender.id in [int(id) for id in dbBotData.get('allowedToSpeak').decode().split(' ')]:
        await channel.send('Refusing to speak, you are not allowed to make me speak')
        return False

    languageMatch = language.examineStr(args.message)
    if languageMatch != None:
        await channel.send('Refusing to speak, does not pass language filter')
        return False

    print('Speaking "{}" in channel {}'.format(args.message, args.channel))
    if args.channel == 'current': targetChannel = channel
    else: targetChannel = guild.get_channel(getIDFromChannelMention(args.channel))

    await targetChannel.send(args.message, user_mentions=True)
    await channel.send('Message has been spoken')
    return True
        
async def command_impostercronk(event, *rawArgs):
    sender = event.author
    channel = event.get_channel()
    guild = event.get_guild()

    if sender.id != int(dbBotData.get('ownerID').decode()):
        await channel.send('Can only be run by my owner')
        return False

    adjusted = []
    unadjusted = []
    for memberID in guild.get_members():
        member = guild.get_member(memberID)
        if not member is None:
            if member.nickname == 'AwesomeCronk':
                try:
                    await member.edit(nickname='ImposterCronk')
                    adjusted.append(member)
                except:
                    unadjusted.append(member)

    if len(adjusted): await channel.send('Adjusted nicknames for:\n{}'.format('\n'.join([str(culprit) for culprit in adjusted])))
    if len(unadjusted): await channel.send('Could not adjust nicknames for:\n{}'.format('\n'.join([str(culprit) for culprit in unadjusted])))

    return True


async def command_qotd_add(event, *rawArgs):
    sender = event.author
    channel = event.get_channel()
    guild = event.get_guild()

    try:
        with redirectIO() as (argparseOut, argparseErr):
            parser = argparse.ArgumentParser(prog='qotd-add', description=descriptions.qotd_add)
            parser.add_argument(
                'question',
                type=str,
                help='The question to add'
            )
            args = parser.parse_args(rawArgs)
    except BaseException as e:
        await channel.send('```\n' + argparseOut.getvalue() + argparseErr.getvalue() + '\n```')
        print('argparse exited')
        return False
    
    if not userHasPermission(sender, guild, hikari.Permissions.MANAGE_MESSAGES):
        await channel.send('You do not have permission to manage QOTD questions')
        return False

    dbQuestions = dbQOTD.node('questions')
    nodeID = 0
    while nodeID in dbQuestions.nodes: nodeID += 1
    dbQuestions.mkNode(nodeID)
    dbQuestion = dbQuestions.node(nodeID)

    dbQuestion.mkKey(0, 'question')
    dbQuestion.mkKey(1, 'lastAsked')
    dbQuestion.mkKey(2, 'timesAsked')
    dbQuestion.mkKey(3, 'suggester')

    dbQuestion.set('question', args.question.encode())
    dbQuestion.set('lastAsked', b'\x00')
    dbQuestion.set('timesAsked', b'\x00')
    dbQuestion.set('suggester', b'')    # Placeholder

    await channel.send('Added question to QOTD list')
    return True

async def command_qotd_list(event, *rawArgs):
    sender = event.author
    channel = event.get_channel()
    guild = event.get_guild()

    try:
        with redirectIO() as (argparseOut, argparseErr):
            parser = argparse.ArgumentParser(prog='qotd-list', description=descriptions.qotd_list)
            args = parser.parse_args(rawArgs)
    except BaseException as e:
        await channel.send('```\n' + argparseOut.getvalue() + argparseErr.getvalue() + '\n```')
        print('argparse exited')
        return False
    
    if not userHasPermission(sender, guild, hikari.Permissions.MANAGE_MESSAGES):
        await channel.send('You do not have permission to manage QOTD questions')
        return False
    
    dbQuestions = dbQOTD.node('questions')
    response = '{} Questions, Current: {}, Minimum age: {}'.format(
        len(dbQuestions.nodes),
        int.from_bytes(dbQOTD.get('current'), 'big'),
        int.from_bytes(dbQOTD.get('minAge'), 'big')
    )
    
    for nodeID in dbQuestions.nodes:
        dbQuestion = dbQuestions.node(nodeID)
        response += '\n{}. `{}`\n  Last asked: #{}, Asked {} times, Suggested by {}'.format(
            nodeID,
            dbQuestion.get('question').decode(),
            int.from_bytes(dbQuestion.get('lastAsked'), 'big'),
            int.from_bytes(dbQuestion.get('timesAsked'), 'big'),
            dbQuestion.get('suggester').decode()
        )

    await channel.send(response)
    return True

async def command_qotd_config(event, *rawArgs):
    sender = event.author
    channel = event.get_channel()
    guild = event.get_guild()

    try:
        with redirectIO() as (argparseOut, argparseErr):
            parser = argparse.ArgumentParser(prog='qotd-config', description=descriptions.qotd_config)
            parser.add_argument(
                '-c',
                '--current',
                type=int,
                default=-1,
                help='Sets the current QOTD (for today, not tomorrow)'
            )
            parser.add_argument(
                '-a',
                '--age',
                type=int,
                default=-1,
                help='Sets the minimum age to re-ask questions'
            )
            args = parser.parse_args(rawArgs)
    except BaseException as e:
        await channel.send('```\n' + argparseOut.getvalue() + argparseErr.getvalue() + '\n```')
        print('argparse exited')
        return False
    
    if not userHasPermission(sender, guild, hikari.Permissions.MANAGE_MESSAGES):
        await channel.send('You do not have permission to manage QOTD questions')
        return False
    
    response = ''

    if args.current != -1:
        dbQOTD.set('current', int.to_bytes(args.current, 4, 'big'))
        response += 'Set current QOTD to {}'.format(args.current)

    if args.age != -1:
        dbQOTD.set('minAge', int.to_bytes(args.age, 4, 'big'))
        response += '\nSet minimum age to re-ask questions to {}'.format(args.age)

    await channel.send(response)
    return True

async def command_qotd_ask(event, *rawArgs):
    sender = event.author
    channel = event.get_channel()
    guild = event.get_guild()

    try:
        with redirectIO() as (argparseOut, argparseErr):
            parser = argparse.ArgumentParser(prog='qotd-ask', description=descriptions.qotd_ask)
            args = parser.parse_args(rawArgs)
    except BaseException as e:
        await channel.send('```\n' + argparseOut.getvalue() + argparseErr.getvalue() + '\n```')
        print('argparse exited')
        return False
    
    if not userHasPermission(sender, guild, hikari.Permissions.MANAGE_MESSAGES):
        await channel.send('You do not have permission to manage QOTD questions')
        return False

    success = askQOTD()
    dbQOTD.set('timestamp', int.to_bytes(int(datetime.now(timezone.utc).timestamp()), 8, 'big'))
    return success
