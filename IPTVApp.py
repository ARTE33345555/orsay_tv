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

    def resume(self):
        print("[App] IPTV resume")

    def pause(self):
        print("[App] IPTV pause")

    def loop(self):
        pass
