import asyncio
import contextlib
import json
import os
import tempfile
import uuid
from dataclasses import dataclass, field
from pathlib import Path

import discord
import edge_tts
from discord.errors import ConnectionClosed
from discord.ext import commands
from dotenv import load_dotenv

try:
    import davey  # type: ignore
except ImportError:
    davey = None  # type: ignore


load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", "!")
DEFAULT_TTS_ENGINE = os.getenv("TTS_ENGINE", "edge")
DEFAULT_TTS_VOICE = os.getenv("TTS_VOICE", "ko-KR-SunHiNeural")
FFMPEG_PATH = os.getenv("FFMPEG_PATH", "ffmpeg")
MAX_TTS_LENGTH = int(os.getenv("MAX_TTS_LENGTH", "300"))
DEBUG_LOG = os.getenv("DEBUG_LOG", "false").strip().lower() in {"1", "true", "yes", "on"}
TEMP_DIR = Path(os.getenv("TTS_TEMP_DIR", tempfile.gettempdir())) / "discord_tts_bot"
DATA_DIR = Path(os.getenv("TTS_DATA_DIR", "data"))
SAMPLES_DIR = Path(os.getenv("TTS_SAMPLES_DIR", "voice_samples"))
CONFIG_PATH = DATA_DIR / "guild_settings.json"

SUPPORTED_ENGINES = {
    "edge": {
        "label": "Microsoft Edge TTS",
        "voices": {
            "ko_female_1": "ko-KR-SunHiNeural",
            "ko_female_2": "ko-KR-JiMinNeural",
            "ko_male_1": "ko-KR-InJoonNeural",
            "ko_male_2": "ko-KR-BongJinNeural",
            "en_female_1": "en-US-JennyNeural",
            "en_male_1": "en-US-GuyNeural",
        },
        "language_defaults": {
            "ko": "ko_female_1",
            "en": "en_female_1",
        },
    }
}

if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN is not set. Add it to your .env file.")

TEMP_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

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
guild_settings: dict[str, dict] = {}


def debug_log(message: str) -> None:
    if DEBUG_LOG:
        print(f"[DEBUG] {message}")


def load_settings() -> dict[str, dict]:
    if not CONFIG_PATH.exists():
        return {}
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_settings() -> None:
    with CONFIG_PATH.open("w", encoding="utf-8") as f:
        json.dump(guild_settings, f, ensure_ascii=False, indent=2)


def get_default_voice_id() -> str:
    for voice_id, provider_voice in SUPPORTED_ENGINES[DEFAULT_TTS_ENGINE]["voices"].items():
        if provider_voice == DEFAULT_TTS_VOICE:
            return voice_id
    return next(iter(SUPPORTED_ENGINES[DEFAULT_TTS_ENGINE]["voices"]))


def get_guild_config(guild_id: int) -> dict:
    key = str(guild_id)
    if key not in guild_settings:
        guild_settings[key] = {
            "read_channel_id": None,
            "tts_engine": DEFAULT_TTS_ENGINE,
            "voice_id": get_default_voice_id(),
            "autojoin": False,
            "xsaid": False,
            "multilang": True,
        }
        save_settings()
    return guild_settings[key]


def get_guild_state(guild_id: int) -> GuildAudioState:
    if guild_id not in guild_states:
        guild_states[guild_id] = GuildAudioState()
    return guild_states[guild_id]


def resolve_voice(engine: str, voice_id: str) -> str:
    engine_info = SUPPORTED_ENGINES.get(engine)
    if not engine_info:
        raise ValueError(f"지원하지 않는 엔진이야: {engine}")

    provider_voice = engine_info["voices"].get(voice_id)
    if not provider_voice:
        raise ValueError(f"지원하지 않는 voice_id야: {voice_id}")

    return provider_voice


def detect_language(text: str) -> str:
    has_korean = any("가" <= ch <= "힣" for ch in text)
    has_english = any("a" <= ch.lower() <= "z" for ch in text)

    if has_korean:
        return "ko"
    if has_english:
        return "en"
    return "ko"


