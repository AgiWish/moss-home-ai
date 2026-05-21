from plugins_func.register import register_function, ToolType, ActionResponse, Action
from plugins_func.functions.hass_init import initialize_hass_handler
from config.logger import setup_logging
import asyncio
import os
import random
import re
import shutil
import threading
import time
import unicodedata
import requests
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler

TAG = __name__
logger = setup_logging()

MA_BASE_URL = "http://192.168.5.8:8096"
MA_USERNAME = "<MA_USERNAME>"
MA_PASSWORD = "<MA_PASSWORD>"

DEFAULT_MUSIC_PLAYER = "apfeb2842e85f8"
LEBO_AIRPLAY_PLAYER = "ap56d0040bdeb3"
TV_UNIVERSAL_PLAYER = "up7b227e0ddfbe2b27f5d07c22df10ea3a"
FALLBACK_MUSIC_PLAYER = "media_player.xiaomi_oh2p_1813_play_control"
TV_MIN_MUSIC_VOLUME = 55

MUSIC_RESOURCE_DIR = "/music_resource"
MUSIC_LIBRARY_CACHE_DIR = "/music_library/115缓存"
MUSIC_INDEX_FILE = "/opt/xiaozhi-esp32-server/data/music_resource_index.tsv"
MUSIC_SEARCH_SECONDS = 10
MUSIC_INDEX_BUILD_SECONDS = 90
MAX_CACHE_FILE_MB = 500
SYNC_CACHE_FILE_MB = 20
AUDIO_EXTENSIONS = {
    ".mp3",
    ".flac",
    ".m4a",
    ".aac",
    ".ogg",
    ".opus",
    ".wav",
    ".ape",
    ".dsf",
    ".dff",
}

PLAYER_ALIASES = {
    "media_player.dian_shi": DEFAULT_MUSIC_PLAYER,
    "media_player.dian_shi_2": DEFAULT_MUSIC_PLAYER,
    "media_player.ke_ting_dian_shi": DEFAULT_MUSIC_PLAYER,
    "media_player.apple_tv": DEFAULT_MUSIC_PLAYER,
    "media_player.ke_ting_apple_tv": DEFAULT_MUSIC_PLAYER,
    "media_player.le_bo_tou_ping_ke_ting_dian_shi": LEBO_AIRPLAY_PLAYER,
    "media_player.le_bo_tou_ping_ke_ting_dian_shi_2": LEBO_AIRPLAY_PLAYER,
    "up7b227e0ddfbe2b27f5d07c22df10ea3a": LEBO_AIRPLAY_PLAYER,
    "ap56d0040bdeb3": LEBO_AIRPLAY_PLAYER,
    "media_player.ke_ting_xiao_hei": "media_player.xiaomi_oh2p_1813_play_control",
    "media_player.shu_fang_xiao_lan": "media_player.xiaomi_oh2_74bc_play_control",
    "media_player.zhu_wo_xiao_huang": "media_player.xiaomi_oh2_bf09_play_control",
    "media_player.ci_wo_xiao_lu": "media_player.xiaomi_oh2_1e13_play_control",
}

PENDING_MUSIC = {}
PENDING_MUSIC_LOCK = threading.Lock()

hass_play_music_function_desc = {
    "type": "function",
    "function": {
        "name": "hass_play_music",
        "description": "用户想听音乐、有声书、播放、换一首、下一首、换个歌手时使用，在房间的媒体播放器里播放对应音频。如果本地音乐库没有，会从115音乐资源库搜索单曲并缓存到本地音乐库后再播放。",
        "parameters": {
            "type": "object",
            "properties": {
                "media_content_id": {
                    "type": "string",
                    "description": "可以是音乐或有声书的专辑名称、歌曲名、演唱者,如果未指定就填random",
                },
                "entity_id": {
                    "type": "string",
                    "description": "需要操作的播放器设备id，homeassistant里的entity_id。客厅/电视/Apple TV默认使用media_player.dian_shi_2；客厅小黑用media_player.xiaomi_oh2p_1813_play_control；书房小蓝用media_player.xiaomi_oh2_74bc_play_control；主卧小黄用media_player.xiaomi_oh2_bf09_play_control；次卧小绿用media_player.xiaomi_oh2_1e13_play_control",
                },
            },
            "required": ["media_content_id", "entity_id"],
        },
    },
}


