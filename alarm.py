import os
import threading
from datetime import datetime

from PySide6.QtCore import QObject, Signal, QTimer

from config import ConfigManager
from logger import Logger
from utils import resource_path


def _play_wav_async(path, loop=True):
    def _play():
        try:
            import winsound
            flags = winsound.SND_FILENAME | winsound.SND_ASYNC
            if loop:
                flags |= winsound.SND_LOOP
            winsound.PlaySound(path, flags)
        except Exception:
            pass

    threading.Thread(target=_play, daemon=True).start()


def _stop_wav():
    try:
        import winsound
        winsound.PlaySound(None, winsound.SND_PURGE)
    except Exception:
        pass


class AlarmManager(QObject):
    alarm_triggered = Signal(str)
    alarm_dismissed = Signal()
    alarm_phase_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = ConfigManager()
        self.logger = Logger()
        self.alarms = []
        self.active = False
        self.current_label = ""
        self.sound_path = resource_path("assets/alarm.wav")

        self.check_timer = QTimer(self)
        self.check_timer.setInterval(1000)
        self.check_timer.timeout.connect(self._check_alarms)
        self._triggered_times = set()

    def _check_alarms(self):
        if not self.config.get("alarmEnabled", True):
            return
        if self.active:
            return

        now = datetime.now()
        current_time = now.strftime("%H:%M")
        current_minute_key = now.strftime("%Y-%m-%d %H:%M")

        if current_minute_key in self._triggered_times:
            return

        if len(self._triggered_times) > 100:
            self._triggered_times.clear()

        for alarm in self.alarms:
            if not alarm.get("enabled", True):
                continue
            if alarm["time"] == current_time:
                self._triggered_times.add(current_minute_key)
                self._trigger(alarm["label"])
                return

    def _trigger(self, label):
        self.active = True
        self.current_label = label
        self.logger.info(f"闹钟触发: {label}")
        self.alarm_triggered.emit(label)

    def dismiss(self):
        self.active = False
        self.stop_sound()
        self.current_label = ""
        self.alarm_dismissed.emit()

    def load_alarms(self):
        self.alarms = self.config.get_alarms()

    def save_alarms(self, alarms):
        self.alarms = alarms
        self.config.set_alarms(alarms)
        self.config.save()

    def get_alarms(self):
        return list(self.alarms)

    def start(self):
        self.load_alarms()
        self.check_timer.start()

    def stop(self):
        self.check_timer.stop()
        if self.active:
            self.dismiss()

    def play_sound(self):
        if not self.config.get("soundEnabled", True):
            return
        if os.path.exists(self.sound_path):
            _play_wav_async(self.sound_path, loop=True)

    def stop_sound(self):
        _stop_wav()
