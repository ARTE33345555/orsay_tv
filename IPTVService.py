# =========================
# IPTV Service (daemon)
# =========================
class IPTVService(Service):
    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.running = False
        self.channels = []
        self.current = None

    def init(self):
        print("[Service] IPTVService started")
        self.running = True

    def load_playlist(self, url):
        print(f"[IPTV] Loading playlist: {url}")
        # Пока заглушка
        self.channels = [
            {"name": "Channel 1", "url": "http://stream1"},
            {"name": "Channel 2", "url": "http://stream2"}
        ]
        self.event_bus.emit("iptv_playlist_loaded", self.channels)

    def play(self, index):
        if index < len(self.channels):
            self.current = self.channels[index]
            print(f"[IPTV] Playing {self.current['name']}")
            self.event_bus.emit("iptv_play", self.current)

    def loop(self):
        if self.running:
            pass  # здесь потом будет буферизация/декодирование
