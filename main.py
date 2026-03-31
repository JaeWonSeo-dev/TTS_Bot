import os
import tempfile
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv
from gtts import gTTS


load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", "!")
TTS_LANGUAGE = os.getenv("TTS_LANGUAGE", "ko")

if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN is not set. Add it to your .env file.")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents, help_command=None)


def build_tts_file(text: str, lang: str) -> Path:
    temp_dir = Path(tempfile.gettempdir()) / "discord_tts_bot"
    temp_dir.mkdir(parents=True, exist_ok=True)

    output_path = temp_dir / "tts_output.mp3"
    tts = gTTS(text=text, lang=lang)
    tts.save(str(output_path))
    return output_path


async def ensure_voice_client(ctx: commands.Context) -> discord.VoiceClient:
    if not ctx.author.voice or not ctx.author.voice.channel:
        raise RuntimeError("먼저 음성 채널에 들어가 주세요.")

    target_channel = ctx.author.voice.channel
    voice_client = ctx.voice_client

    if voice_client and voice_client.channel != target_channel:
        await voice_client.move_to(target_channel)
        return voice_client

    if voice_client:
        return voice_client

    return await target_channel.connect()


@bot.event
async def on_ready() -> None:
    print(f"Logged in as {bot.user}")


@bot.command(name="ping")
async def ping(ctx: commands.Context) -> None:
    await ctx.reply("pong")


@bot.command(name="join")
async def join(ctx: commands.Context) -> None:
    try:
        await ensure_voice_client(ctx)
        await ctx.reply("음성 채널에 들어왔어.")
    except Exception as exc:
        await ctx.reply(str(exc))


@bot.command(name="leave")
async def leave(ctx: commands.Context) -> None:
    if not ctx.voice_client:
        await ctx.reply("지금 들어가 있는 음성 채널이 없어.")
        return

    await ctx.voice_client.disconnect()
    await ctx.reply("음성 채널에서 나왔어.")


@bot.command(name="say")
async def say(ctx: commands.Context, *, text: str | None = None) -> None:
    if not text:
        await ctx.reply("읽을 문장을 입력해 줘. 예: !say 안녕하세요")
        return

    try:
        voice_client = await ensure_voice_client(ctx)
    except Exception as exc:
        await ctx.reply(str(exc))
        return

    if voice_client.is_playing():
        voice_client.stop()

    try:
        audio_path = build_tts_file(text, TTS_LANGUAGE)
        source = discord.FFmpegPCMAudio(str(audio_path))
        voice_client.play(source)
        await ctx.reply(f"읽는 중: {text[:100]}")
    except Exception as exc:
        await ctx.reply(f"TTS 재생 중 오류가 났어: {exc}")


@bot.command(name="help")
async def help_command(ctx: commands.Context) -> None:
    await ctx.reply(
        "사용 가능한 명령어\n"
        f"- {COMMAND_PREFIX}ping\n"
        f"- {COMMAND_PREFIX}join\n"
        f"- {COMMAND_PREFIX}leave\n"
        f"- {COMMAND_PREFIX}say <문장>"
    )


bot.run(DISCORD_TOKEN)
