#!/usr/bin/env python3
"""
ORSAY TV Voice Assistant System
Extensible voice command processing with plugin architecture.
Supports: Vosk (offline), command routing, event triggering, plugin system.
"""

import os
import sys
import json
import threading
import queue
import time
from pathlib import Path
from typing import Dict, List, Callable, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import importlib.util


# ============================================
# CONFIGURATION
# ============================================
BASE_DIR = Path(__file__).parent.parent
PLUGINS_DIR = BASE_DIR / "voice_plugins"
CONFIG_DIR = BASE_DIR / "firmware" / "etc"
LOGS_DIR = BASE_DIR / "firmware" / "var" / "logs"


# ============================================
# VOICE COMMAND DATA STRUCTURES
# ============================================
@dataclass
class VoiceCommand:
    """Represents a recognized voice command"""
    text: str
    confidence: float
    timestamp: datetime
    language: str = "ru"
    platform: str = "unknown"


@dataclass
class CommandIntent:
    """Represents parsed intent from voice command"""
    plugin: str
    action: str
    params: Dict[str, Any]
    confidence: float


class VoiceLogger:
    """Logging system for voice assistant"""
    
    def __init__(self):
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        self.log_file = LOGS_DIR / f"voice_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)
        
        try:
            with open(self.log_file, "a") as f:
                f.write(log_entry + "\n")
        except:
            pass
    
    def info(self, msg: str):
        self.log(msg, "INFO")
    
    def success(self, msg: str):
        self.log(msg, "SUCCESS")
    
    def error(self, msg: str):
        self.log(msg, "ERROR")
    
    def debug(self, msg: str):
        self.log(msg, "DEBUG")


logger = VoiceLogger()


# ============================================
# VOICE COMMAND RECOGNIZER
# ============================================
class VoiceRecognizer:
    """
    Offline speech recognition using Vosk.
    Falls back to manual command injection if unavailable.
    """
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self.recognizer = None
        self.is_listening = False
        self._init_vosk()
    
    def _init_vosk(self):
        """Initialize Vosk speech recognition"""
        try:
            import vosk
            import sounddevice as sd
            
            if self.model_path and os.path.exists(self.model_path):
                self.model = vosk.Model(self.model_path)
                self.recognizer = vosk.KaldiRecognizer(self.model, 16000)
                logger.success("[Vosk] Speech recognition initialized")
                return True
            else:
                logger.info("[Vosk] Model not found, using fallback mode")
                return False
        
        except ImportError:
            logger.info("[Vosk] Not installed. Install: pip install vosk sounddevice")
            return False
        except Exception as e:
            logger.error(f"[Vosk] Initialization failed: {e}")
            return False
    
    def start_listening(self, callback: Callable[[VoiceCommand], None]):
        """Start listening for voice input"""
        if not self.recognizer:
            logger.warning("Vosk not available, using manual command mode")
            return False
        
        logger.info("Starting voice listening...")
        self.is_listening = True
        
        try:
            import sounddevice as sd
            
            def audio_callback(indata, frames, time_info, status):
                if status:
                    logger.debug(f"Audio status: {status}")
                
                if self.recognizer.AcceptWaveform(bytes(indata)):
                    result_json = self.recognizer.Result()
                    result = json.loads(result_json)
                    
                    if "result" in result and result["result"]:
                        text = " ".join([item.get("conf", "") for item in result["result"]])
                        if text.strip():
                            command = VoiceCommand(
                                text=text.strip(),
                                confidence=0.9,
                                timestamp=datetime.now(),
                                language="ru"
                            )
                            callback(command)
            
            with sd.RawInputStream(
                samplerate=16000,
                blocksize=4000,
                channels=1,
                dtype="int16",
                callback=audio_callback
            ):
                logger.success("Microphone stream active")
                while self.is_listening:
                    time.sleep(0.1)
        
        except Exception as e:
            logger.error(f"Listening error: {e}")
            return False
        
        return True
    
    def stop_listening(self):
        """Stop listening for voice"""
        self.is_listening = False
        logger.info("Stopped listening")
    
    def inject_command(self, text: str) -> VoiceCommand:
        """Manually inject a command (for testing/fallback)"""
        return VoiceCommand(
            text=text,
            confidence=1.0,
            timestamp=datetime.now(),
            language="ru"
        )