@register_function(
    "hass_play_music", hass_play_music_function_desc, ToolType.SYSTEM_CTL
)
def hass_play_music(conn: "ConnectionHandler", entity_id="", media_content_id="random"):
    try:
        ha_response = handle_hass_play_music(conn, entity_id, media_content_id)
        return ActionResponse(
            action=Action.RESPONSE, result=ha_response, response=ha_response
        )
    except Exception as e:
        logger.bind(tag=TAG).error(f"处理音乐意图错误: {type(e).__name__}: {e}")
        return ActionResponse(Action.ERROR, "音乐服务暂时不可用", None)


def handle_hass_play_music(conn: "ConnectionHandler", entity_id, media_content_id):
    ha_config = initialize_hass_handler(conn)
    api_key = ha_config.get("api_key")
    base_url = ha_config.get("base_url")
    if not entity_id:
        entity_id = DEFAULT_MUSIC_PLAYER
    entity_id = PLAYER_ALIASES.get(entity_id.strip(), entity_id.strip())
    if not api_key or not base_url:
        return "音乐播放失败，Home Assistant 配置缺失"

    query = normalize_query(media_content_id)
    pending_query = get_pending_music_query(query)
    if pending_query:
        query = pending_query
    media_uri, display_name = find_music_in_ma(query)
    if not media_uri:
        cached = cache_music_from_resource(query, entity_id)
        if cached:
            if cached.get("pending"):
                return f"已找到{cached['display_name']}，文件较大，正在后台缓存，缓存好会自动播放"
            trigger_music_sync()
            media_uri, display_name = wait_find_cached_music(query, cached)
        if not media_uri:
            if cached:
                return f"已缓存{cached['display_name']}，音乐库正在扫描，稍后再试"
            return f"没有找到{media_content_id}，请先把歌曲加入音乐库"

    target_players = [entity_id]
    if entity_id == DEFAULT_MUSIC_PLAYER:
        target_players.append(LEBO_AIRPLAY_PLAYER)
        target_players.append(FALLBACK_MUSIC_PLAYER)
    last_error = ""
    if entity_id == DEFAULT_MUSIC_PLAYER:
        wake_tv_player(base_url, api_key)
    for player_id in target_players:
        if not is_player_available(base_url, api_key, player_id):
            last_error = f"{player_id} 当前不可用"
            logger.bind(tag=TAG).warning(f"跳过不可用播放器:{player_id}")
            continue
        prepare_player(base_url, api_key, player_id)
        ok, message = play_media_via_ma(player_id, media_uri, display_name)
        if ok:
            return message
        last_error = message
        logger.bind(tag=TAG).warning(f"播放器{player_id}播放失败，准备尝试下一个目标: {message}")
    return last_error


def is_player_available(base_url, api_key, entity_id):
    ma_player = get_ma_player(entity_id)
    if ma_player:
        if not ma_player.get("available"):
            return False
        return True
    try:
        response = requests.get(
            f"{base_url}/api/states/{entity_id}",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            timeout=5,
        )
        if response.status_code != 200:
            logger.bind(tag=TAG).warning(
                f"查询播放器状态失败:{entity_id}, status:{response.status_code}, body:{response.text[:200]}"
            )
            return True
        state = response.json().get("state")
        return state not in ("unavailable", "unknown")
    except Exception as e:
        logger.bind(tag=TAG).warning(f"查询播放器状态异常:{entity_id}, {type(e).__name__}: {e}")
        return True


def get_ma_player(player_id):
    try:
        for player in ma_api("players/all"):
            if player.get("player_id") == player_id:
                return player
    except Exception as e:
        logger.bind(tag=TAG).warning(f"查询MA播放器失败: {type(e).__name__}: {e}")
    return None


def play_media_via_ma(player_id, media_uri, display_name):
    try:
        ma_api(
            "player_queues/play_media",
            {
                "queue_id": player_id,
                "media": media_uri,
                "option": "replace",
            },
            timeout=20,
        )
        logger.bind(tag=TAG).info(
            f"播放音乐:{display_name}, player_id:{player_id}, media_uri:{media_uri}, command:player_queues/play_media"
        )
        return True, f"正在播放{display_name}"
    except Exception as e:
        logger.bind(tag=TAG).warning(
            f"Music Assistant播放失败:{player_id}, {type(e).__name__}: {e}"
        )
        return False, f"音乐播放失败，{player_id}不可用"


