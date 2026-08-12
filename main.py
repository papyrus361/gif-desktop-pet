import sys
import os

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication

from config import ConfigManager
from logger import Logger
from gif_manager import GifManager
from pet_window import PetWindow
from animation import AnimationManager
from alarm import AlarmManager
from tray import TrayManager
from settings import SettingsDialog
from bubble import FloatingBall, TimerFloatingBall, StopwatchFloatingBall, AlarmBanner
from clock import ClockDialog


class DesktopPetApp:
    def __init__(self):
        self.logger = Logger()
        self.config = ConfigManager()
        self.logger.info("程序启动")

        self.app = QApplication(sys.argv)
        self.app.setApplicationName("DesktopPet")
        self.app.setQuitOnLastWindowClosed(False)
        self.app._pet_app = self

        self.gif_manager = GifManager(self.config.get("gifFolder", "") or None)
        saved_gif = self.config.get("currentGif", "")
        if saved_gif:
            self.gif_manager.switch_to_name(saved_gif)
        if self.gif_manager.get_count() == 0:
            self.logger.warning("未找到GIF文件")

        self.pet_window = PetWindow(self.gif_manager)
        self.pet_windows = [self.pet_window]

        self.anim = AnimationManager()
        self.alarm = AlarmManager()
        self.tray = TrayManager(self.gif_manager)
        self.floating_ball = FloatingBall()
        self.timer_ball = TimerFloatingBall()
        self.stopwatch_ball = StopwatchFloatingBall()
        self.alarm_ball_visible = False
        self.alarm_banner = AlarmBanner()
        self.auto_switch_timer = QTimer(self.app)
        self.auto_switch_timer.timeout.connect(self._auto_switch_gif)

        self._setup_alarm()
        self._setup_tray()
        self._setup_gif_signals()
        self._setup_pet_window_signals(self.pet_window)
        self._restore_config_state()
        self._start_countdown()
        self._update_auto_switch()

        if self.config.get("alarmEnabled", True):
            self.alarm.start()

    def _start_countdown(self):
        alarms = self.alarm.get_alarms()
        self.floating_ball.set_alarms(alarms)
        if self.alarm_ball_visible:
            self.floating_ball.start_countdown()
        else:
            self.floating_ball.stop_countdown()

    def _setup_alarm(self):
        self.alarm.alarm_triggered.connect(self._on_alarm_trigger)
        self.alarm.alarm_dismissed.connect(self._on_alarm_dismiss)
        self.floating_ball.dismiss_requested.connect(self.dismiss_alarm)
        self.floating_ball.add_alarm_requested.connect(self.show_add_alarm_dialog)
        self.floating_ball.manage_alarm_requested.connect(self.show_alarm_dialog)
        self.floating_ball.close_requested.connect(self._hide_alarm_ball)

    def _on_alarm_trigger(self, label):
        self.floating_ball.show_alarm_mode()
        self.alarm_banner.show_alarm(label)
        self.alarm.play_sound()
        self.anim.scale_to(self.pet_window, 4.0, 500)
        QTimer.singleShot(600, lambda: self.anim.shake(self.pet_window, 8000, 25))
        self.tray.show_message("闹钟提醒", f"{label} 时间到了！")

    def _on_alarm_dismiss(self):
        self.anim.stop_shake(self.pet_window)
        saved_scale = self.config.get("scale", 1.0)
        self.pet_window.set_pet_scale(saved_scale)
        self.alarm_banner.hide_banner()
        self.alarm.stop_sound()
        self._start_countdown()

    def _show_alarm_ball(self):
        self.alarm_ball_visible = True
        self._start_countdown()

    def _hide_alarm_ball(self):
        self.alarm_ball_visible = False
        self.floating_ball.stop_countdown()

    def dismiss_alarm(self):
        self.alarm.dismiss()

    def _setup_tray(self):
        self.tray.show_requested.connect(self._show_pet)
        self.tray.hide_requested.connect(self._hide_pet)
        self.tray.switch_gif_requested.connect(self._switch_gif)
        self.tray.alarm_requested.connect(self.show_alarm_dialog)
        self.tray.settings_requested.connect(self.show_settings_dialog)
        self.tray.gif_folder_requested.connect(self.choose_gif_folder)
        self.tray.default_gif_folder_requested.connect(self.use_default_gif_folder)
        self.tray.quit_requested.connect(self._quit)

    def _show_pet(self):
        for pet_window in self.pet_windows:
            pet_window.show()
        self.tray.set_visible(True)

    def _hide_pet(self):
        for pet_window in self.pet_windows:
            pet_window.hide()
        self.tray.set_visible(False)

    def _switch_gif(self, index):
        self.gif_manager.switch_to(index)

    def _setup_gif_signals(self):
        self.gif_manager.gif_changed.connect(self._on_gif_changed)

    def _on_gif_changed(self, path, index):
        self.pet_window.switch_gif(path)
        self.config.set("currentGif", self.gif_manager.get_current_name())

    def _setup_pet_window_signals(self, pet_window):
        pet_window.alarm_dialog_requested.connect(self.show_alarm_dialog)
        pet_window.add_alarm_requested.connect(self.show_add_alarm_dialog)
        pet_window.alarm_toggled.connect(self._on_alarm_toggled)
        pet_window.clock_requested.connect(self.show_clock_dialog)
        pet_window.settings_dialog_requested.connect(self.show_settings_dialog)
        pet_window.clone_requested.connect(self.clone_pet)
        pet_window.close_requested.connect(self.close_pet)
        pet_window.gif_folder_requested.connect(self._on_pet_gif_folder)
        pet_window.default_gif_folder_requested.connect(self._on_pet_default_folder)

    def choose_gif_folder(self):
        self._on_pet_gif_folder(self.pet_window)

    def use_default_gif_folder(self):
        self._on_pet_default_folder(self.pet_window)

    def _on_pet_gif_folder(self, pet_window):
        from PySide6.QtWidgets import QFileDialog, QMessageBox

        start_dir = pet_window.gif_manager.gif_dir
        folder = QFileDialog.getExistingDirectory(pet_window, "选择 GIF 文件夹", start_dir)
        if not folder:
            return
        if not self._set_gif_folder_for_pet(pet_window, folder):
            QMessageBox.warning(pet_window, "未找到 GIF", "所选文件夹中没有 GIF 文件。")

    def _on_pet_default_folder(self, pet_window):
        self._set_gif_folder_for_pet(pet_window, None)

    def _set_gif_folder_for_pet(self, pet_window, folder):
        candidate = GifManager(folder)
        if candidate.get_count() == 0:
            return False

        pet_window.gif_manager.set_gif_dir(folder)
        pet_window.gif_manager.switch_to(0)

        if pet_window is self.pet_window:
            self.config.set("gifFolder", "" if self.gif_manager.is_default_dir() else self.gif_manager.gif_dir)
            self.config.set("currentGif", self.gif_manager.get_current_name())
            self.config.save()
        return True

    def close_pet(self, pet_window):
        if pet_window not in self.pet_windows:
            return
        self.pet_windows.remove(pet_window)
        pet_window.hide()
        if pet_window is not self.pet_window:
            pet_window.deleteLater()
        if not self.pet_windows:
            self._quit()

    def clone_pet(self, source):
        clone_manager = GifManager(source.gif_manager.gif_dir)
        clone_manager.switch_to_name(source.gif_manager.get_current_name())
        clone = PetWindow(clone_manager)
        clone_manager.gif_changed.connect(clone.switch_gif)
        clone.set_pet_scale(source.pet_scale)
        clone.move(source.x() + 32, source.y() + 32)
        self.pet_windows.append(clone)
        self._setup_pet_window_signals(clone)
        clone.show()

    def _on_alarm_toggled(self, index, enabled):
        if self.config.get("alarmEnabled", True):
            self.alarm.start()
        self._start_countdown()

    def _restore_config_state(self):
        self.pet_window.set_always_top(self.config.get("alwaysTop", True))

    def show_clock_dialog(self):
        dialog = ClockDialog(self.pet_window)
        dialog.alarm_changed.connect(self._on_alarm_changed)
        dialog.alarm_ball_requested.connect(self._show_alarm_ball)
        dialog.timer_ball_requested.connect(self.timer_ball.start)
        dialog.stopwatch_ball_requested.connect(self.stopwatch_ball.start)
        dialog.exec()

    def _on_alarm_changed(self):
        if self.config.get("alarmEnabled", True):
            self.alarm.start()
        self._start_countdown()

    def show_settings_dialog(self):
        dialog = SettingsDialog(self.pet_window)
        dialog.settings_changed.connect(self._on_settings_changed)
        dialog.exec()

    def show_alarm_dialog(self):
        from PySide6.QtWidgets import (
            QDialog, QVBoxLayout, QListWidget, QPushButton,
            QHBoxLayout, QTimeEdit, QLineEdit, QDialogButtonBox,
            QTabWidget, QWidget, QFormLayout, QSpinBox, QLabel
        )

        dialog = QDialog(self.pet_window)
        dialog.setWindowTitle("闹钟管理")
        dialog.setFixedSize(350, 400)
        dialog.setWindowFlags(
            dialog.windowFlags() | Qt.WindowType.WindowStaysOnTopHint
        )
        layout = QVBoxLayout(dialog)

        list_widget = QListWidget()
        for a in self.alarm.get_alarms():
            list_widget.addItem(f"{a['time']}  {a['label']}")
        layout.addWidget(list_widget)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("添加")
        remove_btn = QPushButton("删除")
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(remove_btn)
        layout.addLayout(btn_layout)

        close_layout = QHBoxLayout()
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.accept)
        close_layout.addStretch()
        close_layout.addWidget(close_btn)
        layout.addLayout(close_layout)

        def _add_alarm():
            add_dialog = QDialog(dialog)
            add_dialog.setWindowTitle("添加闹钟")
            add_dialog.setFixedSize(320, 200)
            add_dialog.setWindowFlags(
                add_dialog.windowFlags() | Qt.WindowType.WindowStaysOnTopHint
            )
            add_layout = QVBoxLayout(add_dialog)

            tabs = QTabWidget()
            tab_specific = QWidget()
            specific_layout = QFormLayout(tab_specific)
            time_edit = QTimeEdit()
            time_edit.setDisplayFormat("HH:mm")
            label_edit_s = QLineEdit()
            specific_layout.addRow("时间:", time_edit)
            specific_layout.addRow("标签:", label_edit_s)
            tabs.addTab(tab_specific, "指定时间")

            tab_timer = QWidget()
            timer_layout = QFormLayout(tab_timer)
            hours_spin = QSpinBox()
            hours_spin.setRange(0, 23)
            hours_spin.setSuffix(" 小时")
            minutes_spin = QSpinBox()
            minutes_spin.setRange(1, 59)
            minutes_spin.setSuffix(" 分钟")
            minutes_spin.setValue(30)
            label_edit_t = QLineEdit()
            timer_layout.addRow("小时:", hours_spin)
            timer_layout.addRow("分钟:", minutes_spin)
            timer_layout.addRow("标签:", label_edit_t)
            tabs.addTab(tab_timer, "倒计时")

            add_layout.addWidget(tabs)
            btn_box = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
            )
            add_layout.addWidget(btn_box)

            btn_box.accepted.connect(add_dialog.accept)
            btn_box.rejected.connect(add_dialog.reject)

            if add_dialog.exec() == QDialog.DialogCode.Accepted:
                from datetime import datetime, timedelta
                alarms = self.alarm.get_alarms()
                if tabs.currentIndex() == 0:
                    time_str = time_edit.time().toString("HH:mm")
                    label = label_edit_s.text().strip() or "闹钟"
                else:
                    delta = timedelta(hours=hours_spin.value(), minutes=minutes_spin.value())
                    future = datetime.now() + delta
                    time_str = future.strftime("%H:%M")
                    label = label_edit_t.text().strip() or "闹钟"
                alarms.append({"time": time_str, "label": label})
                alarms.sort(key=lambda a: a["time"])
                self.alarm.save_alarms(alarms)
                list_widget.addItem(f"{time_str}  {label}")
                list_widget.sortItems()
                self._start_countdown()

        add_btn.clicked.connect(_add_alarm)

        def _remove_alarm():
            row = list_widget.currentRow()
            if row < 0:
                return
            alarms = self.alarm.get_alarms()
            if 0 <= row < len(alarms):
                alarms.pop(row)
                self.alarm.save_alarms(alarms)
                list_widget.takeItem(row)
                self._start_countdown()

        remove_btn.clicked.connect(_remove_alarm)

        dialog.exec()

    def show_add_alarm_dialog(self):
        from PySide6.QtWidgets import (
            QDialog, QVBoxLayout, QTimeEdit, QLineEdit,
            QDialogButtonBox, QFormLayout
        )

        dialog = QDialog(self.pet_window)
        dialog.setWindowTitle("添加闹钟")
        dialog.setFixedSize(320, 180)
        dialog.setWindowFlags(
            dialog.windowFlags() | Qt.WindowType.WindowStaysOnTopHint
        )
        layout = QVBoxLayout(dialog)

        form = QFormLayout()
        time_edit = QTimeEdit()
        time_edit.setDisplayFormat("HH:mm")
        label_edit = QLineEdit()
        form.addRow("时间:", time_edit)
        form.addRow("标签:", label_edit)
        layout.addLayout(form)

        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)
        layout.addWidget(btn_box)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            time_str = time_edit.time().toString("HH:mm")
            label = label_edit.text().strip() or "闹钟"
            alarms = self.alarm.get_alarms()
            alarms.append({"time": time_str, "label": label, "enabled": True})
            alarms.sort(key=lambda a: a["time"])
            self.alarm.save_alarms(alarms)
            self._start_countdown()

    def _on_settings_changed(self, settings):
        self.pet_window.set_always_top(settings["alwaysTop"])

        if settings["autoStart"]:
            self._enable_auto_start()
        else:
            self._disable_auto_start()

        if settings["alarmEnabled"]:
            self.alarm.start()
            self._start_countdown()
        else:
            self.alarm.stop()
            self.floating_ball.stop_countdown()

        self.pet_window.set_pet_scale(settings["defaultScale"] / 100.0)
        self._update_auto_switch()
        self.config.save()

    def _update_auto_switch(self):
        if self.config.get("autoSwitch", False) and self.gif_manager.get_count() > 1:
            seconds = max(1, int(self.config.get("autoSwitchInterval", 30)))
            self.auto_switch_timer.start(seconds * 1000)
        else:
            self.auto_switch_timer.stop()

    def _auto_switch_gif(self):
        if not self.config.get("randomSwitch", False):
            self.gif_manager.next()
            return

        import random
        count = self.gif_manager.get_count()
        current = self.gif_manager.current_index
        choices = [index for index in range(count) if index != current]
        if choices:
            self.gif_manager.switch_to(random.choice(choices))

    def _enable_auto_start(self):
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE
            )
            exe_path = sys.argv[0]
            if os.path.splitext(exe_path)[1].lower() != ".exe":
                exe_path = os.path.abspath(sys.executable)
                script = os.path.abspath(sys.argv[0])
                exe_path = f'"{exe_path}" "{script}"'
            winreg.SetValueEx(key, "DesktopPet", 0, winreg.REG_SZ, exe_path)
            winreg.CloseKey(key)
        except Exception as e:
            self.logger.error(f"设置开机启动失败: {e}")

    def _disable_auto_start(self):
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE
            )
            try:
                winreg.DeleteValue(key, "DesktopPet")
            except FileNotFoundError:
                pass
            winreg.CloseKey(key)
        except Exception as e:
            self.logger.error(f"取消开机启动失败: {e}")

    def _quit(self):
        self.alarm.stop()
        self.floating_ball.stop_countdown()
        self.timer_ball.stop()
        self.stopwatch_ball.stop()
        self.alarm_banner.hide_banner()
        self.config.set("x", self.pet_window.x())
        self.config.set("y", self.pet_window.y())
        self.config.set("scale", self.pet_window.pet_scale)
        self.config.set("currentGif", self.gif_manager.get_current_name())
        self.config.save()
        self.logger.info("程序关闭")
        self.app.quit()

    def run(self):
        self.pet_window.show()
        self.tray.set_visible(True)
        return self.app.exec()


def main():
    app = DesktopPetApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
