import argparse

from utils import dbBotData, getIDFromChannelMention, redirectIO

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

    print('Speaking "{}" in channel {}'.format(args.message, args.channel))
    if args.channel == 'current': targetChannel = channel
    else: targetChannel = guild.get_channel(getIDFromChannelMention(args.channel))

    await targetChannel.send(args.message, user_mentions=True)
    await channel.send('Message has been spoken')
    return True
        
