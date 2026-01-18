from services.cast_to_screen import CastToScreen
from services.skip_reclam import SkipReclam
from services.music_playback import MusicPlayback
from services.link_wireless import LinkWireless
from apps.hello_tv import HelloTV
from apps.olistore import Olistore

def main():
    print("Orsay Core starting...")
    CastToScreen().init()
    SkipReclam().init()
    MusicPlayback().init()
    LinkWireless().init()

    HelloTV().launch()
    Olistore().launch()

    while True:
        CastToScreen().loop()
        SkipReclam().loop()
        MusicPlayback().loop()
        LinkWireless().loop()
        HelloTV().loop()
        Olistore().loop()

if __name__ == "__main__":
    main()
