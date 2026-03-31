import asyncio
import contextlib
import os
import tempfile
import uuid
from dataclasses import dataclass, field
from pathlib import Path

import discord
import edge_tts
from discord.ext import commands
from dotenv import load_dotenv


load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", "!")
TTS_VOICE = os.getenv("TTS_VOICE", "ko-KR-SunHiNeural")
FFMPEG_PATH = os.getenv("FFMPEG_PATH", "ffmpeg")
MAX_TTS_LENGTH = int(os.getenv("MAX_TTS_LENGTH", "300"))
TEMP_DIR = Path(os.getenv("TTS_TEMP_DIR", tempfile.gettempdir())) / "discord_tts_bot"

if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN is not set. Add it to your .env file.")

TEMP_DIR.mkdir(parents=True, exist_ok=True)

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents, help_command=None)


@dataclass
class TTSItem:
    text: str
    author_name: str
    text_channel_id: int
    file_path: Path


@dataclass
class GuildAudioState:
    queue: asyncio.Queue[TTSItem] = field(default_factory=asyncio.Queue)
    worker_task: asyncio.Task | None = None
    current_item: TTSItem | None = None


guild_states: dict[int, GuildAudioState] = {}


def get_guild_state(guild_id: int) -> GuildAudioState:
    if guild_id not in guild_states:
        guild_states[guild_id] = GuildAudioState()
    return guild_states[guild_id]


async def synthesize_tts(text: str, voice: str) -> Path:
    output_path = TEMP_DIR / f"tts_{uuid.uuid4().hex}.mp3"
    communicate = edge_tts.Communicate(text=text, voice=voice)
    await communicate.save(str(output_path))
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

    return await target_channel.connect(timeout=20, reconnect=True)


async def cleanup_file(path: Path) -> None:
    with contextlib.suppress(FileNotFoundError, PermissionError):
        path.unlink()


async def audio_player_loop(guild_id: int) -> None:
    state = get_guild_state(guild_id)

    while True:
        item = await state.queue.get()
        state.current_item = item

        guild = bot.get_guild(guild_id)
        voice_client = guild.voice_client if guild else None
        text_channel = bot.get_channel(item.text_channel_id)

        try:
            if guild is None or voice_client is None or not voice_client.is_connected():
                if text_channel:
                    await text_channel.send("음성 채널 연결이 끊겨서 재생을 멈췄어.")
                await cleanup_file(item.file_path)
                state.current_item = None
                while not state.queue.empty():
                    queued = await state.queue.get()
                    await cleanup_file(queued.file_path)
                    state.queue.task_done()
                return

            finished = asyncio.Event()

            def after_playback(error: Exception | None) -> None:
                if error and text_channel:
                    bot.loop.call_soon_threadsafe(
                        asyncio.create_task,
                        text_channel.send(f"재생 중 오류가 났어: {error}"),
                    )
                bot.loop.call_soon_threadsafe(finished.set)

            source = discord.FFmpegPCMAudio(executable=FFMPEG_PATH, source=str(item.file_path))
            voice_client.play(source, after=after_playback)
            await finished.wait()
        finally:
            await cleanup_file(item.file_path)
            state.current_item = None
            state.queue.task_done()


def ensure_worker(guild_id: int) -> None:
    state = get_guild_state(guild_id)
    if state.worker_task is None or state.worker_task.done():
        state.worker_task = asyncio.create_task(audio_player_loop(guild_id))


def sanitize_text(text: str) -> str:
    text = " ".join(text.split())
    return text[:MAX_TTS_LENGTH].strip()


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
        await ctx.reply(f"입장 실패: {exc}")


@bot.command(name="leave")
async def leave(ctx: commands.Context) -> None:
    if not ctx.guild:
        await ctx.reply("서버에서만 사용할 수 있어.")
        return

    voice_client = ctx.voice_client
    if not voice_client:
        await ctx.reply("지금 들어가 있는 음성 채널이 없어.")
        return

    state = get_guild_state(ctx.guild.id)

    if voice_client.is_playing():
        voice_client.stop()

    while not state.queue.empty():
        queued = await state.queue.get()
        await cleanup_file(queued.file_path)
        state.queue.task_done()

    await voice_client.disconnect()
    await ctx.reply("음성 채널에서 나왔어.")