def normalize_query(media_content_id):
    query = (media_content_id or "random").strip()
    lower_query = query.lower().replace(" ", "")
    aliases = {
        "爱豆": "I Do",
        "爱do": "I Do",
        "ido": "I Do",
        "idou": "I Do",
        "爱周杰伦": "I Do",
        "播放": "random",
        "帮我播放": "random",
        "开始播放": "random",
        "放歌": "random",
        "播放音乐": "random",
        "听歌": "random",
        "没播放": "random",
        "没有播放": "random",
        "小智没有播放": "random",
        "这首歌": "random",
        "哎这首歌": "random",
    }
    if lower_query in aliases:
        return aliases[lower_query]
    return query


def get_pending_music_query(query):
    if normalize_text(query) not in ("random", "播放", "帮我播放", "开始播放", "这首歌", "没播放", "没有播放"):
        return None
    with PENDING_MUSIC_LOCK:
        pending = dict(PENDING_MUSIC)
    if not pending:
        return None
    if time.time() - pending.get("created_at", 0) > 600:
        clear_pending_music()
        return None
    return pending.get("query") or pending.get("display_name")


def set_pending_music(query, cached, player_id):
    with PENDING_MUSIC_LOCK:
        PENDING_MUSIC.clear()
        PENDING_MUSIC.update(
            {
                "query": query,
                "display_name": cached.get("display_name"),
                "player_id": player_id,
                "created_at": time.time(),
            }
        )


def clear_pending_music():
    with PENDING_MUSIC_LOCK:
        PENDING_MUSIC.clear()


def get_ma_token():
    response = requests.post(
        f"{MA_BASE_URL}/auth/login",
        json={"credentials": {"username": MA_USERNAME, "password": MA_PASSWORD}},
        timeout=5,
    )
    response.raise_for_status()
    return response.json()["token"]


def ma_api(command, args=None, timeout=8):
    token = get_ma_token()
    response = requests.post(
        f"{MA_BASE_URL}/api",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"command": command, "args": args or {}},
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()


def find_music_in_ma(query):
    if normalize_text(query) in ("random", "换一首", "下一首", "再换一首", "换个歌手", "换歌"):
        return find_random_music_in_ma()
    result = ma_api(
        "music/search",
        {
            "search_query": query,
            "limit": 5,
            "library_only": True,
        },
    )
    tracks = result.get("tracks") or []
    if not tracks:
        return None, None
    track = tracks[0]
    artist = ""
    artists = track.get("artists") or []
    if artists:
        artist = artists[0].get("name") or ""
    display_name = f"{artist} - {track.get('name')}" if artist else track.get("name")
    return track.get("uri"), display_name


def find_random_music_in_ma():
    try:
        tracks = ma_api("music/tracks/library_items", {"limit": 50}) or []
    except Exception as e:
        logger.bind(tag=TAG).warning(f"随机取音乐库失败: {type(e).__name__}: {e}")
        tracks = []
    tracks = [track for track in tracks if track.get("uri")]
    if not tracks:
        return find_music_in_ma("周杰伦")
    track = random.choice(tracks)
    artist = ""
    artists = track.get("artists") or []
    if artists:
        artist = artists[0].get("name") or ""
    display_name = f"{artist} - {track.get('name')}" if artist else track.get("name")
    return track.get("uri"), display_name


def trigger_music_sync():
    try:
        ma_api(
            "music/sync",
            {
                "media_types": ["track"],
                "providers": [
                    "filesystem_local--n7kvtqbh",
                    "opensubsonic--jZadZc9A",
                ],
            },
        )
    except Exception as e:
        logger.bind(tag=TAG).warning(f"触发音乐库同步失败: {type(e).__name__}: {e}")


