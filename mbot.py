import os
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
import yt_dlp

load_dotenv()
TOKEN = os.getenv("MUSIC_BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='?', intents=intents)

guild_id = None  # Set your server's guild ID here for faster slash command registration

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=guild_id)) if guild_id else await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(f'Error syncing commands: {e}')

@bot.command(name='music-play', help='Play music by title or link')
async def music_play(ctx, *, query: str):
    user = ctx.author
    voice_state = user.voice
    if not voice_state or not voice_state.channel:
        await ctx.send('❌ Please join a voice channel first!')
        return

    channel = voice_state.channel
    # Connect to voice channel if not already connected
    if ctx.voice_client is None:
        try:
            vc = await channel.connect()
        except Exception as e:
            await ctx.send(f'❌ Could not join voice channel: {e}')
            return
    else:
        vc = ctx.voice_client
        if vc.channel != channel:
            await vc.move_to(channel)

    await ctx.send(f'🔍 Searching for: {query}')

    # Search YouTube for the query
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'default_search': 'ytsearch',
        'quiet': True,
        'extract_flat': 'in_playlist',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(query, download=False)
            if 'entries' in info:
                info = info['entries'][0]  # Take first result
            url = info['url'] if 'url' in info else info['webpage_url']
            title = info.get('title', 'Unknown Title')
            webpage_url = info.get('webpage_url', None)
            thumbnail = info.get('thumbnail', None)
        except Exception as e:
            await ctx.send(f'❌ Could not find or play "{query}": {e}')
            return

    # Prepare FFmpeg audio source
    ffmpeg_options = {
        'options': '-vn',
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
    }
    try:
        audio_source = await discord.FFmpegOpusAudio.from_probe(url, **ffmpeg_options)
    except Exception as e:
        await ctx.send(f'❌ Error preparing audio: {e}')
        return

    # Play audio
    try:
        if vc.is_playing():
            vc.stop()
        vc.play(audio_source)
    except Exception as e:
        await ctx.send(f'❌ Error playing audio: {e}')
        return

    # Send embed with song info
    embed = discord.Embed(title='Now Playing', description=f'[{title}]({webpage_url})', color=0x1DB954)
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    embed.set_footer(text=f'Requested by {user.display_name}', icon_url=user.display_avatar.url)
    await ctx.send(embed=embed)

@bot.command(name='music-help', help='Show help for music commands')
async def music_help(ctx):
    embed = discord.Embed(title='Music Bot Help', color=0x1DB954)
    embed.add_field(name='?music-play [title or link]', value='Play a song by title or link.', inline=False)
    embed.add_field(name='?music-skip', value='Skip the current song.', inline=False)
    embed.add_field(name='?music-pause', value='Pause the current song.', inline=False)
    embed.add_field(name='?music-resume', value='Resume playback.', inline=False)
    embed.add_field(name='?music-stop', value='Stop playback and clear the queue.', inline=False)
    embed.add_field(name='?music-nowplaying', value='Show info about the currently playing song.', inline=False)
    embed.set_footer(text='Use ?music-play to get started!')
    await ctx.send(embed=embed)

@bot.command(name='music-skip', help='Skip the current song.')
async def music_skip(ctx):
    await ctx.send('⏭️ Skipping the current song... (not implemented yet)')

@bot.command(name='music-pause', help='Pause the current song.')
async def music_pause(ctx):
    await ctx.send('⏸️ Pausing the current song... (not implemented yet)')

@bot.command(name='music-resume', help='Resume playback.')
async def music_resume(ctx):
    await ctx.send('▶️ Resuming playback... (not implemented yet)')

@bot.command(name='music-stop', help='Stop playback and clear the queue.')
async def music_stop(ctx):
    await ctx.send('⏹️ Stopping playback and clearing the queue... (not implemented yet)')

@bot.command(name='music-nowplaying', help='Show info about the currently playing song.')
async def music_nowplaying(ctx):
    await ctx.send('🎶 Now playing info... (not implemented yet)')

bot.run(TOKEN)
