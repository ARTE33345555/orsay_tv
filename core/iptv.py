from iptv_engine import IPTVEngine
from privilege import get_setting

iptv = IPTVEngine()

def apply_settings():
    if get_setting("iptv_enabled") == "true":
        iptv.start()

    playlist = get_setting("iptv_playlist")
    if playlist:
        iptv.load_m3u(playlist)