def wait_find_cached_music(query, cached):
    searches = [query, cached.get("title"), cached.get("artist"), cached.get("display_name")]
    seen = set()
    for _ in range(4):
        for item in searches:
            if not item:
                continue
            key = normalize_text(item)
            if key in seen:
                continue
            seen.add(key)
            try:
                media_uri, display_name = find_music_in_ma(item)
                if media_uri:
                    return media_uri, display_name
            except Exception as e:
                logger.bind(tag=TAG).warning(f"缓存后搜索音乐库失败: {type(e).__name__}: {e}")
        time.sleep(2)
    return None, None


def cache_music_from_resource(query, player_id=None):
    match = search_music_resource(query)
    if not match:
        return None
    src_path = match["path"]
    try:
        size_mb = os.path.getsize(src_path) / 1024 / 1024
        if size_mb > MAX_CACHE_FILE_MB:
            logger.bind(tag=TAG).warning(f"跳过过大的音乐文件:{src_path}, size_mb:{size_mb:.1f}")
            return None
        os.makedirs(MUSIC_LIBRARY_CACHE_DIR, exist_ok=True)
        ext = os.path.splitext(src_path)[1]
        target_name = sanitize_filename(match["display_name"]) + ext.lower()
        dst_path = unique_target_path(os.path.join(MUSIC_LIBRARY_CACHE_DIR, target_name))
        cached = dict(match)
        cached["cached_path"] = dst_path
        if os.path.exists(dst_path):
            logger.bind(tag=TAG).info(f"音乐已在本地缓存:{dst_path}")
            return cached
        if is_cache_copying(dst_path):
            cached["pending"] = True
            logger.bind(tag=TAG).info(f"音乐正在后台缓存:{dst_path}")
            return cached
        if size_mb > SYNC_CACHE_FILE_MB:
            cached["pending"] = True
            set_pending_music(query, cached, player_id or DEFAULT_MUSIC_PLAYER)
            start_background_cache(src_path, dst_path, match["display_name"], player_id or DEFAULT_MUSIC_PLAYER, query, cached)
            return cached
        shutil.copy2(src_path, dst_path)
        logger.bind(tag=TAG).info(f"已从115资源库同步缓存音乐:{src_path} -> {dst_path}")
        return cached
    except Exception as e:
        logger.bind(tag=TAG).error(f"缓存115音乐失败:{type(e).__name__}: {e}, path:{src_path}")
        return None


def is_cache_copying(dst_path):
    marker_path = f"{dst_path}.copying"
    if not os.path.exists(marker_path):
        return False
    try:
        age_seconds = time.time() - os.path.getmtime(marker_path)
        if age_seconds < 1800:
            return True
        os.remove(marker_path)
        part_path = f"{dst_path}.part"
        if os.path.exists(part_path):
            os.remove(part_path)
        logger.bind(tag=TAG).warning(f"已清理过期音乐缓存任务:{dst_path}")
    except OSError:
        return True
    return False


def start_background_cache(src_path, dst_path, display_name, player_id, query, cached):
    def copy_worker():
        part_path = f"{dst_path}.part"
        marker_path = f"{dst_path}.copying"
        try:
            with open(marker_path, "w", encoding="utf-8") as marker:
                marker.write(src_path)
            shutil.copy2(src_path, part_path)
            os.replace(part_path, dst_path)
            logger.bind(tag=TAG).info(f"已从115资源库后台缓存音乐:{src_path} -> {dst_path}")
            trigger_music_sync()
            media_uri, found_display_name = wait_find_cached_music(query, cached)
            if media_uri:
                ok, message = play_media_via_ma(player_id, media_uri, found_display_name or display_name)
                if ok:
                    clear_pending_music()
                logger.bind(tag=TAG).info(f"后台缓存后自动播放结果:{message}")
            else:
                logger.bind(tag=TAG).warning(f"后台缓存完成但音乐库暂未找到:{display_name}")
        except Exception as e:
            logger.bind(tag=TAG).error(f"后台缓存音乐失败:{display_name}, {type(e).__name__}: {e}")
            try:
                if os.path.exists(part_path):
                    os.remove(part_path)
            except OSError:
                pass
        finally:
            try:
                if os.path.exists(marker_path):
                    os.remove(marker_path)
            except OSError:
                pass

    thread = threading.Thread(target=copy_worker, name="xiaozhi-music-cache", daemon=True)
    thread.start()
    logger.bind(tag=TAG).info(f"已启动后台音乐缓存:{display_name}, {src_path} -> {dst_path}")


