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
# Services (daemons)
# =========================
class CastToScreen(Service):
    def init(self):
        print("[Service] CastToScreen started")

    def loop(self):
        pass


class SkipReclam(Service):
    def init(self):
        print("[Service] SkipReclam started")

    def loop(self):
        pass


class MusicPlayback(Service):
    def init(self):
        print("[Service] MusicPlayback started")

    def loop(self):
        pass


class LinkWireless(Service):
    def init(self):
        print("[Service] LinkWireless started")

    def loop(self):
        pass


# =========================
# Apps (cards)
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
# MAIN KERNEL LOOP
# =========================
def main():
    print("Orsay MIX Core starting...")

    event_bus = EventBus()

    services = ServiceManager()
    apps = AppManager()

    # Register services (Tizen-style)
    services.register(CastToScreen())
    services.register(SkipReclam())
    services.register(MusicPlayback())
    services.register(LinkWireless())

    services.init_all()

    # Launch apps (webOS-style cards)
    apps.open(HelloTV())
    apps.open(Olistore())

    # Kernel loop
    while True:
        services.loop_all()
        apps.loop()
        time.sleep(0.016)  # ~60 FPS


if __name__ == "__main__":
    main()

