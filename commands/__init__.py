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
    'mute': command_mute,
    'unmute': command_unmute,
    'shush': command_shush,
    'language': command_language,
    'embed-verify': command_embed_verify,
    'clear': command_clear,
    'clear-alike': command_clear_alike,

    'speak': command_speak,
    'impostercronk': command_impostercronk,
    'qotd-add': command_qotd_add,
    'qotd-list': command_qotd_list,
    'qotd-config': command_qotd_config,
    'qotd-ask': command_qotd_ask
}