@bot.command(name="say")
async def say(ctx: commands.Context, *, text: str | None = None) -> None:
    if not ctx.guild:
        await ctx.reply("서버에서만 사용할 수 있어.")
        return

    if not text:
        await ctx.reply("읽을 문장을 입력해 줘. 예: !say 안녕하세요")
        return

    clean_text = sanitize_text(text)
    if not clean_text:
        await ctx.reply("읽을 수 있는 문장이 없어.")
        return

    if len(text.strip()) > MAX_TTS_LENGTH:
        await ctx.reply(f"문장이 너무 길어서 앞 {MAX_TTS_LENGTH}자까지만 읽을게.")

    try:
        await ensure_voice_client(ctx)
        audio_path = await synthesize_tts(clean_text, TTS_VOICE)
    except Exception as exc:
        await ctx.reply(f"TTS 준비 중 오류가 났어: {exc}")
        return

    state = get_guild_state(ctx.guild.id)
    item = TTSItem(
        text=clean_text,
        author_name=ctx.author.display_name,
        text_channel_id=ctx.channel.id,
        file_path=audio_path,
    )
    await state.queue.put(item)
    ensure_worker(ctx.guild.id)

    queue_size = state.queue.qsize()
    if state.current_item is None and queue_size == 1:
        await ctx.reply(f"바로 읽을게: {clean_text[:100]}")
    else:
        await ctx.reply(f"대기열에 추가했어. 현재 대기: {queue_size}개")


@bot.command(name="skip")
async def skip(ctx: commands.Context) -> None:
    if not ctx.voice_client or not ctx.voice_client.is_playing():
        await ctx.reply("지금 재생 중인 음성이 없어.")
        return

    ctx.voice_client.stop()
    await ctx.reply("현재 음성을 건너뛰었어.")


@bot.command(name="stop")
async def stop(ctx: commands.Context) -> None:
    if not ctx.guild:
        await ctx.reply("서버에서만 사용할 수 있어.")
        return

    state = get_guild_state(ctx.guild.id)

    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()

    cleared = 0
    while not state.queue.empty():
        queued = await state.queue.get()
        await cleanup_file(queued.file_path)
        state.queue.task_done()
        cleared += 1

    await ctx.reply(f"재생을 멈추고 대기열 {cleared}개를 비웠어.")


@bot.command(name="queue")
async def queue_status(ctx: commands.Context) -> None:
    if not ctx.guild:
        await ctx.reply("서버에서만 사용할 수 있어.")
        return

    state = get_guild_state(ctx.guild.id)
    pending_items = list(state.queue._queue)

    lines = []
    if state.current_item:
        lines.append(f"지금 재생 중: {state.current_item.author_name} - {state.current_item.text[:60]}")

    if pending_items:
        lines.append("대기열:")
        for idx, item in enumerate(pending_items[:10], start=1):
            lines.append(f"{idx}. {item.author_name} - {item.text[:60]}")

    if not lines:
        await ctx.reply("대기열이 비어 있어.")
        return

    await ctx.reply("\n".join(lines))


@bot.command(name="help")
async def help_command(ctx: commands.Context) -> None:
    await ctx.reply(
        "사용 가능한 명령어\n"
        f"- {COMMAND_PREFIX}ping\n"
        f"- {COMMAND_PREFIX}join\n"
        f"- {COMMAND_PREFIX}leave\n"
        f"- {COMMAND_PREFIX}say <문장>\n"
        f"- {COMMAND_PREFIX}skip\n"
        f"- {COMMAND_PREFIX}stop\n"
        f"- {COMMAND_PREFIX}queue"
    )


bot.run(DISCORD_TOKEN)
