# Base imports
import asyncio
import os
import re
from hashlib import sha256
from typing import List, Union

# Installed Imports
import aiohttp
import discord
from discord import Attachment, DMChannel, Message, TextChannel
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID_1"))

SEEN_MESSAGES = []

LOOP_SPEED = 5


# printing hashes of secrets instead of secrets
def print_secret(secret_to_hash: Union[int, str]) -> str:
    """Returns MD5 hash of an input.
    Parameters:
    secret_to_hash (Union[int, str]) a secret whose hash should be printed

    Returns:
    hexdigest (str) hexdigest of md5 of initial secret
    """
    try:
        encoded_string = str(secret_to_hash).encode("utf-8")
        hash_object = sha256(encoded_string, usedforsecurity=False)
    except TypeError as e:
        print(f"Trouble with encoding, generating rando instead. Error:{e}")
        from random import SystemRandom
        return SystemRandom().random()
    return hash_object.hexdigest()


# Defining Discord bot
# TODO why prefix = "!" ?
# TODO maybe fewer intents are required than used.
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)


async def get_new_messages_from_channel(
        channel: TextChannel,
        num_of_messages: int
        ) -> List[Message]:
    # returns list of triplets of userID, messageID and Message string
    global SEEN_MESSAGES
    message_list = [
        message
        async for message in channel.history(limit=num_of_messages)
        if message.id not in SEEN_MESSAGES
        ]
    new_messages = [message.id for message in message_list]
    SEEN_MESSAGES = SEEN_MESSAGES + new_messages
    return message_list


def regex_check(message: str) -> bool:
    # regex pattern, currently checks for two double pipes.
    regex_pattern = r"^\s*(?:\|\|(?:[^|]|\|(?!\|))*?\|\|\s*)+\s*$"
    # find matches
    match = re.search(regex_pattern, message)
    # cast to bool
    return bool(match)


def image_check(attachments: List[Attachment]) -> bool:
    return_value = True
    for attachment in attachments:
        # can abort if any check was False
        if return_value and len(attachment.filename) > 8:
            if attachment.filename[:8] != "SPOILER_":
                return_value = False
    return return_value


async def send_warning(dm_channel: DMChannel, message_content: str):
    # direct message
    channel = "Dark Room"
    await dm_channel.send(
        f"Warning! Your message in the spoiler channel {channel} with the" +
        f"content \"{message_content}\" was not properly put in spoilers. " +
        "Make sure every image is hidden and every piece of text is between " +
        "a pair of double pipes, e.g. \"\\|\\|spoiler\\|\\|\". You have 1 " +
        "minute to edit the post.")


async def punishment(dm_channel: DMChannel, message: Message):
    # direct message + message removed
    await message.delete()
    await dm_channel.send("Consider this a warning! Message Deleted!")


async def consequences(user_id: int, message: Message, channel: TextChannel):
    # wait for correctional edits (1 minute)
    await asyncio.sleep(60)
    if not await spoiler_check(message, channel):
        # 4. Send Warning in DM
        user = bot.get_user(user_id)
        dm_channel = await bot.create_dm(user)
        await send_warning(dm_channel, message.content)
        # wait for correctional edits after message (1 minute)
        await asyncio.sleep(60)
        # 5. no correction: remove message, add strike to user
        print(message.content)
        if not await spoiler_check(message, channel):
            await punishment(dm_channel, message)


# Event decorator for discord bot to loop
@tasks.loop(seconds=LOOP_SPEED)
async def check_newest_messages(
    session: aiohttp.ClientSession,
    channel: TextChannel
) -> None:
    """ Loops and calls fetchers and sender.
    Parameters:
    channel (TextChannel): TextChannel object to send post to
    session (aiohttp.ClientSession): client session to make GET request
    """
    # TODO check session is alive at beginning of each loop

    # 1. Check for new messages
    new_msg_list = await get_new_messages_from_channel(
        channel,
        num_of_messages=20
        )

    print([msg.content for msg in new_msg_list])

    # 2. Iterate through messages:
    # TODO: these should be handelled at the same time, but currently aren't
    for message in new_msg_list:

        await iterate_through_messages(channel, message)
    print("END OF LOOP")


async def iterate_through_messages(channel, message):
    user_id = message.author.id
    message_content = message.content

    # 3. run regex on message
    allowed = await spoiler_check(message, channel)
    print(allowed, message_content, message.attachments)

    if not allowed:
        await consequences(user_id, message, channel)


async def spoiler_check(message: Message, channel: TextChannel):
    # update message contents
    message = await channel.fetch_message(message.id)

    msg_valid = regex_check(message.content)
    attachments_valid = image_check(message.attachments)
    return msg_valid and attachments_valid


# Event decorator for discord bots
@bot.event
async def on_ready():
    """ Startup configurations.Gets session and channel object,
        Populates the buffers.
    """
    # Called once when the bot is initialized
    print(
        f"Logged in as {bot.user.name} with ID ({print_secret(bot.user.id)})"
    )

    # Initialize aiohttp session
    session = aiohttp.ClientSession()
    # Get Discord Channel object
    channel = bot.get_channel(CHANNEL_ID)

    check_newest_messages.start(session, channel)

# so the file doesn't run when imported
if __name__ == "__main__":
    # But when the file is run, run the bot with its token.
    bot.run(BOT_TOKEN)