# ============================================
# PLUGIN SYSTEM
# ============================================
class VoicePlugin:
    """Base class for voice assistant plugins"""
    
    # Plugin metadata
    name: str = "Unknown Plugin"
    version: str = "0.0.1"
    description: str = "No description"
    author: str = "Unknown"
    
    # Supported intents: {"action": "keywords"}
    intents: Dict[str, List[str]] = {}
    
    def __init__(self, event_bus=None):
        self.event_bus = event_bus
        self.enabled = True
        logger.info(f"Plugin loaded: {self.name} v{self.version}")
    
    def can_handle(self, command: VoiceCommand) -> bool:
        """Check if plugin can handle this command"""
        raise NotImplementedError
    
    def parse_intent(self, command: VoiceCommand) -> Optional[CommandIntent]:
        """Parse voice command into intent"""
        raise NotImplementedError
    
    def handle(self, intent: CommandIntent) -> bool:
        """Execute the command intent"""
        raise NotImplementedError
    
    def emit_event(self, event_name: str, data: Any = None):
        """Emit event to event bus"""
        if self.event_bus:
            self.event_bus.emit(f"{self.name}:{event_name}", data)


class PluginLoader:
    """Load and manage voice assistant plugins"""
    
    def __init__(self, plugins_dir: Path = PLUGINS_DIR):
        self.plugins_dir = plugins_dir
        self.plugins: Dict[str, VoicePlugin] = {}
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
    
    def load_plugin(self, plugin_path: Path, event_bus=None) -> Optional[VoicePlugin]:
        """Load a single plugin from Python file"""
        try:
            if not plugin_path.exists():
                logger.error(f"Plugin not found: {plugin_path}")
                return None
            
            # Import module dynamically
            spec = importlib.util.spec_from_file_location(
                plugin_path.stem,
                plugin_path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find plugin class
            plugin_class = None
            for item_name in dir(module):
                item = getattr(module, item_name)
                if (isinstance(item, type) and 
                    issubclass(item, VoicePlugin) and 
                    item is not VoicePlugin):
                    plugin_class = item
                    break
            
            if not plugin_class:
                logger.error(f"No VoicePlugin class found in {plugin_path}")
                return None
            
            # Instantiate and register
            plugin = plugin_class(event_bus=event_bus)
            self.plugins[plugin.name] = plugin
            logger.success(f"✓ Loaded plugin: {plugin.name}")
            return plugin
        
        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_path}: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None
    
    def load_all_plugins(self, event_bus=None) -> int:
        """Load all plugins from plugins directory"""
        logger.info(f"=== Loading Voice Plugins from {self.plugins_dir} ===")
        
        count = 0
        for plugin_file in self.plugins_dir.glob("*.py"):
            if plugin_file.name.startswith("_"):
                continue
            
            if self.load_plugin(plugin_file, event_bus):
                count += 1
        
        logger.success(f"Loaded {count} plugins")
        return count
    
    def list_plugins(self) -> List[str]:
        """List loaded plugin names"""
        return list(self.plugins.keys())
    
    def get_plugin(self, name: str) -> Optional[VoicePlugin]:
        """Get plugin by name"""
        return self.plugins.get(name)
    
    def disable_plugin(self, name: str) -> bool:
        """Disable a plugin"""
        if name in self.plugins:
            self.plugins[name].enabled = False
            logger.info(f"Disabled plugin: {name}")
            return True
        return False
    
    def enable_plugin(self, name: str) -> bool:
        """Enable a plugin"""
        if name in self.plugins:
            self.plugins[name].enabled = True
            logger.info(f"Enabled plugin: {name}")
            return True
        return False