def choose_voice_id_for_text(config: dict, text: str) -> str:
    if not config.get("multilang", True):
        return config["voice_id"]

    engine = config["tts_engine"]
    language = detect_language(text)
    return SUPPORTED_ENGINES[engine]["language_defaults"].get(language, config["voice_id"])


async def synthesize_tts(text: str, engine: str, voice_id: str) -> Path:
    output_path = TEMP_DIR / f"tts_{uuid.uuid4().hex}.mp3"

    if engine == "edge":
        provider_voice = resolve_voice(engine, voice_id)
        communicate = edge_tts.Communicate(text=text, voice=provider_voice)
        try:
            await communicate.save(str(output_path))
        except Exception as exc:
            with contextlib.suppress(FileNotFoundError, PermissionError):
                output_path.unlink()

            message = str(exc)
            if "403" in message:
                raise RuntimeError(
                    "Edge TTS 요청이 차단됐어(HTTP 403). edge-tts를 최신 버전으로 업데이트하고 다시 실행해 봐."
                ) from exc
            raise RuntimeError(f"TTS 합성 실패: {exc}") from exc
        return output_path

    raise RuntimeError(f"아직 구현되지 않은 엔진이야: {engine}")


async def connect_voice_channel(guild: discord.Guild, target_channel: discord.VoiceChannel | discord.StageChannel) -> discord.VoiceClient:
    voice_client = guild.voice_client

    if voice_client and voice_client.channel == target_channel and voice_client.is_connected():
        return voice_client

    if voice_client:
        try:
            if voice_client.is_connected() and voice_client.channel != target_channel:
                await voice_client.move_to(target_channel)
                return voice_client
        except Exception as exc:
            debug_log(f"voice move failed, resetting voice client: {exc}")

        with contextlib.suppress(Exception):
            await voice_client.disconnect(force=True)

        await asyncio.sleep(0.5)

    try:
        return await target_channel.connect(timeout=20, reconnect=True)
    except ConnectionClosed as exc:
        code = getattr(exc, "code", None)
        if code == 4017:
            raise RuntimeError(
                "Discord 음성 서버가 DAVE(E2EE) 프로토콜을 요구해서 연결을 거부했어 (4017). "
                "봇 프로세스를 완전히 종료한 뒤 다시 실행해서 최신 discord.py/davey가 실제로 로드되게 해야 해. "
                "그래도 계속 4017이면 현재 음성 스택으로는 이 채널 연결이 안 되는 상태야."
            ) from exc
        debug_log(f"voice connect first attempt failed: {exc}")
    except Exception as first_exc:
        debug_log(f"voice connect first attempt failed: {first_exc}")
        stale_voice_client = guild.voice_client
        if stale_voice_client:
            with contextlib.suppress(Exception):
                await stale_voice_client.disconnect(force=True)
            await asyncio.sleep(1.0)
        try:
            return await target_channel.connect(timeout=20, reconnect=True)
        except ConnectionClosed as exc:
            code = getattr(exc, "code", None)
            if code == 4017:
                raise RuntimeError(
                    "Discord 음성 서버가 DAVE(E2EE) 프로토콜을 요구해서 연결을 거부했어 (4017). "
                    "봇 프로세스를 완전히 종료한 뒤 다시 실행해서 최신 discord.py/davey가 실제로 로드되게 해야 해. "
                    "그래도 계속 4017이면 현재 음성 스택으로는 이 채널 연결이 안 되는 상태야."
                ) from exc
            raise

    stale_voice_client = guild.voice_client
    if stale_voice_client:
        with contextlib.suppress(Exception):
            await stale_voice_client.disconnect(force=True)
        await asyncio.sleep(1.0)
    return await target_channel.connect(timeout=20, reconnect=True)


async def ensure_voice_client(ctx: commands.Context) -> discord.VoiceClient:
    if not ctx.author.voice or not ctx.author.voice.channel:
        raise RuntimeError("먼저 음성 채널에 들어가 주세요.")

    return await connect_voice_channel(ctx.guild, ctx.author.voice.channel)


