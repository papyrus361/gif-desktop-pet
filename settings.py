from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QCheckBox, QSlider, QGroupBox, QFormLayout,
    QDialogButtonBox
)

from config import ConfigManager


class SettingsDialog(QDialog):
    settings_changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = ConfigManager()
        self.setWindowTitle("设置")
        self.setFixedWidth(380)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self._original = {
            "autoStart": self.config.get("autoStart", False),
            "alwaysTop": self.config.get("alwaysTop", True),
            "alarmEnabled": self.config.get("alarmEnabled", True),
            "soundEnabled": self.config.get("soundEnabled", True),
            "autoSwitch": self.config.get("autoSwitch", False),
            "randomSwitch": self.config.get("randomSwitch", False),
            "defaultScale": self.config.get("defaultScale", 100),
            "defaultVolume": self.config.get("defaultVolume", 70),
        }
        self._setup_ui()
        self.adjustSize()

    def _setup_ui(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e2e;
            }
            QGroupBox {
                color: #89b4fa;
                font-size: 14px;
                font-weight: bold;
                border: 1px solid #45475a;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
            }
            QCheckBox {
                color: #cdd6f4;
                font-size: 13px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #45475a;
                border-radius: 4px;
                background: #181825;
            }
            QCheckBox::indicator:checked {
                background: #89b4fa;
                border-color: #89b4fa;
            }
            QLabel {
                color: #cdd6f4;
                font-size: 13px;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #313244;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                width: 16px;
                height: 16px;
                background: #89b4fa;
                border-radius: 8px;
                margin: -5px 0;
            }
            QSlider::sub-page:horizontal {
                background: #89b4fa;
                border-radius: 3px;
            }
            QPushButton {
                background: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 6px 18px;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #45475a;
                border-color: #89b4fa;
            }
        """)
        layout = QVBoxLayout(self)

        general_group = QGroupBox("通用")
        general_layout = QFormLayout(general_group)

        self.auto_start_cb = QCheckBox("开机启动")
        self.auto_start_cb.setChecked(self._original["autoStart"])
        general_layout.addRow(self.auto_start_cb)

        self.always_top_cb = QCheckBox("永远置顶")
        self.always_top_cb.setChecked(self._original["alwaysTop"])
        general_layout.addRow(self.always_top_cb)

        layout.addWidget(general_group)

        alarm_group = QGroupBox("闹钟")
        alarm_layout = QFormLayout(alarm_group)

        self.alarm_enabled_cb = QCheckBox("开启闹钟")
        self.alarm_enabled_cb.setChecked(self._original["alarmEnabled"])
        alarm_layout.addRow(self.alarm_enabled_cb)

        self.sound_enabled_cb = QCheckBox("开启声音")
        self.sound_enabled_cb.setChecked(self._original["soundEnabled"])
        alarm_layout.addRow(self.sound_enabled_cb)

        layout.addWidget(alarm_group)

        pet_group = QGroupBox("桌宠")
        pet_layout = QFormLayout(pet_group)

        self.auto_switch_cb = QCheckBox("自动切换桌宠")
        self.auto_switch_cb.setChecked(self._original["autoSwitch"])
        pet_layout.addRow(self.auto_switch_cb)

        self.random_switch_cb = QCheckBox("随机变化")
        self.random_switch_cb.setChecked(self._original["randomSwitch"])
        pet_layout.addRow(self.random_switch_cb)

        scale_layout = QHBoxLayout()
        self.scale_slider = QSlider(Qt.Orientation.Horizontal)
        self.scale_slider.setRange(30, 500)
        self.scale_slider.setValue(self._original["defaultScale"])
        self.scale_label = QLabel(f"{self._original['defaultScale']}%")
        self.scale_slider.valueChanged.connect(
            lambda v: self.scale_label.setText(f"{v}%")
        )
        scale_layout.addWidget(self.scale_slider)
        scale_layout.addWidget(self.scale_label)
        pet_layout.addRow("默认缩放:", scale_layout)

        volume_layout = QHBoxLayout()
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(self._original["defaultVolume"])
        self.volume_label = QLabel(f"{self._original['defaultVolume']}%")
        self.volume_slider.valueChanged.connect(
            lambda v: self.volume_label.setText(f"{v}%")
        )
        volume_layout.addWidget(self.volume_slider)
        volume_layout.addWidget(self.volume_label)
        pet_layout.addRow("默认音量:", volume_layout)

        layout.addWidget(pet_group)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._save)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _save(self):
        self.config.set("autoStart", self.auto_start_cb.isChecked())
        self.config.set("alwaysTop", self.always_top_cb.isChecked())
        self.config.set("alarmEnabled", self.alarm_enabled_cb.isChecked())
        self.config.set("soundEnabled", self.sound_enabled_cb.isChecked())
        self.config.set("autoSwitch", self.auto_switch_cb.isChecked())
        self.config.set("randomSwitch", self.random_switch_cb.isChecked())
        self.config.set("defaultScale", self.scale_slider.value())
        self.config.set("defaultVolume", self.volume_slider.value())
        self.config.save()
        self.settings_changed.emit({
            "autoStart": self.auto_start_cb.isChecked(),
            "alwaysTop": self.always_top_cb.isChecked(),
            "alarmEnabled": self.alarm_enabled_cb.isChecked(),
            "soundEnabled": self.sound_enabled_cb.isChecked(),
            "autoSwitch": self.auto_switch_cb.isChecked(),
            "randomSwitch": self.random_switch_cb.isChecked(),
            "defaultScale": self.scale_slider.value(),
            "defaultVolume": self.volume_slider.value(),
        })
        self.accept()

    def reject(self):
        self.config.load()
        super().reject()