# ============================================
# COMMAND MATCHER & INTENT PARSER
# ============================================
class CommandMatcher:
    """Match voice commands to plugin intents"""
    
    def __init__(self, plugins: Dict[str, VoicePlugin]):
        self.plugins = plugins
    
    def normalize_text(self, text: str) -> str:
        """Normalize command text"""
        return text.lower().strip()
    
    def match(self, command: VoiceCommand) -> Optional[Tuple[VoicePlugin, CommandIntent]]:
        """
        Match command to a plugin and parse intent.
        Returns (plugin, intent) or None if no match.
        """
        normalized = self.normalize_text(command.text)
        
        # Try each plugin
        for plugin in self.plugins.values():
            if not plugin.enabled:
                continue
            
            if plugin.can_handle(command):
                intent = plugin.parse_intent(command)
                if intent:
                    logger.info(f"Matched to plugin: {plugin.name}, action: {intent.action}")
                    return (plugin, intent)
        
        logger.warning(f"No plugin matched command: {command.text}")
        return None


# ============================================
# VOICE ASSISTANT ENGINE
# ============================================
class VoiceAssistant:
    """
    Main voice assistant engine with plugin system.
    Manages recognition, intent matching, and command execution.
    """
    
    def __init__(self, event_bus=None, vosk_model_path: Optional[str] = None):
        self.event_bus = event_bus
        self.recognizer = VoiceRecognizer(vosk_model_path)
        self.plugin_loader = PluginLoader()
        self.plugins: Dict[str, VoicePlugin] = {}
        self.matcher = None
        
        self.is_running = False
        self.command_queue: queue.Queue = queue.Queue()
        self.command_thread: Optional[threading.Thread] = None
        
        logger.info("=== Voice Assistant Initialized ===")
    
    def load_plugins(self) -> int:
        """Load all voice assistant plugins"""
        count = self.plugin_loader.load_all_plugins(self.event_bus)
        self.plugins = self.plugin_loader.plugins
        self.matcher = CommandMatcher(self.plugins)
        return count
    
    def register_plugin(self, plugin: VoicePlugin):
        """Register a plugin programmatically"""
        plugin.event_bus = self.event_bus
        self.plugins[plugin.name] = plugin
        self.matcher = CommandMatcher(self.plugins)
        logger.success(f"Registered plugin: {plugin.name}")
    
    def start(self):
        """Start the voice assistant"""
        logger.info("Starting voice assistant...")
        
        if not self.plugins:
            logger.warning("No plugins loaded!")
        
        self.is_running = True
        
        # Start command processing thread
        self.command_thread = threading.Thread(
            target=self._process_commands,
            daemon=True
        )
        self.command_thread.start()
        
        # Start voice listening (blocking in separate thread)
        listen_thread = threading.Thread(
            target=self._listen_voice,
            daemon=True
        )
        listen_thread.start()
        
        logger.success("Voice assistant started")
    
    def stop(self):
        """Stop the voice assistant"""
        logger.info("Stopping voice assistant...")
        self.is_running = False
        self.recognizer.stop_listening()
    
    def _listen_voice(self):
        """Listen for voice input (runs in thread)"""
        self.recognizer.start_listening(self._on_command_recognized)
    
    def _on_command_recognized(self, command: VoiceCommand):
        """Callback when voice command is recognized"""
        logger.info(f"Command recognized: '{command.text}' (conf: {command.confidence})")
        self.command_queue.put(command)
    
    def _process_commands(self):
        """Process commands from queue (runs in thread)"""
        while self.is_running:
            try:
                # Wait for command with timeout
                command = self.command_queue.get(timeout=1.0)
                
                # Match to plugin
                result = self.matcher.match(command)
                
                if result:
                    plugin, intent = result
                    self._execute_command(plugin, intent)
                else:
                    self._emit_no_match_event(command)
            
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Command processing error: {e}")
    
    def _execute_command(self, plugin: VoicePlugin, intent: CommandIntent):
        """Execute a command intent via plugin"""
        try:
            logger.info(f"Executing: {plugin.name}::{intent.action}")
            success = plugin.handle(intent)
            
            if success:
                logger.success(f"✓ Command executed: {intent.action}")
                self._emit_command_success_event(plugin, intent)
            else:
                logger.warning(f"✗ Command failed: {intent.action}")
                self._emit_command_failed_event(plugin, intent)
        
        except Exception as e:
            logger.error(f"Execution error: {e}")
            self._emit_command_error_event(plugin, intent, e)
    
    def _emit_no_match_event(self, command: VoiceCommand):
        """Emit event when no plugin matches"""
        if self.event_bus:
            self.event_bus.emit("voice_no_match", {"command": command.text})
    
    def _emit_command_success_event(self, plugin: VoicePlugin, intent: CommandIntent):
        """Emit event on successful command"""
        if self.event_bus:
            self.event_bus.emit("voice_command_success", {
                "plugin": plugin.name,
                "action": intent.action,
                "params": intent.params
            })
    
    def _emit_command_failed_event(self, plugin: VoicePlugin, intent: CommandIntent):
        """Emit event on failed command"""
        if self.event_bus:
            self.event_bus.emit("voice_command_failed", {
                "plugin": plugin.name,
                "action": intent.action
            })
    
    def _emit_command_error_event(self, plugin: VoicePlugin, intent: CommandIntent, error: Exception):
        """Emit event on command error"""
        if self.event_bus:
            self.event_bus.emit("voice_command_error", {
                "plugin": plugin.name,
                "action": intent.action,
                "error": str(error)
            })
    
    def inject_command(self, text: str):
        """Manually inject a voice command (for testing)"""
        command = self.recognizer.inject_command(text)
        self._on_command_recognized(command)
    
    def get_loaded_plugins(self) -> List[Dict[str, str]]:
        """Get information about loaded plugins"""
        plugins_info = []
        for name, plugin in self.plugins.items():
            plugins_info.append({
                "name": plugin.name,
                "version": plugin.version,
                "description": plugin.description,
                "author": plugin.author,
                "enabled": plugin.enabled
            })
        return plugins_info