async def connect_to_member_voice_channel(guild: discord.Guild, member: discord.Member) -> discord.VoiceClient:
    voice_state = getattr(member, "voice", None)
    if not voice_state or not voice_state.channel:
        raise RuntimeError("사용자가 음성 채널에 없어 자동 연결할 수 없어.")

    return await connect_voice_channel(guild, voice_state.channel)


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


def build_channel_read_text(message: discord.Message) -> str:
    config = get_guild_config(message.guild.id)
    content = sanitize_text(message.content)
    if config.get("xsaid", False):
        return f"{message.author.display_name}. {content}"
    return content


async def enqueue_tts(guild: discord.Guild, channel_id: int, text: str, author_name: str) -> int:
    config = get_guild_config(guild.id)
    voice_id = choose_voice_id_for_text(config, text)
    audio_path = await synthesize_tts(text, config["tts_engine"], voice_id)

    state = get_guild_state(guild.id)
    item = TTSItem(
        text=text,
        author_name=author_name,
        text_channel_id=channel_id,
        file_path=audio_path,
    )
    await state.queue.put(item)
    ensure_worker(guild.id)
    debug_log(f"queue size now {state.queue.qsize()} for guild={guild.id}")
    return state.queue.qsize()


def describe_voice(engine: str, voice_id: str) -> str:
    provider_voice = resolve_voice(engine, voice_id)
    return f"{voice_id} ({provider_voice})"


@bot.event
async def on_ready() -> None:
    global guild_settings
    guild_settings = load_settings()
    print(f"Logged in as {bot.user}")
    print(
        "[startup] "
        f"discord.py={discord.__version__} "
        f"edge_tts={getattr(edge_tts, '__version__', 'unknown')} "
        f"davey={getattr(davey, '__version__', 'missing') if davey else 'missing'}"
    )


@bot.event
async def on_message(message: discord.Message) -> None:
    if message.author.bot or not message.guild:
        return

    debug_log(
        f"on_message guild={message.guild.id} channel={message.channel.id} author={message.author.display_name} content={message.content[:80]!r}"
    )
    await bot.process_commands(message)

    config = get_guild_config(message.guild.id)
    read_channel_id = config.get("read_channel_id")
    if not read_channel_id:
        debug_log("skip: no read_channel_id configured")
        return

    if message.channel.id != read_channel_id:
        debug_log(f"skip: channel {message.channel.id} != configured read channel {read_channel_id}")
        return

    if message.content.startswith(COMMAND_PREFIX):
        debug_log("skip: command message in read channel")
        return

    if not message.content.strip():
        debug_log("skip: empty message content")
        return

    voice_state = getattr(message.author, "voice", None)
    if not voice_state or not voice_state.channel:
        debug_log("skip: author is not in a voice channel")
        return

    text = build_channel_read_text(message)
    if not text:
        debug_log("skip: build_channel_read_text returned empty")
        return

    enqueue_task = asyncio.create_task(
        enqueue_tts(message.guild, message.channel.id, text, message.author.display_name)
    )

    try:
        await connect_to_member_voice_channel(message.guild, message.author)
    except Exception as exc:
        enqueue_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await enqueue_task
        debug_log(f"voice connect failed: {exc}")
        await message.channel.send(f"음성 채널 자동 연결 중 오류가 났어: {exc}")
        return

    try:
        await enqueue_task
    except Exception as exc:
        debug_log(f"enqueue failed: {exc}")
        await message.channel.send(f"자동 읽기 중 오류가 났어: {exc}")


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
        queue_size = await enqueue_tts(ctx.guild, ctx.channel.id, clean_text, ctx.author.display_name)
    except Exception as exc:
        await ctx.reply(f"TTS 준비 중 오류가 났어: {exc}")
        return

    state = get_guild_state(ctx.guild.id)
    if state.current_item is None and queue_size == 1:
        await ctx.reply(f"바로 읽을게: {clean_text[:100]}")
    else:
        await ctx.reply(f"대기열에 추가했어. 현재 대기: {queue_size}개")