def search_music_resource(query):
    if not os.path.isdir(MUSIC_RESOURCE_DIR):
        logger.bind(tag=TAG).warning(f"115音乐资源目录不可用:{MUSIC_RESOURCE_DIR}")
        return None
    query_key = normalize_text(query)
    if not query_key:
        return None
    indexed = load_music_index()
    if not indexed:
        indexed = build_music_index()
    best = search_music_index(query_key, indexed)
    if best:
        return best

    start = time.monotonic()
    best = None
    for root, dirs, files in os.walk(MUSIC_RESOURCE_DIR):
        if time.monotonic() - start > MUSIC_SEARCH_SECONDS:
            break
        dirs[:] = [item for item in dirs if not item.startswith(".") and item not in ("@eaDir", "#recycle")]
        for filename in files:
            if time.monotonic() - start > MUSIC_SEARCH_SECONDS:
                break
            ext = os.path.splitext(filename)[1].lower()
            if ext not in AUDIO_EXTENSIONS:
                continue
            path = os.path.join(root, filename)
            score = score_music_match(query_key, path, filename)
            if score <= 0:
                continue
            title, artist, display_name = parse_track_name(filename)
            candidate = {
                "path": path,
                "title": title,
                "artist": artist,
                "display_name": display_name,
                "score": score,
            }
            if not best or score > best["score"]:
                best = candidate
            if score >= 100:
                return candidate
    return best


def load_music_index():
    if not os.path.exists(MUSIC_INDEX_FILE):
        return []
    indexed = []
    try:
        with open(MUSIC_INDEX_FILE, "r", encoding="utf-8") as file:
            for line in file:
                parts = line.rstrip("\n").split("\t")
                if len(parts) < 5:
                    continue
                path, title, artist, display_name, key = parts[:5]
                indexed.append(
                    {
                        "path": path,
                        "title": title,
                        "artist": artist,
                        "display_name": display_name,
                        "key": key,
                    }
                )
        return indexed
    except Exception as e:
        logger.bind(tag=TAG).warning(f"读取音乐索引失败:{type(e).__name__}: {e}")
        return []


def build_music_index():
    indexed = []
    start = time.monotonic()
    try:
        os.makedirs(os.path.dirname(MUSIC_INDEX_FILE), exist_ok=True)
        tmp_file = f"{MUSIC_INDEX_FILE}.tmp"
        with open(tmp_file, "w", encoding="utf-8") as file:
            for root, dirs, files in os.walk(MUSIC_RESOURCE_DIR):
                if time.monotonic() - start > MUSIC_INDEX_BUILD_SECONDS:
                    break
                dirs[:] = [item for item in dirs if not item.startswith(".") and item not in ("@eaDir", "#recycle")]
                for filename in files:
                    ext = os.path.splitext(filename)[1].lower()
                    if ext not in AUDIO_EXTENSIONS:
                        continue
                    path = os.path.join(root, filename)
                    title, artist, display_name = parse_track_name(filename)
                    key = normalize_text(path)
                    file.write(f"{path}\t{title}\t{artist}\t{display_name}\t{key}\n")
                    indexed.append(
                        {
                            "path": path,
                            "title": title,
                            "artist": artist,
                            "display_name": display_name,
                            "key": key,
                        }
                    )
        os.replace(tmp_file, MUSIC_INDEX_FILE)
        logger.bind(tag=TAG).info(f"音乐资源索引已更新:{len(indexed)}首")
    except Exception as e:
        logger.bind(tag=TAG).warning(f"构建音乐索引失败:{type(e).__name__}: {e}")
    return indexed


def search_music_index(query_key, indexed):
    best = None
    for item in indexed:
        score = score_music_key(query_key, item.get("key") or "")
        if score <= 0:
            continue
        candidate = dict(item)
        candidate["score"] = score
        if not best or score > best["score"]:
            best = candidate
        if score >= 100:
            return candidate
    return best


