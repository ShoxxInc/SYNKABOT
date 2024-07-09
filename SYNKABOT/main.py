# Base imports
import asyncio
import os
import re
from hashlib import sha256
from typing import List, Union

# Installed Imports
import discord
from discord import Attachment, DMChannel, Message, TextChannel
from discord.ext import commands
from dotenv import load_dotenv

# load environment variables
load_dotenv()

# Globals
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID_1"))
SEEN_MESSAGES = []
LOOP_SPEED = 5
GLOBAL_SLEEP_TIMER = 60


# printing hashes of secrets instead of secrets
def print_secret(secret_to_hash: Union[int, str]) -> str:
    """Returns SHA256 hash of an input.
    Parameters:
    secret_to_hash (Union[int, str]) a secret whose hash should be printed

    Returns:
    hexdigest (str) hexdigest of SHA256 of initial secret
    """
    try:
        encoded_string = str(secret_to_hash).encode("utf-8")
        hash_object = sha256(encoded_string)
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


def regex_check(message: str) -> bool:
    """Checks message for spoiler contents.
    Parameters:
    message (str): message that needs to be spoilered strings and line breaks

    Returns:
    (bool) whether or not the message was spoilered correctly
    """
    # TODO quick hack for edge cases not caught by regex.
    # To be incorporated into Regex
    if message == "":
        return True
    if message == "||||":
        return False
    # regex pattern, currently checks for two double pipes.
    regex_pattern = r"^\s*(?:\|\|(?:[^|]|\|(?!\|))*?\|\|\s*)+\s*$"
    # find matches
    match = re.search(regex_pattern, message)
    # cast to bool
    return bool(match)


def image_check(attachments: List[Attachment]) -> bool:
    """Checks that all attachments have been spoiler tagged.
    Parameters:
    attachments: (List[Attachment]): list of images attached to the message

    Returns:
    (bool) whether or not the attachements were spoilered correctly
    """
    return_value = True
    for attachment in attachments:
        # can abort if any check was False
        if return_value and len(attachment.filename) > 8:
            if attachment.filename[:8] != "SPOILER_":
                return_value = False
    return return_value


async def send_warning(dm_channel: DMChannel, message_content: str):
    """CORO Sends a warning DM to poster of non-spoiled message
    Parameters:
    dm_channel: (DMChannel):    list of images attached to the message
    message_content: (str):     bad message
    """
    channel = "Dark Room"
    await dm_channel.send(
        f"Warning! Your message in the spoiler channel {channel} with the" +
        f"content \"{message_content}\" was not properly put in spoilers. " +
        "Make sure every image is hidden and every piece of text is between " +
        "a pair of double pipes, e.g. \"\\|\\|spoiler\\|\\|\". You have 1 " +
        "minute to edit the post.")


async def punishment(dm_channel: DMChannel, message: Message):
    """CORO Deletes the message and sends second warning DM
    Parameters:
    dm_channel: (DMChannel):    List of images attached to the message
    messaget: (Message):        Message to delete
    """
    await message.delete()
    await dm_channel.send("Consider this a warning! Message Deleted!")


async def consequences(user_id: int, message: Message, channel: TextChannel):
    """CORO Checks that all attachments have been spoiler tagged.
    Parameters:
    user_id: (int):         id of user whose message was initially flagged.
    message: (Message):     initially flagged message
    channel: (TextChannel): channel in which violation occured
    """
    await asyncio.sleep(GLOBAL_SLEEP_TIMER)
    if not await spoiler_check(message, channel):
        # 4. Send Warning in DM
        user = bot.get_user(user_id)
        dm_channel = await bot.create_dm(user)
        await send_warning(dm_channel, message.content)
        # wait for correctional edits after message (1 minute)
        await asyncio.sleep(GLOBAL_SLEEP_TIMER)
        # 5. no correction: remove message, add strike to user
        print(message.content)
        if not await spoiler_check(message, channel):
            await punishment(dm_channel, message)


async def treat_message(channel: TextChannel, message: Message):
    """CORO Checks every message in the channel
    Parameters:
    channel: (TextChannel): channel where a message was sent
    message: (Message):     message that was sent
    """
    message_content = message.content

    # 3. run regex on message, check images
    allowed = await spoiler_check(message, channel)
    print(allowed, message_content, message.attachments)

    if not allowed:
        user_id = message.author.id
        await consequences(user_id, message, channel)


async def spoiler_check(message: Message, channel: TextChannel):
    """Checks that both text and images are correctly spoilered.
    Parameters:
    channel: (TextChannel): channel where a message was sent
    message: (Message):     message that was sent

    Returns:
    (bool): whether message is accepted or not
    """
    # update message contents, required because user may edit message.
    message = await channel.fetch_message(message.id)

    msg_valid = regex_check(message.content)
    attachments_valid = image_check(message.attachments)
    return msg_valid and attachments_valid


# Event decorator for discord bots
@bot.event
async def on_ready():
    """CORO Startup configurations. Send status message"""
    # Called once when the bot is initialized
    print(
        f"Logged in as {bot.user.name} with ID ({print_secret(bot.user.id)})"
    )


@bot.event
async def on_message(message: Message):
    """CORO Event listener that catches every message sent on the server.
    Parameters:
    message: (Message): Message to treat"""
    print(message)
    # Only treat messages in the designated spoiler channel.
    if message.channel.id == CHANNEL_ID:
        await treat_message(message.channel, message)


# so the file doesn't run when imported
if __name__ == "__main__":
    # But when the file is run, run the bot with its token.
    bot.run(BOT_TOKEN)