@bot.command(name="setreadchannel", aliases=["setup"])
@commands.has_permissions(manage_guild=True)
async def set_read_channel(ctx: commands.Context, channel: discord.TextChannel | None = None) -> None:
    if not ctx.guild:
        await ctx.reply("서버에서만 사용할 수 있어.")
        return

    target_channel = channel or ctx.channel
    config = get_guild_config(ctx.guild.id)
    config["read_channel_id"] = target_channel.id
    config["xsaid"] = False
    save_settings()
    await ctx.reply(f"이제 {target_channel.mention} 채널 메시지를 자동으로 읽을게. 닉네임 읽기는 기본으로 꺼둘게.")


@bot.command(name="clearreadchannel")
@commands.has_permissions(manage_guild=True)
async def clear_read_channel(ctx: commands.Context) -> None:
    if not ctx.guild:
        await ctx.reply("서버에서만 사용할 수 있어.")
        return

    config = get_guild_config(ctx.guild.id)
    config["read_channel_id"] = None
    save_settings()
    await ctx.reply("자동 읽기 채널 설정을 해제했어.")


@bot.command(name="readchannel")
async def read_channel_status(ctx: commands.Context) -> None:
    if not ctx.guild:
        await ctx.reply("서버에서만 사용할 수 있어.")
        return

    config = get_guild_config(ctx.guild.id)
    channel_id = config.get("read_channel_id")
    if not channel_id:
        await ctx.reply("자동 읽기 채널이 아직 설정되지 않았어.")
        return

    channel = ctx.guild.get_channel(channel_id)
    if not channel:
        await ctx.reply(f"저장된 채널 ID는 {channel_id}인데 지금 서버에서 찾지 못했어.")
        return

    await ctx.reply(f"현재 자동 읽기 채널은 {channel.mention} 이야.")


@bot.command(name="engines")
async def engines(ctx: commands.Context) -> None:
    lines = ["사용 가능한 TTS 엔진:"]
    for engine_key, info in SUPPORTED_ENGINES.items():
        lines.append(f"- {engine_key}: {info['label']}")
    await ctx.reply("\n".join(lines))


@bot.command(name="voices")
async def voices(ctx: commands.Context, engine: str | None = None) -> None:
    target_engine = engine or (get_guild_config(ctx.guild.id)["tts_engine"] if ctx.guild else DEFAULT_TTS_ENGINE)
    if target_engine not in SUPPORTED_ENGINES:
        await ctx.reply(f"지원하지 않는 엔진이야: {target_engine}")
        return

    lines = [f"{target_engine} 엔진에서 사용 가능한 보이스:"]
    for voice_id, provider_voice in SUPPORTED_ENGINES[target_engine]["voices"].items():
        lines.append(f"- {voice_id}: {provider_voice}")
    await ctx.reply("\n".join(lines[:25]))


@bot.command(name="setengine")
@commands.has_permissions(manage_guild=True)
async def set_engine(ctx: commands.Context, engine: str) -> None:
    if not ctx.guild:
        await ctx.reply("서버에서만 사용할 수 있어.")
        return

    engine = engine.strip().lower()
    if engine not in SUPPORTED_ENGINES:
        await ctx.reply(f"지원하지 않는 엔진이야. 가능한 값: {', '.join(SUPPORTED_ENGINES)}")
        return

    config = get_guild_config(ctx.guild.id)
    config["tts_engine"] = engine
    config["voice_id"] = next(iter(SUPPORTED_ENGINES[engine]["voices"]))
    save_settings()
    await ctx.reply(
        f"TTS 엔진을 {engine}로 바꿨어. 기본 보이스는 {describe_voice(config['tts_engine'], config['voice_id'])} 로 설정했어."
    )


@bot.command(name="setvoice")
@commands.has_permissions(manage_guild=True)
async def set_voice(ctx: commands.Context, voice_id: str) -> None:
    if not ctx.guild:
        await ctx.reply("서버에서만 사용할 수 있어.")
        return

    config = get_guild_config(ctx.guild.id)
    engine = config["tts_engine"]
    if voice_id not in SUPPORTED_ENGINES[engine]["voices"]:
        await ctx.reply("지원하지 않는 voice_id야. `!voices`로 확인해 줘.")
        return

    config["voice_id"] = voice_id
    save_settings()
    await ctx.reply(f"보이스를 {describe_voice(engine, voice_id)} 로 바꿨어.")


