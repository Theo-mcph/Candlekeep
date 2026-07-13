import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import pydub

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
# Paste your target Discord Server ID here to sync slash commands instantly
TEST_GUILD_ID = 1525169954276638930 

if not TOKEN:
    raise ValueError("DISCORD_TOKEN not found in your .env file")

# Setup explicitly typed intents
intents = discord.Intents.default()
intents.voice_states = True
intents.members = True
intents.message_content = True

bot = commands.Bot(
    command_prefix="!", 
    intents=intents,
    debug_guilds=[TEST_GUILD_ID] if TEST_GUILD_ID != 1525169954276638930 else None
)

active_recordings = {}

# Ensure native audio codec structures are explicitly ready
if not discord.opus.is_loaded():
    try:
        discord.opus._load_default()
    except Exception as e:
        print(f"Warning: Failed to load default Opus codec: {e}")

async def process_finished_recording(sink, *args):
    """
    Callback fired instantly when the recording stops.
    Converts and flushes the user tracks out of memory down to the machine.
    """
    print("Recording stopped. Exporting audio files...")
    
    raw_channel = args[0] if args else None
    
    # 1. Strict Type Guard: Check if the channel is a TextChannel
    if not isinstance(raw_channel, discord.TextChannel):
        print("Callback aborting: Target channel context is not a standard TextChannel.")
        return

    # 2. Type Assertion: Creates an explicit reference so the linter knows it cannot be a ForumChannel
    text_channel: discord.TextChannel = raw_channel

    if not sink.audio_data:
        await text_channel.send("⚠️ Recording ended, but no audio data was captured. Did anyone speak?")
        return

    user_mentions = []
    output_dir = "./recorded_tracks"
    os.makedirs(output_dir, exist_ok=True)

    for user_id, audio_file in sink.audio_data.items():
        user_mentions.append(f"<@{user_id}>")
        
        audio_file.file.seek(0)
        raw_pcm_data = audio_file.file.read()
        
        # Structure the binary stream into a clean WAV container
        audio_segment = pydub.AudioSegment(
            data=raw_pcm_data,
            sample_width=2,      # 16-bit audio
            frame_rate=48000,    # Discord standard frequency
            channels=2           # Pycord decodes natively into stereo channels
        )
        
        local_filepath = os.path.join(output_dir, f"{user_id}.wav")
        audio_segment.export(local_filepath, format="wav")
        print(f"File written successfully: {local_filepath}")

    await text_channel.send(f"Recorded separate tracks for: {', '.join(user_mentions)}. Check `{output_dir}/` folder.")

@bot.event
async def on_ready():
    print(f"Bot is online and ready under account: {bot.user}")

@bot.slash_command(name="join", description="Bring the bot into your voice channel")
async def join(ctx: discord.ApplicationContext):
    if not isinstance(ctx.author, discord.Member):
        return await ctx.respond("This command can only be used in a server channel!")

    if not ctx.author.voice or not ctx.author.voice.channel:
        return await ctx.respond("You must join a Voice Channel first!")
    
    # Defer to prevent the command response from getting stuck loading
    await ctx.defer()
    await ctx.author.voice.channel.connect()
    await ctx.followup.send("Joined voice channel!")

@bot.slash_command(name="start", description="Begin multi-track voice logging")
async def start(ctx: discord.ApplicationContext):
    if not isinstance(ctx.author, discord.Member) or not ctx.guild:
        return await ctx.respond("This command can only be used in a server channel!")

    voice_client = ctx.guild.voice_client
    if not voice_client:
        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.respond("You must join a Voice Channel first!")
        voice_client = await ctx.author.voice.channel.connect()
        
    if ctx.guild.id in active_recordings:
        return await ctx.respond("Already capturing audio in this server!")

    await ctx.respond("Recording initialized! Speak naturally.")
    
    sink = discord.sinks.WaveSink()
    voice_client.start_recording(
        sink,
        process_finished_recording,
        ctx.channel
    )
    active_recordings[ctx.guild.id] = sink

@bot.slash_command(name="stop", description="Halt recording and save tracks")
async def stop(ctx: discord.ApplicationContext):
    if not ctx.guild:
        return await ctx.respond("This command can only be used in a server channel!")

    voice_client = ctx.guild.voice_client
    if not voice_client or ctx.guild.id not in active_recordings:
        return await ctx.respond("No active recording session found.")

    await ctx.respond("Processing files...")
    active_recordings.pop(ctx.guild.id, None)
    voice_client.stop_recording()

@bot.slash_command(name="leave", description="Exit the voice channel")
async def leave(ctx: discord.ApplicationContext):
    if not ctx.guild:
        return await ctx.respond("This command can only be used in a server channel!")

    voice_client = ctx.guild.voice_client
    if voice_client:
        active_recordings.pop(ctx.guild.id, None)
        await voice_client.disconnect()
        await ctx.respond("Left voice channel.")
    else:
        await ctx.respond("I'm not in a voice channel.")

bot.run(TOKEN)