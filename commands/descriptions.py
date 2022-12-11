from utils import dbBotData

commandPrefix = dbBotData.get('prefix').decode()


info = 'Show bot info: `{}info`'.format(commandPrefix)
config = 'View or change configuration (no usage example, only ever used by Cronk)'
help = 'Show help for all commands (please don\'t ask me to explain this one, just don\'t)'
history = 'Read off the history file (SHOULD BE DONE IN <#891433717665497140>)'

rules = 'Show or set rules: `{}rules` (to get server rules) | `{}rules -c #channel` (to get channel rules)'.format(commandPrefix, commandPrefix)
warn = 'Warn a user or repeal a warning: `{}warn @user -n "note (remember the quotes)"`(warn somebody) | `{}warn @user -r <warning number>` (repeal a warning)'.format(commandPrefix, commandPrefix)
warnings = 'View a user\'s warnings: `{}warnings @user`'.format(commandPrefix)
kick = 'Kick a user from the server: `{}kick @user`'.format(commandPrefix)
ban = 'Ban a user from the server: `{}ban @user`'.format(commandPrefix)
shush = 'Shush a user: `{}shush @user time` (see `{}shush --help` for time formatting)'.format(commandPrefix, commandPrefix)
language = 'Configure the language filter'
clear_alike = 'Clear all messages in all channels with the same content'

speak = 'Say something somewhere (access restricted for safety reasons)'