@bot.command(name="voice")
async def voice_status(ctx: commands.Context) -> None:
    if not ctx.guild:
        await ctx.reply("서버에서만 사용할 수 있어.")
        return

    config = get_guild_config(ctx.guild.id)
    await ctx.reply(
        f"현재 엔진: {config['tts_engine']}\n현재 기본 보이스: {describe_voice(config['tts_engine'], config['voice_id'])}"
    )


@bot.command(name="male")
@commands.has_permissions(manage_guild=True)
async def set_male_voice(ctx: commands.Context) -> None:
    if not ctx.guild:
        await ctx.reply("서버에서만 사용할 수 있어.")
        return

    config = get_guild_config(ctx.guild.id)
    config["voice_id"] = "ko_male_1"
    save_settings()
    await ctx.reply(f"남성 보이스로 바꿨어: {describe_voice(config['tts_engine'], config['voice_id'])}")


@bot.command(name="female")
@commands.has_permissions(manage_guild=True)
async def set_female_voice(ctx: commands.Context) -> None:
    if not ctx.guild:
        await ctx.reply("서버에서만 사용할 수 있어.")
        return

    config = get_guild_config(ctx.guild.id)
    config["voice_id"] = "ko_female_1"
    save_settings()
    await ctx.reply(f"여성 보이스로 바꿨어: {describe_voice(config['tts_engine'], config['voice_id'])}")


@bot.command(name="autojoin")
@commands.has_permissions(manage_guild=True)
async def autojoin(ctx: commands.Context, value: str | None = None) -> None:
    if not ctx.guild:
        await ctx.reply("서버에서만 사용할 수 있어.")
        return

    config = get_guild_config(ctx.guild.id)
    if value is None:
        await ctx.reply(f"autojoin 현재 상태: {'켜짐' if config.get('autojoin') else '꺼짐'}")
        return

    normalized = value.strip().lower()
    if normalized in {"on", "true", "1", "yes"}:
        config["autojoin"] = True
    elif normalized in {"off", "false", "0", "no"}:
        config["autojoin"] = False
    else:
        await ctx.reply("값은 on/off 중 하나로 넣어 줘.")
        return

    save_settings()
    await ctx.reply(f"autojoin을 {'켜짐' if config.get('autojoin') else '꺼짐'}으로 설정했어.")


@bot.command(name="xsaid")
@commands.has_permissions(manage_guild=True)
async def xsaid(ctx: commands.Context, value: str | None = None) -> None:
    if not ctx.guild:
        await ctx.reply("서버에서만 사용할 수 있어.")
        return

    config = get_guild_config(ctx.guild.id)
    if value is None:
        await ctx.reply(f"xsaid 현재 상태: {'켜짐' if config.get('xsaid', True) else '꺼짐'}")
        return

    normalized = value.strip().lower()
    if normalized in {"on", "true", "1", "yes"}:
        config["xsaid"] = True
    elif normalized in {"off", "false", "0", "no"}:
        config["xsaid"] = False
    else:
        await ctx.reply("값은 on/off 중 하나로 넣어 줘.")
        return

    save_settings()
    await ctx.reply(f"xsaid를 {'켜짐' if config.get('xsaid', True) else '꺼짐'}으로 설정했어.")


@bot.command(name="multilang")
@commands.has_permissions(manage_guild=True)
async def multilang(ctx: commands.Context, value: str | None = None) -> None:
    if not ctx.guild:
        await ctx.reply("서버에서만 사용할 수 있어.")
        return

    config = get_guild_config(ctx.guild.id)
    if value is None:
        await ctx.reply(f"multilang 현재 상태: {'켜짐' if config.get('multilang', True) else '꺼짐'}")
        return

    normalized = value.strip().lower()
    if normalized in {"on", "true", "1", "yes"}:
        config["multilang"] = True
    elif normalized in {"off", "false", "0", "no"}:
        config["multilang"] = False
    else:
        await ctx.reply("값은 on/off 중 하나로 넣어 줘.")
        return

    save_settings()
    await ctx.reply(f"한국어/영어 자동 읽기를 {'켜짐' if config.get('multilang', True) else '꺼짐'}으로 설정했어.")