# ============================================
# BUILT-IN EXAMPLE PLUGINS
# ============================================

class HelloPlugin(VoicePlugin):
    """Example: Simple hello world plugin"""
    
    name = "Hello"
    version = "1.0.0"
    description = "Simple greeting responses"
    author = "ARTE33345555"
    
    intents = {
        "greet": ["привет", "hello", "привет tv", "привет система"],
        "who_are_you": ["кто ты", "что ты", "представься"],
    }
    
    def can_handle(self, command: VoiceCommand) -> bool:
        text = command.text.lower()
        for keywords in self.intents.values():
            if any(kw in text for kw in keywords):
                return True
        return False
    
    def parse_intent(self, command: VoiceCommand) -> Optional[CommandIntent]:
        text = command.text.lower()
        
        if any(kw in text for kw in self.intents["greet"]):
            return CommandIntent("Hello", "greet", {}, 0.95)
        elif any(kw in text for kw in self.intents["who_are_you"]):
            return CommandIntent("Hello", "who_are_you", {}, 0.95)
        
        return None
    
    def handle(self, intent: CommandIntent) -> bool:
        if intent.action == "greet":
            print("🤖 [Assistant] Привет! Я голосовой ассистент ORSAY TV")
            self.emit_event("greeting_response")
            return True
        elif intent.action == "who_are_you":
            print("🤖 [Assistant] Я ORSAY TV Voice Assistant - ваш персональный помощник")
            self.emit_event("identity_response")
            return True
        return False


