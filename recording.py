import functools
import io
import os

import pydub  # pip install pydub==0.25.1

import discord
from discord.sinks import MP3Sink
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

bot = discord.Bot()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


async def finished_callback(error: Exception | None, sink: MP3Sink, channel: discord.TextChannel):
    if error:
        print(f"Recording error: {error}")
        return

    mention_strs = []
    audio_segs: list[pydub.AudioSegment] = []
    files: list[discord.File] = []
    longest = pydub.AudioSegment.empty()

    for user_id, audio in sink.audio_data.items():
        mention_strs.append(f"<@{user_id}>")
        seg = pydub.AudioSegment.from_file(audio.file, format="mp3")
        # Determine the longest audio segment
        if len(seg) > len(longest):
            audio_segs.append(longest)
            longest = seg
        else:
            audio_segs.append(seg)
        audio.file.seek(0)
        files.append(discord.File(audio.file, filename=f"{user_id}.mp3"))

    for seg in audio_segs:
        longest = longest.overlay(seg)

    with io.BytesIO() as f:
        longest.export(f, format="mp3", parameters=["-f", "mp3"])
        f.seek(0)
        await channel.send(
            f"Finished! Recorded audio for {', '.join(mention_strs)}.",
            files=files + [discord.File(f, filename="recording.mp3")],
        )


@bot.command()
async def join(ctx: discord.ApplicationContext):
    """Candlekeep joins the voice channel!"""
    if not isinstance(ctx.author, discord.Member):
        return await ctx.respond("This command only works in a server.")

    voice = ctx.author.voice
    if not voice or not voice.channel:
        return await ctx.respond("You're not in a vc right now")

    await ctx.defer()
    await voice.channel.connect()
    await ctx.respond("Joined!")


@bot.command()
async def start(ctx: discord.ApplicationContext):
    """Record the voice channel!"""
    if not isinstance(ctx.author, discord.Member):
        return await ctx.respond("This command only works in a server.")

    voice = ctx.author.voice
    if not voice or not voice.channel:
        return await ctx.respond("You're not in a vc right now")

    vc = ctx.voice_client
    if not vc:
        return await ctx.respond(
            "I'm not in a vc right now. Use `/join` to make me join!"
        )

    if not isinstance(ctx.channel, discord.TextChannel):
        return await ctx.respond("This command only works in a regular text channel")

    await ctx.defer()

    sink = MP3Sink()
    vc.start_recording(
        sink,
        functools.partial(finished_callback, sink=sink, channel=ctx.channel),
    )

    await ctx.respond("The recording has started!")


@bot.command()
async def stop(ctx: discord.ApplicationContext):
    """Stop the recording"""
    vc = ctx.voice_client
    if not vc:
        return await ctx.respond("There's no recording going on right now")

    vc.stop_recording()

    await ctx.respond("The recording has stopped!")


@bot.command()
async def leave(ctx: discord.ApplicationContext):
    """Leave the voice channel!"""
    vc = ctx.voice_client
    if not vc:
        return await ctx.respond("I'm not in a vc right now")

    await vc.disconnect()

    await ctx.respond("Left!")


bot.run(TOKEN)