def score_music_key(query_key, item_key):
    if query_key in item_key:
        return 100 + len(query_key)
    terms = [normalize_text(part) for part in re.split(r"[\s,，、]+", query_key) if normalize_text(part)]
    if terms and all(term in item_key for term in terms):
        return 60 + sum(len(term) for term in terms)
    chars = [char for char in query_key if "\u4e00" <= char <= "\u9fff"]
    if len(chars) >= 2:
        hit_count = sum(1 for char in chars if char in item_key)
        if hit_count / len(chars) >= 0.8:
            return 40 + hit_count
    return 0


def score_music_match(query_key, path, filename):
    filename_key = normalize_text(os.path.splitext(filename)[0])
    path_key = normalize_text(path)
    if query_key in filename_key:
        return 100 + len(query_key)
    if query_key in path_key:
        return 80 + len(query_key)
    terms = [normalize_text(part) for part in re.split(r"[\s,，、]+", query_key) if normalize_text(part)]
    if terms and all(term in path_key for term in terms):
        return 60 + sum(len(term) for term in terms)
    chars = [char for char in query_key if "\u4e00" <= char <= "\u9fff"]
    if len(chars) >= 2:
        hit_count = sum(1 for char in chars if char in filename_key)
        if hit_count / len(chars) >= 0.8:
            return 40 + hit_count
    return 0


def parse_track_name(filename):
    stem = os.path.splitext(filename)[0]
    stem = re.sub(r"^[\d\s._-]+", "", stem).strip()
    parts = re.split(r"\s*[-－—]\s*", stem, maxsplit=1)
    if len(parts) == 2:
        title = parts[0].strip()
        artist = parts[1].strip()
        display_name = f"{artist} - {title}" if artist else title
        return title, artist, display_name
    return stem, "", stem


def normalize_text(text):
    text = unicodedata.normalize("NFKC", str(text or "")).lower()
    return re.sub(r"[\s\W_]+", "", text, flags=re.UNICODE)


def sanitize_filename(text):
    text = re.sub(r"[\\/:*?\"<>|]+", "_", str(text or "").strip())
    return text[:120] or "unknown"


def unique_target_path(path):
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path)
    return f"{base}{ext}"


def prepare_player(base_url, api_key, entity_id):
    if entity_id in (DEFAULT_MUSIC_PLAYER, LEBO_AIRPLAY_PLAYER, TV_UNIVERSAL_PLAYER):
        wake_tv_player(base_url, api_key)
        ensure_tv_music_volume(entity_id)
    logger.bind(tag=TAG).info(f"播放前已检查播放器状态:{entity_id}")


def ensure_tv_music_volume(entity_id):
    player = get_ma_player(entity_id)
    if not player:
        return
    volume = player.get("volume_level")
    if volume is None:
        return
    try:
        volume = int(volume)
    except (TypeError, ValueError):
        return
    if volume >= TV_MIN_MUSIC_VOLUME:
        return
    try:
        ma_api(
            "players/cmd/volume_set",
            {"player_id": entity_id, "volume_level": TV_MIN_MUSIC_VOLUME},
            timeout=10,
        )
        logger.bind(tag=TAG).info(
            f"电视音乐音量过低，已从{volume}调整到{TV_MIN_MUSIC_VOLUME}:{entity_id}"
        )
    except Exception as e:
        logger.bind(tag=TAG).warning(f"调整电视音乐音量失败: {type(e).__name__}: {e}")


def unmute_player(entity_id):
    try:
        ma_api("players/cmd/volume_mute", {"player_id": entity_id, "muted": False})
    except Exception as e:
        logger.bind(tag=TAG).warning(f"取消静音失败: {type(e).__name__}: {e}")


def wake_tv_player(base_url, api_key):
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    wake_calls = [
        ("media_player/turn_on", {"entity_id": "media_player.dian_shi"}),
        ("button/press", {"entity_id": "button.xiaomi_oh2p_1813_tv_switchon"}),
    ]
    for service, payload in wake_calls:
        try:
            response = requests.post(
                f"{base_url}/api/services/{service}",
                headers=headers,
                json=payload,
                timeout=5,
            )
            if response.status_code not in (200, 201):
                logger.bind(tag=TAG).warning(
                    f"唤醒电视失败:{service}, status:{response.status_code}, body:{response.text[:200]}"
                )
        except Exception as e:
            logger.bind(tag=TAG).warning(f"唤醒电视异常:{service}, {type(e).__name__}: {e}")