class IPTVPlugin(VoicePlugin):
    """Example: IPTV control plugin"""
    
    name = "IPTV"
    version = "1.0.0"
    description = "Control IPTV playback via voice"
    author = "ARTE33345555"
    
    intents = {
        "play": ["включи канал", "запусти iptv", "канал"],
        "pause": ["пауза", "остановить", "стоп"],
        "next": ["следующий канал", "далее", "next"],
        "prev": ["предыдущий канал", "назад", "back"],
    }
    
    def can_handle(self, command: VoiceCommand) -> bool:
        text = command.text.lower()
        for keywords in self.intents.values():
            if any(kw in text for kw in keywords):
                return True
        return False
    
    def parse_intent(self, command: VoiceCommand) -> Optional[CommandIntent]:
        text = command.text.lower()
        
        if any(kw in text for kw in self.intents["play"]):
            return CommandIntent("IPTV", "play", {}, 0.9)
        elif any(kw in text for kw in self.intents["pause"]):
            return CommandIntent("IPTV", "pause", {}, 0.9)
        elif any(kw in text for kw in self.intents["next"]):
            return CommandIntent("IPTV", "next_channel", {}, 0.9)
        elif any(kw in text for kw in self.intents["prev"]):
            return CommandIntent("IPTV", "prev_channel", {}, 0.9)
        
        return None
    
    def handle(self, intent: CommandIntent) -> bool:
        if intent.action == "play":
            print("📺 [IPTV] Запускаю потоковое телевидение...")
            self.emit_event("iptv_started")
            return True
        elif intent.action == "pause":
            print("📺 [IPTV] Пауза")
            self.emit_event("iptv_paused")
            return True
        elif intent.action == "next_channel":
            print("📺 [IPTV] Следующий канал")
            self.emit_event("channel_changed", {"direction": "next"})
            return True
        elif intent.action == "prev_channel":
            print("📺 [IPTV] Предыдущий канал")
            self.emit_event("channel_changed", {"direction": "prev"})
            return True
        return False


class IoTPlugin(VoicePlugin):
    """Example: IoT device control plugin"""
    
    name = "IoT"
    version = "1.0.0"
    description = "Control IoT devices via voice"
    author = "ARTE33345555"
    
    intents = {
        "lights_on": ["включи свет", "свет включить", "освещение"],
        "lights_off": ["выключи свет", "свет выключить", "темно"],
        "set_color": ["цвет", "красный", "зеленый", "синий"],
        "temperature": ["температура", "термостат", "тепло", "холодно"],
    }
    
    def can_handle(self, command: VoiceCommand) -> bool:
        text = command.text.lower()
        for keywords in self.intents.values():
            if any(kw in text for kw in keywords):
                return True
        return False
    
    def parse_intent(self, command: VoiceCommand) -> Optional[CommandIntent]:
        text = command.text.lower()
        
        if any(kw in text for kw in self.intents["lights_on"]):
            return CommandIntent("IoT", "lights_on", {"room": "living_room"}, 0.9)
        elif any(kw in text for kw in self.intents["lights_off"]):
            return CommandIntent("IoT", "lights_off", {"room": "living_room"}, 0.9)
        elif any(kw in text for kw in self.intents["set_color"]):
            color = self._extract_color(text)
            return CommandIntent("IoT", "set_color", {"color": color}, 0.85)
        elif any(kw in text for kw in self.intents["temperature"]):
            return CommandIntent("IoT", "adjust_temperature", {"room": "living_room"}, 0.8)
        
        return None
    
    def _extract_color(self, text: str) -> str:
        """Extract color from text"""
        colors = {"красный": "red", "зеленый": "green", "синий": "blue"}
        for word, color in colors.items():
            if word in text:
                return color
        return "white"
    
    def handle(self, intent: CommandIntent) -> bool:
        if intent.action == "lights_on":
            print(f"💡 [IoT] Включаю свет в комнате: {intent.params.get('room')}")
            self.emit_event("lights_on", intent.params)
            return True
        elif intent.action == "lights_off":
            print(f"💡 [IoT] Выключаю свет в комнате: {intent.params.get('room')}")
            self.emit_event("lights_off", intent.params)
            return True
        elif intent.action == "set_color":
            color = intent.params.get('color', 'white')
            print(f"🌈 [IoT] Устанавливаю цвет: {color}")
            self.emit_event("color_changed", {"color": color})
            return True
        elif intent.action == "adjust_temperature":
            print(f"🌡 [IoT] Регулирую температуру в комнате: {intent.params.get('room')}")
            self.emit_event("temperature_adjusted", intent.params)
            return True
        return False


