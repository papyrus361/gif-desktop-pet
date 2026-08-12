import json
import os
import sys


class ConfigManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        if getattr(sys, "frozen", False):
            self.config_dir = os.path.join(
                os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "DesktopPet"
            )
        else:
            self.config_dir = os.path.dirname(os.path.abspath(__file__))
        os.makedirs(self.config_dir, exist_ok=True)
        self.config_path = os.path.join(self.config_dir, "config.json")
        self.defaults = {
            "x": None,
            "y": None,
            "scale": 1.0,
            "currentGif": "",
            "gifFolder": "",
            "alwaysTop": True,
            "autoStart": False,
            "clickThrough": False,
            "alarmEnabled": True,
            "soundEnabled": True,
            "autoSwitch": False,
            "randomSwitch": False,
            "autoSwitchInterval": 30,
            "defaultScale": 100,
            "defaultVolume": 70,
            "alarms": [
                {"time": "08:00", "label": "起床"},
                {"time": "12:00", "label": "午饭"},
                {"time": "18:00", "label": "下班"},
                {"time": "22:30", "label": "睡觉"},
            ],
        }
        self.data = dict(self.defaults)
        self.load()

    def load(self):
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    for k, v in self.defaults.items():
                        self.data[k] = loaded.get(k, v)
        except Exception:
            self.data = dict(self.defaults)

    def save(self):
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value

    def get_alarms(self):
        alarms = self.data.get("alarms", [])
        for alarm in alarms:
            alarm.setdefault("enabled", True)
        return alarms

    def set_alarms(self, alarms):
        self.data["alarms"] = alarms
