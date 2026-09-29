#!/usr/bin/env python3
"""
ORSAY Time Capsule - UI Application
Terminal/D-Pad based interface for recording management.
"""

import json
from typing import Optional, List
from time_capsule.core import (
    TimeCapsuleSystem, RecordingSource, Recording, StorageDevice
)


class CapsuleUI:
    """Terminal-based UI for Time Capsule"""
    
    def __init__(self, capsule_system: TimeCapsuleSystem):
        self.capsule = capsule_system
        self.current_menu = "main"
        self.selected_index = 0
    
    def show_main_menu(self):
        """Display main menu"""
        menu_items = [
            ("Record", "start_recording"),
            ("Stop Recording", "stop_recording"),
            ("Recordings", "list_recordings"),
            ("Scheduled", "scheduled_recordings"),
            ("Storage", "storage_info"),
            ("Sources", "sources_info"),
            ("Settings", "settings"),
        ]
        
        self._display_menu(
            title="TIME CAPSULE",
            items=menu_items,
            selected=self.selected_index
        )
    
    def show_recording_sources(self):
        """Show available recording sources"""
        status = self.capsule.get_system_status()
        sources = status["available_sources"]
        
        print("\n" + "="*50)
        print("AVAILABLE SOURCES")
        print("="*50 + "\n")
        
        for i, source in enumerate(sources):
            marker = "●" if i == self.selected_index else " "
            print(f"  {marker} {source.upper()}")
        
        for source in ["tv", "usb", "hdmi", "network"]:
            if source not in sources:
                print(f"  ○ {source.upper()} (Not available on this TV)")
        
        print("\n" + "="*50)
        self.current_menu = "sources"
    
    def show_storage_info(self):
        """Show storage information"""
        devices = self.capsule.storage_manager.get_devices()
        
        print("\n" + "="*50)
        print("STORAGE DEVICES")
        print("="*50 + "\n")
        
        for i, device in enumerate(devices):
            marker = "→" if i == self.selected_index else " "
            free_gb = device.free_size / (1024**3)
            usage = device.usage_percent
            
            print(f"{marker} {device.device_id.upper()}")
            print(f"  Type: {device.device_type}")
            print(f"  Free: {free_gb:.1f} GB")
            print(f"  Usage: {usage:.1f}%")
            print(f"  Status: {device.status}")
            print()
        
        print("="*50)
        self.current_menu = "storage"
    
    def show_recordings_list(self):
        """Show list of recordings"""
        recordings = self.capsule.library.list_recordings()
        
        print("\n" + "="*50)
        print("TIME CAPSULE RECORDINGS")
        print("="*50 + "\n")
        
        if not recordings:
            print("  No recordings found\n")
        else:
            current_date = None
            
            for i, rec in enumerate(recordings):
                # Show date separator
                rec_date = rec.started.split("T")[0]
                if rec_date != current_date:
                    print(f"\n{rec_date}\n")
                    current_date = rec_date
                
                marker = "▶" if i == self.selected_index else " "
                start_time = rec.started.split("T")[1][:5]
                duration_str = self._format_duration(rec.duration)
                
                print(f"{marker} {start_time}  {rec.source.upper()}")
                print(f"   {rec.title}")
                print(f"   {duration_str}  ({rec.filesize / (1024**2):.1f} MB)")
                print()
        
        print("="*50)
        self.current_menu = "recordings"
    
    def show_scheduled_recordings(self):
        """Show scheduled recordings"""
        scheduled = self.capsule.scheduler.list_scheduled()
        
        print("\n" + "="*50)
        print("SCHEDULED RECORDINGS")
        print("="*50 + "\n")
        
        if not scheduled:
            print("  No scheduled recordings\n")
        else:
            for i, sched in enumerate(scheduled):
                marker = "□" if i == self.selected_index else " "
                status = "✓" if sched.enabled else "✗"
                
                print(f"{marker} {status} {sched.title}")
                print(f"   {sched.date} {sched.start_time}-{sched.end_time}")
                print(f"   Source: {sched.source} | Storage: {sched.storage}")
                print()
        
        print("="*50)
        self.current_menu = "scheduled"
    
    def show_recording_control(self):
        """Show active recording control"""
        status = self.capsule.recording_engine.get_current_recording_status()
        
        if not status:
            print("\nNo recording in progress\n")
            return
        
        print("\n" + "="*50)
        print("RECORDING IN PROGRESS")
        print("="*50 + "\n")
        
        print(f"Title: {status['title']}")
        print(f"Source: {status['source'].upper()}")
        print(f"Duration: {self._format_duration(status['duration'])}")
        print(f"Storage: {status['storage']}")
        print(f"Filesize: {status['filesize'] / (1024**2):.1f} MB")
        
        print("\n" + "="*50)
        print("[■ STOP]  [⏸ PAUSE]")
        print("="*50)
    
    def _display_menu(self, title: str, items: List[tuple], selected: int):
        """Display a menu"""
        print("\n" + "="*50)
        print(title)
        print("="*50 + "\n")
        
        for i, (label, action) in enumerate(items):
            marker = "→" if i == selected else " "
            print(f"{marker} [ {label} ]")
        
        print("\n" + "="*50)
        print("[↑/↓ Navigate] [Enter Select] [Back] [Exit]")
        print("="*50)
    
    def _format_duration(self, seconds: int) -> str:
        """Format duration as HH:MM:SS"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
    
    def handle_input(self, key: str) -> Optional[str]:
        """Handle user input (D-pad emulation)"""
        if key == "up":
            self.selected_index = max(0, self.selected_index - 1)
        elif key == "down":
            self.selected_index += 1
        elif key == "enter":
            return "select"
        elif key == "back":
            self.current_menu = "main"
            self.selected_index = 0
        elif key == "exit":
            return "exit"
        
        return None


def demo_ui():
    """Demo the UI"""
    from time_capsule.core import TimeCapsuleSystem
    
    print("\nInitializing Time Capsule UI...\n")
    
    capsule = TimeCapsuleSystem()
    ui = CapsuleUI(capsule)
    
    # Show main menu
    ui.show_main_menu()
    
    # Simulate D-pad navigation
    print("\n[UI Demo - Simulating D-pad navigation]\n")
    
    commands = ["down", "down", "enter"]
    for cmd in commands:
        print(f"\n>>> {cmd}")
        ui.handle_input(cmd)
        
        if ui.current_menu == "main":
            ui.show_main_menu()
        elif ui.current_menu == "recordings":
            ui.show_recordings_list()


if __name__ == "__main__":
    demo_ui()
