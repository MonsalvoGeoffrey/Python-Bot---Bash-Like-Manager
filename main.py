# This example requires the 'message_content' intent.

from dotenv import load_dotenv
load_dotenv()

import os
import discord
from discord import Message
from typing import List, Optional, Any, Tuple
import shlex
import asyncio


async def exec_command(message:Message, raw_arguments: list[str], stdin: Optional[List[str]]=None):
    stdin = stdin or []
    stdout: List[str] = []
    command = raw_arguments.pop(0)
    pos_args: List[str] = []
    char_args: List[Tuple[str, str | None]] = []
    word_args: List[Tuple[str, str | None]] = []

    state = "pos"
    cur_arg = ""

    while len(raw_arguments) > 0:
        next_arg = raw_arguments.pop(0)
        if next_arg == "|":
            if state == "word":
                word_args.append((cur_arg, None))
            elif state == "char":
                char_args.append((cur_arg, None))
            break

        if next_arg.startswith("--"):
            if state == "word":
                word_args.append((cur_arg, None))
            elif state == "char":
                char_args.append((cur_arg, None))
            state = "word"
            cur_arg = next_arg[2:]
            continue

        if next_arg.startswith("-"):
            if state == "word":
                word_args.append((cur_arg, None))
            elif state == "char":
                char_args.append((cur_arg, None))
            state = "char"
            cur_arg = next_arg[1:]
            continue

        if state == "word":
            word_args.append((cur_arg, next_arg))
        elif state == "char":
            char_args.append((cur_arg, next_arg))
        else:
            pos_args.append(next_arg)
        state = "pos"

    if state == "word":
        word_args.append((cur_arg, None))
    elif state == "char":
        char_args.append((cur_arg, None))


    if command == "debug":
        stdout.append(f"""
Command: {command}
Positional Arguments: {str(pos_args)}
Character Arguments: {str(char_args)}
Word Arguments: {str(word_args)}
Next Command: {str(raw_arguments)}
""")
        # await message.reply(response)
    if command == "sleep":
        await asyncio.sleep(int(pos_args[0]) if len(pos_args) > 0 else 1)
    elif command == "echo":
        await message.reply(" ".join(pos_args))


    if len(raw_arguments) > 0:
        await exec_command(message, raw_arguments, stdout)
    else:
        for output in stdout:
            await message.reply(output)
    # print(raw_arguments)



class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_message(self, message: Message):
        if message.author.bot:
            return
        print(f'Message from {message.author}: {message.content}')
        raw_arguments = shlex.split(message.content)
        if raw_arguments[0] == "exec":
            await exec_command(message, raw_arguments[1:])


intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)

TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN == None:
    raise BaseException("Something's wrong with the token !!!")

client.run(TOKEN)
