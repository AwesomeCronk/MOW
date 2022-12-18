from .system import *
from .moderation import *
from .fun import *

commands = {
    'info': command_info,
    'config': command_config,
    'help': command_help,
    'history': command_history,

    'rules': command_rules,
    'warn': command_warn,
    'warnings': command_warnings,
    'kick': command_kick,
    'ban': command_ban,
    'shush': command_shush,
    'language': command_language,
    'embed-verify': command_embed_verify,
    'clear-alike': command_clear_alike,

    'speak': command_speak
}