@bot.command(name="settings")
async def settings(ctx: commands.Context) -> None:
    if not ctx.guild:
        await ctx.reply("서버에서만 사용할 수 있어.")
        return

    config = get_guild_config(ctx.guild.id)
    channel_id = config.get("read_channel_id")
    channel = ctx.guild.get_channel(channel_id) if channel_id else None
    channel_text = channel.mention if channel else "설정 안 됨"

    await ctx.reply(
        "현재 설정\n"
        f"- 자동 읽기 채널: {channel_text}\n"
        f"- 엔진: {config['tts_engine']}\n"
        f"- 기본 보이스: {describe_voice(config['tts_engine'], config['voice_id'])}\n"
        f"- 한국어 기본: {describe_voice(config['tts_engine'], SUPPORTED_ENGINES[config['tts_engine']]['language_defaults']['ko'])}\n"
        f"- 영어 기본: {describe_voice(config['tts_engine'], SUPPORTED_ENGINES[config['tts_engine']]['language_defaults']['en'])}\n"
        f"- autojoin: {'켜짐' if config.get('autojoin') else '꺼짐'}\n"
        f"- xsaid: {'켜짐' if config.get('xsaid', True) else '꺼짐'}\n"
        f"- multilang: {'켜짐' if config.get('multilang', True) else '꺼짐'}"
    )


@bot.command(name="sample")
async def sample(ctx: commands.Context, voice_id: str | None = None, *, text: str | None = None) -> None:
    if not ctx.guild:
        await ctx.reply("서버에서만 사용할 수 있어.")
        return

    config = get_guild_config(ctx.guild.id)
    target_voice = voice_id or choose_voice_id_for_text(config, text or "안녕하세요")
    sample_text = text or "안녕하세요. This is a Discord TTS bot sample."

    try:
        await ensure_voice_client(ctx)
        audio_path = await synthesize_tts(sanitize_text(sample_text), config["tts_engine"], target_voice)
    except Exception as exc:
        await ctx.reply(f"샘플 생성 중 오류가 났어: {exc}")
        return

    state = get_guild_state(ctx.guild.id)
    item = TTSItem(
        text=sample_text,
        author_name=ctx.author.display_name,
        text_channel_id=ctx.channel.id,
        file_path=audio_path,
    )
    await state.queue.put(item)
    ensure_worker(ctx.guild.id)
    await ctx.reply(f"샘플 보이스를 재생할게: {describe_voice(config['tts_engine'], target_voice)}")


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
        f"- {COMMAND_PREFIX}setreadchannel [#채널] / {COMMAND_PREFIX}setup [#채널]\n"
        f"- {COMMAND_PREFIX}clearreadchannel\n"
        f"- {COMMAND_PREFIX}readchannel\n"
        f"- {COMMAND_PREFIX}settings\n"
        f"- {COMMAND_PREFIX}xsaid <on|off>\n"
        f"- {COMMAND_PREFIX}multilang <on|off>\n"
        f"- {COMMAND_PREFIX}engines\n"
        f"- {COMMAND_PREFIX}voices [engine]\n"
        f"- {COMMAND_PREFIX}setengine <engine>\n"
        f"- {COMMAND_PREFIX}setvoice <voice_id>\n"
        f"- {COMMAND_PREFIX}male\n"
        f"- {COMMAND_PREFIX}female\n"
        f"- {COMMAND_PREFIX}voice\n"
        f"- {COMMAND_PREFIX}sample [voice_id] [문장]\n"
        f"- {COMMAND_PREFIX}skip\n"
        f"- {COMMAND_PREFIX}stop\n"
        f"- {COMMAND_PREFIX}queue"
    )


@set_read_channel.error
@clear_read_channel.error
@set_engine.error
@set_voice.error
@set_male_voice.error
@set_female_voice.error
@xsaid.error
@multilang.error
async def admin_command_error(ctx: commands.Context, error: Exception) -> None:
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply("이 명령어는 서버 관리 권한이 있어야 써.")
        return
    await ctx.reply(f"명령 처리 중 오류가 났어: {error}")


bot.run(DISCORD_TOKEN)
