from datetime import datetime, timedelta

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QTabWidget, QWidget, QListWidget, QLabel,
    QTimeEdit, QLineEdit, QSpinBox, QFormLayout,
    QDialogButtonBox, QAbstractItemView
)

from config import ConfigManager


class ClockDialog(QDialog):
    alarm_changed = Signal()
    alarm_ball_requested = Signal()
    timer_ball_requested = Signal(int)
    stopwatch_ball_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = ConfigManager()
        self.setWindowTitle("时钟")
        self.setFixedSize(380, 420)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self._setup_style()
        self._setup_ui()

    def _setup_style(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e2e;
                border: 1px solid #45475a;
                border-radius: 10px;
            }
            QTabWidget::pane {
                border: 1px solid #45475a;
                background-color: #1e1e2e;
                border-radius: 6px;
            }
            QTabBar::tab {
                background: #313244;
                color: #cdd6f4;
                padding: 8px 20px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #45475a;
                color: #f5c2e7;
            }
            QPushButton {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 6px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #45475a;
                border-color: #89b4fa;
            }
            QPushButton:pressed {
                background-color: #585b70;
            }
            QPushButton#dangerBtn {
                background-color: #f38ba8;
                color: #1e1e2e;
                border: none;
            }
            QPushButton#dangerBtn:hover {
                background-color: #f5c2e7;
            }
            QListWidget {
                background-color: #181825;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
                font-size: 13px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 6px 8px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #45475a;
            }
            QLabel {
                color: #cdd6f4;
                font-size: 13px;
            }
            QLineEdit, QTimeEdit, QSpinBox {
                background-color: #181825;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 13px;
            }
            QLineEdit:focus, QTimeEdit:focus, QSpinBox:focus {
                border-color: #89b4fa;
            }
        """)

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        tabs = QTabWidget()
        tabs.addTab(self._build_alarm_tab(), "⏰ 闹钟")
        tabs.addTab(self._build_timer_tab(), "⏳ 计时器")
        tabs.addTab(self._build_stopwatch_tab(), "⏱ 秒表")
        layout.addWidget(tabs)

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def _build_alarm_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.alarm_list = QListWidget()
        self._refresh_alarm_list()
        layout.addWidget(self.alarm_list)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("＋ 添加")
        add_btn.clicked.connect(self._add_alarm)
        btn_row.addWidget(add_btn)

        del_btn = QPushButton("✕ 删除")
        del_btn.setObjectName("dangerBtn")
        del_btn.clicked.connect(self._remove_alarm)
        btn_row.addWidget(del_btn)
        ball_btn = QPushButton("召唤悬浮球")
        ball_btn.clicked.connect(self.alarm_ball_requested.emit)
        btn_row.addWidget(ball_btn)
        layout.addLayout(btn_row)

        return tab

    def _refresh_alarm_list(self):
        self.alarm_list.clear()
        for a in self.config.get_alarms():
            status = "●" if a.get("enabled", True) else "○"
            self.alarm_list.addItem(f" {status}  {a['time']}   {a['label']}")

    def _add_alarm(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("添加闹钟")
        dlg.setFixedSize(300, 160)
        dlg.setWindowFlags(dlg.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        dlg.setStyleSheet(self.styleSheet())

        layout = QVBoxLayout(dlg)
        form = QFormLayout()
        te = QTimeEdit()
        te.setDisplayFormat("HH:mm")
        le = QLineEdit()
        form.addRow("时间:", te)
        form.addRow("标签:", le)
        layout.addLayout(form)

        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        layout.addWidget(bb)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            time_str = te.time().toString("HH:mm")
            label = le.text().strip() or "闹钟"
            alarms = self.config.get_alarms()
            alarms.append({"time": time_str, "label": label, "enabled": True})
            alarms.sort(key=lambda a: a["time"])
            self.config.set_alarms(alarms)
            self.config.save()
            self._refresh_alarm_list()
            self.alarm_changed.emit()

    def _remove_alarm(self):
        row = self.alarm_list.currentRow()
        if row < 0:
            return
        alarms = self.config.get_alarms()
        if 0 <= row < len(alarms):
            alarms.pop(row)
            self.config.set_alarms(alarms)
            self.config.save()
            self._refresh_alarm_list()
            self.alarm_changed.emit()

    def _build_timer_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        form = QFormLayout()
        input_row = QHBoxLayout()
        self.t_h = QSpinBox()
        self.t_h.setRange(0, 23)
        self.t_h.setSuffix(" 时")
        self.t_m = QSpinBox()
        self.t_m.setRange(0, 59)
        self.t_m.setSuffix(" 分")
        self.t_s = QSpinBox()
        self.t_s.setRange(0, 59)
        self.t_s.setSuffix(" 秒")
        self.t_m.setValue(5)
        input_row.addWidget(self.t_h)
        input_row.addWidget(self.t_m)
        input_row.addWidget(self.t_s)
        form.addRow("时长:", input_row)
        layout.addLayout(form)

        self.timer_display = QLabel("00:00:00")
        self.timer_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_display.setStyleSheet(
            "font-size: 36px; font-weight: bold; color: #89b4fa; padding: 16px;"
        )
        layout.addWidget(self.timer_display)

        btn_row = QHBoxLayout()
        self.timer_start_btn = QPushButton("▶ 开始")
        self.timer_start_btn.clicked.connect(self._timer_start)
        btn_row.addWidget(self.timer_start_btn)

        self.timer_pause_btn = QPushButton("⏸ 暂停")
        self.timer_pause_btn.clicked.connect(self._timer_pause)
        self.timer_pause_btn.setEnabled(False)
        btn_row.addWidget(self.timer_pause_btn)

        self.timer_reset_btn = QPushButton("↺ 重置")
        self.timer_reset_btn.clicked.connect(self._timer_reset)
        btn_row.addWidget(self.timer_reset_btn)
        layout.addLayout(btn_row)

        ball_btn = QPushButton("召唤倒计时悬浮球")
        ball_btn.clicked.connect(self._request_timer_ball)
        layout.addWidget(ball_btn)

        self.timer_timer = QTimer(self)
        self.timer_timer.setInterval(1000)
        self.timer_timer.timeout.connect(self._timer_tick)
        self.timer_remaining = 0

        return tab

    def _timer_start(self):
        h = self.t_h.value()
        m = self.t_m.value()
        s = self.t_s.value()
        self.timer_remaining = h * 3600 + m * 60 + s
        if self.timer_remaining <= 0:
            return
        self._update_timer_display()
        self.timer_timer.start()
        self.timer_start_btn.setEnabled(False)
        self.timer_pause_btn.setEnabled(True)
        self.t_h.setEnabled(False)
        self.t_m.setEnabled(False)
        self.t_s.setEnabled(False)

    def _request_timer_ball(self):
        seconds = self.t_h.value() * 3600 + self.t_m.value() * 60 + self.t_s.value()
        if seconds > 0:
            self.timer_ball_requested.emit(seconds)

    def _timer_pause(self):
        self.timer_timer.stop()
        self.timer_start_btn.setEnabled(True)
        self.timer_pause_btn.setEnabled(False)

    def _timer_reset(self):
        self.timer_timer.stop()
        self.timer_remaining = 0
        self._update_timer_display()
        self.timer_start_btn.setEnabled(True)
        self.timer_pause_btn.setEnabled(False)
        self.t_h.setEnabled(True)
        self.t_m.setEnabled(True)
        self.t_s.setEnabled(True)

    def _timer_tick(self):
        if self.timer_remaining <= 0:
            self.timer_timer.stop()
            self.timer_display.setText("⏰  时间到！")
            self._play_beep()
            self.timer_start_btn.setEnabled(True)
            self.timer_pause_btn.setEnabled(False)
            self.t_h.setEnabled(True)
            self.t_m.setEnabled(True)
            self.t_s.setEnabled(True)
            return
        self.timer_remaining -= 1
        self._update_timer_display()

    def _update_timer_display(self):
        h = self.timer_remaining // 3600
        m = (self.timer_remaining % 3600) // 60
        s = self.timer_remaining % 60
        self.timer_display.setText(f"{h:02d}:{m:02d}:{s:02d}")

    def _play_beep(self):
        try:
            import winsound
            winsound.Beep(1000, 200)
            winsound.Beep(800, 200)
            winsound.Beep(1200, 400)
        except Exception:
            pass

    def _build_stopwatch_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.sw_display = QLabel("00:00.00")
        self.sw_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sw_display.setStyleSheet(
            "font-size: 36px; font-weight: bold; color: #a6e3a1; padding: 16px;"
        )
        layout.addWidget(self.sw_display)

        btn_row = QHBoxLayout()
        self.sw_start_btn = QPushButton("▶ 开始")
        self.sw_start_btn.clicked.connect(self._sw_start)
        btn_row.addWidget(self.sw_start_btn)

        self.sw_reset_btn = QPushButton("↺ 重置")
        self.sw_reset_btn.clicked.connect(self._sw_reset)
        btn_row.addWidget(self.sw_reset_btn)
        layout.addLayout(btn_row)

        ball_btn = QPushButton("召唤秒表悬浮球")
        ball_btn.clicked.connect(self.stopwatch_ball_requested.emit)
        layout.addWidget(ball_btn)

        self.sw_list = QListWidget()
        self.sw_list.setMaximumHeight(100)
        layout.addWidget(self.sw_list)

        self.sw_timer = QTimer(self)
        self.sw_timer.setInterval(50)
        self.sw_timer.timeout.connect(self._sw_tick)
        self.sw_elapsed = 0
        self.sw_running = False

        return tab

    def _sw_start(self):
        if self.sw_running:
            self.sw_timer.stop()
            self.sw_running = False
            self.sw_start_btn.setText("▶ 开始")
        else:
            self.sw_timer.start()
            self.sw_running = True
            self.sw_start_btn.setText("⏸ 停止")

    def _sw_reset(self):
        self.sw_timer.stop()
        self.sw_running = False
        self.sw_elapsed = 0
        self.sw_start_btn.setText("▶ 开始")
        self.sw_list.clear()
        self.sw_display.setText("00:00.00")

    def _sw_tick(self):
        self.sw_elapsed += 50
        ms = self.sw_elapsed
        minutes = ms // 60000
        seconds = (ms % 60000) // 1000
        centis = (ms % 1000) // 10
        self.sw_display.setText(f"{minutes:02d}:{seconds:02d}.{centis:02d}")
