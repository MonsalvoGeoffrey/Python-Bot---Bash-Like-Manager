# This example requires the 'message_content' intent.

from dotenv import load_dotenv
load_dotenv()

import os
import discord
from discord import Message
from typing import List, Optional, Tuple, Match
import shlex
import asyncio
import re




# equivalent of shlex_split that preserve expressions
def custom_shlex_split(s: str):
    # Improved pattern to match:
    # 1. Quoted strings (both single and double quotes) and return without quotes
    # 2. $(expressions) including nested ones
    # 3. Non-space sequences (words)
    pattern = r"""(?:'([^']*)'|"([^"]*)"|(\$\((?:[^()]|\([^()]*\))*\))|(\S+))"""
    matches = re.findall(pattern, s)
    # Flatten the list of tuples, filter out empty strings, and concatenate non-empty matches
    return ["".join(match) for match in matches if any(match)]





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

        expression_match: Optional[Match[str]] = re.match(r'^\$\((.*)\)$', next_arg)
        if expression_match:
            # Extract the content of the expression without the $( and )
            content = expression_match.group(1)
            out = await exec_command(message, custom_shlex_split(content))
            if out:
                out.reverse()
                for output in out:
                    raw_arguments.insert(0, output)
            continue

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
    elif command == "sum":
        res = 0
        for num in pos_args:
            res += int(num)
        stdout.append(str(res))



    if len(raw_arguments) > 0:
        await exec_command(message, raw_arguments, stdout)
    else:
        # for output in stdout:
            # await message.reply(output)
        return stdout

    # print(raw_arguments)



class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_message(self, message: Message):
        if message.author.bot:
            return
        print(f'Message from {message.author}: {message.content}')
        raw_arguments = custom_shlex_split(message.content)
        if raw_arguments[0] == "exec":
            stdout = await exec_command(message, raw_arguments[1:])
            if not stdout:
                return
            for output in stdout:
                await message.reply(output)


intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)

TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN == None:
    raise BaseException("Something's wrong with the token !!!")

client.run(TOKEN)
