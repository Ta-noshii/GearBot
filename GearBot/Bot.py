import os
import traceback

import discord
import sys

from commands.OwnerCommands import Stop, Upgrade
from commands.command import Command
from commands import CustomCommands
from commands.ping import Ping
from commands.util import prefix
from functions import configuration, spam


class Help(Command):
    def __init__(self):
        super().__init__("Shows help")

    async def execute(self, client, channel, user, params):
        inf = "**Available commands:**\n------------------------------------\n"
        for key in commands:
            if commands[key].canExecute(user):
                inf += f"{key} : {commands[key].help}\n"
        cCommands = CustomCommands.getCommands(channel.server)
        if len(cCommands.keys()):
            inf += "\n**Other commands:**\n------------------------------------\n"
            for key in cCommands:
                inf += f"{key}\n"

        await client.send_message(channel, inf)


client = discord.Client()

commands = {
    "ping": Ping(),
    "stop": Stop(),
    "upgrade": Upgrade(),
    "help": Help(),
    # "add": AddCustomCommand(),
    # "remove": RemoveCustomCommand()
}


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    print('Do not create custom commands that might interfere with the commands of other bots')
    print('You can report an Issue/Bug on the GearBot repository (https://github.com/AEnterprise/Gearbot)')
    print('This bot is made by Slak#9006 & AEnterprise#4693')
    print('------')

    for server in client.servers:
        if not configuration.hasconfig(server):
            configuration.createconfigserver(server, True)

    global info
    info = await client.application_info()
    global debugMode
    debugMode = (info.name == 'SlakBotTest') | (info.name == 'Parrot test')


@client.event
async def on_message(message):
    if (message.content is None) or (message.content == ''):
        return
    elif not (message.content.startswith(prefix) and message.channel.is_private):
        await spam.check_for_spam(client, message)

    if message.content.startswith(prefix):
        cmd, *args = message.content[1:].split()
        print(f"command '{cmd}' with arguments {args} issued")
    else:
        return

    try:
        if cmd in commands.keys():
            command = commands[cmd]
            if command.canExecute(message.author):
                await command.execute(client, message.channel, message.author, cmd)
            else:
                await client.send_message(message.channel, "You do not have permission to execute this command")
        else:
            custom_commands = CustomCommands.getCommands(message.channel.server)
            if cmd in custom_commands.keys():
                await client.send_message(message.channel, custom_commands[cmd])
                return
            print(f"command '{cmd}' not recognized")
    except discord.Forbidden as e:
        print("Exception: Bot is not allowed to send messages")
        on_command_error(message.channel, cmd, args, e)
    except discord.InvalidArgument as e:
        on_command_error(message.channel, cmd, args, e)
        print("Exception: Invalid message arguments")
    except Exception as e:
        await on_command_error(message.channel, cmd, args, e)
        traceback.print_exc()


async def on_command_error(channel, cmd, args, exception):
    global client
    try:
        print("Command execution failed:"
              f"    Command: {cmd}"
              f"    Arguments: {args}"
              f"    Channel: {channel.name}"
              f"    Server: {channel.server}"
              f"    Exception: {exception}")
        await client.send_message(channel, f"Execution of the {cmd} command failed, please try again later")
    except Exception as e:
        print("Failed to notify caller:")
        print(e)


if __name__ == '__main__':
    try:
        token = os.environ['gearbotlogin']
    except KeyError:
        token = input("Please enter your Discord token: ")
    client.run(token)