# ============================================
# INTEGRATION WITH MAIN SYSTEM
# ============================================
class HomeRadioAssistantV2:
    """
    Updated Home Radio Assistant with plugin-based voice system.
    Integrates with main ORSAY TV kernel.
    """
    
    def __init__(self, event_bus=None):
        self.event_bus = event_bus
        self.voice_assistant = VoiceAssistant(event_bus)
    
    def initialize(self):
        """Initialize the assistant"""
        logger.info("Initializing Home Radio Assistant V2...")
        
        # Load all voice plugins
        plugin_count = self.voice_assistant.load_plugins()
        logger.success(f"Voice Assistant ready with {plugin_count} plugins")
        
        # Emit initialization event
        if self.event_bus:
            self.event_bus.emit("voice_assistant_ready", {
                "plugins": self.voice_assistant.get_loaded_plugins()
            })
    
    def start(self):
        """Start voice listening"""
        self.voice_assistant.start()
    
    def stop(self):
        """Stop voice assistant"""
        self.voice_assistant.stop()
    
    def inject_test_command(self, text: str):
        """Inject test voice command"""
        logger.info(f"Injecting test command: {text}")
        self.voice_assistant.inject_command(text)
    
    def list_plugins(self) -> List[Dict]:
        """List available plugins"""
        return self.voice_assistant.get_loaded_plugins()


# ============================================
# DEMONSTRATION
# ============================================
def demo():
    """Demo of voice assistant with plugins"""
    
    print("\n" + "="*60)
    print("ORSAY TV Voice Assistant - Plugin System Demo")
    print("="*60 + "\n")
    
    # Create a simple event bus
    class SimpleEventBus:
        def __init__(self):
            self.listeners = {}
        
        def on(self, event, callback):
            self.listeners.setdefault(event, []).append(callback)
        
        def emit(self, event, data=None):
            for cb in self.listeners.get(event, []):
                cb(data)
    
    event_bus = SimpleEventBus()
    
    # Initialize assistant
    assistant = HomeRadioAssistantV2(event_bus)
    assistant.initialize()
    
    # Start voice assistant
    print("\n[*] Voice Assistant is running (in test mode)")
    print("[*] Available commands:")
    print("    - 'привет' / 'hello'")
    print("    - 'включи канал' / 'play iptv'")
    print("    - 'включи свет' / 'turn on lights'")
    print("    - 'выключи свет' / 'turn off lights'")
    print("\n[*] Type commands or 'quit' to exit:\n")
    
    # Listen for input and inject as voice commands
    try:
        while True:
            user_input = input(">>> ").strip()
            
            if user_input.lower() == "quit":
                break
            elif user_input.lower() == "plugins":
                plugins = assistant.list_plugins()
                for p in plugins:
                    status = "✓" if p["enabled"] else "✗"
                    print(f"  {status} {p['name']} (v{p['version']}) - {p['description']}")
            elif user_input:
                assistant.inject_test_command(user_input)
                time.sleep(0.5)  # Let it process
    
    except KeyboardInterrupt:
        print("\nShutting down...")
    
    assistant.stop()
    print("Voice Assistant stopped")


if __name__ == "__main__":
    demo()
