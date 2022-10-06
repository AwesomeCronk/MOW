import re

from utils import dbLanguage

def examine(messageEvent):
    message = messageEvent.content
    userID = messageEvent.author.id
    channelID = messageEvent.get_channel().id

    active = dbLanguage.get('active')
    excludeUsers = list(dbLanguage.node('excludeUsers').keyNames.keys())
    excludeChannels = list(dbLanguage.node('excludeChannels').keyNames.keys())

    if str(userID) in excludeUsers:
        return None
    if str(channelID) in excludeChannels:
        return None

    # Match the message content to keyword regexes, return the regex that flagged, if any
    if active:
        dbKeywords = dbLanguage.node('keywords')
        for key in dbKeywords.keys:
            keyword = dbKeywords.get(key).decode()
            if not re.search(keyword, message.lower()) is None:
                return keyword
    return None
