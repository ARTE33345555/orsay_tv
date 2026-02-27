import time

# =========================
# EventBus (webOS style)
# =========================
class EventBus:
    def __init__(self):
        self.listeners = {}

    def on(self, event, callback):
        self.listeners.setdefault(event, []).append(callback)

    def emit(self, event, data=None):
        for cb in self.listeners.get(event, []):
            cb(data)


# =========================
# Base classes
# =========================
class Service:
    def init(self): pass
    def loop(self): pass
    def shutdown(self): pass


class App:
    def launch(self): pass
    def loop(self): pass
    def pause(self): pass
    def resume(self): pass


# =========================
# ServiceManager (Tizen)
# =========================
class ServiceManager:
    def __init__(self):
        self.services = []

    def register(self, service):
        self.services.append(service)

    def init_all(self):
        for s in self.services:
            s.init()

    def loop_all(self):
        for s in self.services:
            s.loop()


# =========================
# AppManager (webOS cards)
# =========================
class AppManager:
    def __init__(self):
        self.stack = []

    def open(self, app):
        if self.stack:
            self.stack[-1].pause()
        self.stack.append(app)
        app.launch()
        app.resume()

    def close(self):
        if self.stack:
            self.stack.pop()
        if self.stack:
            self.stack[-1].resume()

    def loop(self):
        if self.stack:
            self.stack[-1].loop()


# =========================
# Existing Services
# =========================
class CastToScreen(Service):
    def init(self):
        print("[Service] CastToScreen started")

    def loop(self):
        pass


# =========================
# IPTV Service
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
        # Заглушка плейлиста
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
            pass  # здесь можно добавить буферизацию/декодирование


# =========================
# Existing Apps
# =========================
class HelloTV(App):
    def launch(self):
        print("[App] HelloTV launch")

    def resume(self):
        print("[App] HelloTV resume")

    def pause(self):
        print("[App] HelloTV pause")

    def loop(self):
        pass


class Olistore(App):
    def launch(self):
        print("[App] Olistore launch")

    def resume(self):
        print("[App] Olistore resume")

    def pause(self):
        print("[App] Olistore pause")

    def loop(self):
        pass


# =========================
# IPTV App (card)
# =========================
class IPTVApp(App):
    def __init__(self, event_bus, iptv_service):
        self.event_bus = event_bus
        self.service = iptv_service

    def launch(self):
        print("[App] IPTV launch")
        self.service.load_playlist("community_default.m3u")
        # Автозапуск первого канала
        self.service.play(0)

    def resume(self):
        print("[App] IPTV resume")

    def pause(self):
        print("[App] IPTV pause")

    def loop(self):
        pass


# =========================
# MAIN KERNEL LOOP
# =========================
def main():
    print("Orsay MIX Core starting...")

    event_bus = EventBus()
    services = ServiceManager()
    apps = AppManager()

    # === Register Services ===
    cast_service = CastToScreen()
    iptv_service = IPTVService(event_bus)

    services.register(cast_service)
    services.register(iptv_service)

    services.init_all()

    # === Launch Apps ===
    hello_app = HelloTV()
    store_app = Olistore()
    iptv_app = IPTVApp(event_bus, iptv_service)

    apps.open(hello_app)
    apps.open(store_app)
    apps.open(iptv_app)

    # === Kernel Loop ===
    while True:
        services.loop_all()
        apps.loop()
        time.sleep(0.016)  # ~60 FPS


if __name__ == "__main__":
    main()
