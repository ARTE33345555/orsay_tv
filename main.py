import time
import sys

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
# Base Interfaces
# =========================
class Service:
    def init(self): pass
    def loop(self): pass
    def shutdown(self): pass


class App:
    def __init__(self, name="App"):
        self.name = name

    def launch(self): print(f"[{self.name}] Launching...")
    def loop(self): pass
    def pause(self): print(f"[{self.name}] Paused (Background overlay/listening)")
    def resume(self): print(f"[{self.name}] Resumed (Foreground)")


# =========================
# System Installer & Recovery
# =========================
class SystemInstaller:
    def __init__(self):
        self.components = [
            ("Creating compressed system backup (Lossless)", "backup"),
            ("Updating Root CA Certificates (https / YouTube fix)", "ca-certificates"),
            ("Updating Linux Kernel & Base System", "linux"),
            ("Updating WebKit Engine", "webkit"),
            ("Installing Python 3 Environment", "python3"),
            ("Installing WebRTC Components", "webrtc"),
            ("Configuring WoL & WoWLAN Services", "wol_wowl"),
            ("Deploying Wireless Hub (DLNA + Wi-Fi Direct + Samba)", "network_hub"),
            ("Deploying Miracast / AirPlay / Chromecast Stack", "cast_stack"),
            ("Launching Privet TV & Olli Store Environment", "privet_olli")
        ]

    def run_installation(self):
        print("===================================================")
        print("         ORSAY MIX CUSTOM FIRMWARE INSTALLER       ")
        print("===================================================")
        print()

        total = len(self.components)
        for idx, (label, name) in enumerate(self.components, 1):
            print(f"[{idx}/{total}] {label}...", end="", flush=True)
            time.sleep(0.1)

            success = True 
            if success:
                print(" [OK]")
            else:
                print(" [FAILED]")
                self.rollback()
                return False

        print()
        print("---------------------------------------------------")
        print("Installation finished successfully!")
        print("Rebooting system in 10 minutes (or starting Core now)...")
        print("---------------------------------------------------")
        print()
        return True

    def rollback(self):
        print("\n[CRITICAL ERROR] Installation aborted!")
        print("[RECOVERY] Restoring previous firmware from Lossless backup...")
        time.sleep(0.3)
        print("[RECOVERY] Rollback complete. Rebooting into stable system...")


# =========================
# System Managers
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


class AppManager:
    def __init__(self):
        self.stack = []
        self.registry = {}

    def register_app(self, key, app_instance):
        self.registry[key] = app_instance

    def open(self, app_or_key):
        app = self.registry.get(app_or_key, app_or_key) if isinstance(app_or_key, str) else app_or_key
        
        if self.stack and self.stack[-1] == app:
            return

        if self.stack:
            self.stack[-1].pause()
            
        self.stack.append(app)
        app.launch()
        app.resume()

    def close(self):
        if self.stack:
            closing_app = self.stack.pop()
            closing_app.pause()
        if self.stack:
            self.stack[-1].resume()

    def loop(self):
        if self.stack:
            self.stack[-1].loop()


# =========================
# System Services
# =========================
class CastToScreen(Service):
    def init(self):
        print("[Service] CastToScreen (DLNA + Wi-Fi Direct) started")


class SambaShareService(Service):
    def __init__(self, event_bus):
        self.event_bus = event_bus

    def init(self):
        print("[Service] Samba Client/Server active (Shares & Cross-TV Network)")


class PrivetTVAssistant(Service):
    def __init__(self, event_bus):
        self.event_bus = event_bus

    def init(self):
        print("[Service] Privet TV Voice Assistant (LLM + Home Assistant) active")

    def listen_command(self, command_text):
        print(f"\n[Privet TV] Voice Input: '{command_text}'")
        if "telegram" in command_text.lower():
            self.event_bus.emit("voice_open_app", "TelegramTV")
        elif "iptv" in command_text.lower():
            self.event_bus.emit("voice_open_app", "IPTV")


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
        print(f"[IPTV Service] Loading playlist from: {url}")
        self.channels = [
            {"name": "Channel 1", "url": "http://stream1"},
            {"name": "Channel 2", "url": "http://stream2"}
        ]
        self.event_bus.emit("iptv_playlist_loaded", self.channels)

    def play(self, index):
        if index < len(self.channels):
            self.current = self.channels[index]
            print(f"[IPTV Service] Playing {self.current['name']}")
            self.event_bus.emit("iptv_play", self.current)


# =========================
# Applications
# =========================
class HelloTV(App):
    def __init__(self):
        super().__init__("HelloTV")


class Olistore(App):
    def __init__(self):
        super().__init__("Olli Store")


class IPTVApp(App):
    def __init__(self, event_bus, iptv_service):
        super().__init__("IPTV")
        self.event_bus = event_bus
        self.service = iptv_service

    def launch(self):
        super().launch()
        self.service.load_playlist("community_default.m3u")
        self.service.play(0)


class TelegramTVApp(App):
    def __init__(self, event_bus):
        super().__init__("Telegram TV")
        self.event_bus = event_bus

    def launch(self):
        super().launch()
        print("[Telegram TV] Launching (TDLib + OpenCV/libcamera)")
        self.event_bus.emit("telegram_ready", True)

    def incoming_call(self, caller_name):
        print(f"[Telegram TV] Overlay Push Notification: Incoming Call from {caller_name}")


# =========================
# MAIN ENTRY POINT
# =========================
def main():
    installer = SystemInstaller()
    if not installer.run_installation():
        sys.exit(1)

    print("Orsay MIX Core starting...")

    event_bus = EventBus()
    services = ServiceManager()
    apps = AppManager()

    # === Register Services ===
    cast_service = CastToScreen()
    samba_service = SambaShareService(event_bus)
    assistant_service = PrivetTVAssistant(event_bus)
    iptv_service = IPTVService(event_bus)

    services.register(cast_service)
    services.register(samba_service)
    services.register(assistant_service)
    services.register(iptv_service)

    services.init_all()

    # === Instantiate and Register Apps ===
    hello_app = HelloTV()
    store_app = Olistore()
    iptv_app = IPTVApp(event_bus, iptv_service)
    telegram_app = TelegramTVApp(event_bus)

    apps.register_app("HelloTV", hello_app)
    apps.register_app("OlliStore", store_app)
    apps.register_app("IPTV", iptv_app)
    apps.register_app("TelegramTV", telegram_app)

    # === Event Listeners ===
    def handle_voice_app_launch(app_name):
        print(f"[Kernel] Voice Command Triggered App Launch: {app_name}")
        apps.open(app_name)

    event_bus.on("voice_open_app", handle_voice_app_launch)

    # === Launch Sequence & Simulation ===
    print("\n--- Card Stack Initialization ---")
    apps.open(hello_app)
    apps.open(store_app)
    apps.open(iptv_app)
    apps.open(telegram_app)

    # Simulate voice action & push notification
    assistant_service.listen_command("Privet TV, открой Telegram")
    telegram_app.incoming_call("Artem")

    # === Kernel Loop (60 FPS) ===
    print("\n--- Core Kernel Active ---")
    tick = 0
    try:
        while tick < 3:
            services.loop_all()
            apps.loop()
            time.sleep(0.016)
            tick += 1
        print("\nOrsay MIX Core is up and running.")
    except KeyboardInterrupt:
        print("Shutdown requested.")

if __name__ == "__main__":
    main()
