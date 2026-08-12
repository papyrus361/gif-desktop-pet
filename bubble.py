from PySide6.QtCore import Qt, QTimer, QPoint, Signal
from PySide6.QtGui import QFont, QCursor, QAction
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication, QMenu

from config import ConfigManager


class BubbleOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)

        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setWordWrap(True)
        self.label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: bold;
                background-color: rgba(0, 0, 0, 180);
                border-radius: 10px;
                padding: 12px;
            }
        """)
        self.layout.addWidget(self.label)
        self.adjustSize()

    def show_at(self, text, pet_window):
        self.label.setText(text)
        self.adjustSize()
        self._position_near(pet_window)
        self.show()
        self.raise_()

    def _position_near(self, pet_window):
        pet_rect = pet_window.frameGeometry()
        x = pet_rect.center().x() - self.width() // 2
        y = pet_rect.top() - self.height() - 10
        screen = pet_window.screen()
        if screen:
            sg = screen.availableGeometry()
            if y < sg.top():
                y = pet_rect.bottom() + 10
            x = max(sg.left(), min(x, sg.right() - self.width()))
            y = max(sg.top(), min(y, sg.bottom() - self.height()))
        self.move(x, y)

    def hide_bubble(self):
        self.hide()


class FloatingBall(QWidget):
    alarm_toggled = Signal(int, bool)
    add_alarm_requested = Signal()
    manage_alarm_requested = Signal()
    dismiss_requested = Signal()
    close_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self.config = ConfigManager()
        self.ball_size = 80
        self.dragging = False
        self.drag_offset = QPoint()
        self.alarm_active = False
        self._alarms = []
        self._target_label = ""

        self._setup_ui()

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._tick)

    def _setup_ui(self):
        self.setFixedSize(self.ball_size, self.ball_size)

        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setGeometry(0, 0, self.ball_size, self.ball_size)
        self.label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._apply_style(False)

    def _apply_style(self, alarm_mode):
        r = self.ball_size // 2
        if alarm_mode:
            css = (
                f"QLabel {{ color: #f38ba8; font-size: 14px; font-weight: bold;"
                f" background-color: qradialgradient(cx:0.5,cy:0.5,radius:0.5,"
                f"  stop:0 rgba(30,30,46,230), stop:1 rgba(243,139,168,200));"
                f" border-radius: {r}px; padding: 4px;"
                f" border: 3px solid #f38ba8; }}"
            )
        else:
            css = (
                f"QLabel {{ color: #89b4fa; font-size: 12px; font-weight: bold;"
                f" background-color: qradialgradient(cx:0.5,cy:0.5,radius:0.5,"
                f"  stop:0 rgba(30,30,46,210), stop:1 rgba(49,50,68,200));"
                f" border-radius: {r}px; padding: 4px;"
                f" border: 2px solid #45475a; }}"
            )
        self.label.setStyleSheet(css)

    def set_alarms(self, alarms):
        self._alarms = alarms

    def start_countdown(self):
        self.alarm_active = False
        self._apply_style(False)
        self._tick()
        self.timer.start()
        self.show()
        self.raise_()

    def _tick(self):
        from datetime import datetime
        now = datetime.now()
        current_minutes = now.hour * 60 + now.minute

        closest = None
        closest_diff = None
        for alarm in self._alarms:
            if not alarm.get("enabled", True):
                continue
            parts = alarm["time"].split(":")
            alarm_minutes = int(parts[0]) * 60 + int(parts[1])
            diff = alarm_minutes - current_minutes
            if diff <= 0:
                diff += 24 * 60
            if closest_diff is None or diff < closest_diff:
                closest = alarm
                closest_diff = diff

        if closest is None:
            self.label.setText("--:--")
            if not self.alarm_active:
                self.timer.stop()
            return

        self._target_label = closest["label"]
        total_seconds = closest_diff * 60 - now.second
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60

        if hours > 0:
            text = f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            text = f"{minutes:02d}:{secs:02d}"
        self.label.setText(text)

    def show_alarm_mode(self):
        self.alarm_active = True
        self.timer.stop()
        self._apply_style(True)
        self.label.setText("关闭")
        screen = QApplication.primaryScreen()
        if screen:
            sg = screen.availableGeometry()
            self.move(sg.center().x() - self.ball_size // 2,
                      sg.center().y() - self.ball_size // 2)
        self.show()
        self.raise_()

    def stop_countdown(self):
        self.timer.stop()
        self.hide()
        self.alarm_active = False

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.alarm_active:
            self.dismiss_requested.emit()
            event.accept()
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        elif event.button() == Qt.MouseButton.RightButton:
            self._show_context_menu(event.globalPosition().toPoint())
            event.accept()

    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_offset)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.dragging:
            self.dragging = False
            event.accept()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta > 0:
            self.ball_size = min(150, self.ball_size + 10)
        else:
            self.ball_size = max(40, self.ball_size - 10)
        self.setFixedSize(self.ball_size, self.ball_size)
        self.label.setGeometry(0, 0, self.ball_size, self.ball_size)
        self._apply_style(self.alarm_active)
        event.accept()

    def _show_context_menu(self, global_pos):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #1e1e2e; color: #cdd6f4;
                    border: 1px solid #45475a; border-radius: 8px; padding: 6px; }
            QMenu::item { padding: 8px 28px; border-radius: 4px; }
            QMenu::item:selected { background-color: #89b4fa; color: #1e1e2e; }
            QMenu::separator { height: 1px; background: #45475a; margin: 4px 10px; }
        """)

        alarms = self.config.get_alarms()
        has_alarms = False
        for i, alarm in enumerate(alarms):
            has_alarms = True
            action = QAction(f"{alarm['time']}  {alarm['label']}", menu)
            action.setCheckable(True)
            action.setChecked(alarm.get("enabled", True))
            idx = i
            action.triggered.connect(lambda checked, ix=idx: self._toggle_alarm(ix, checked))
            menu.addAction(action)

        if has_alarms:
            menu.addSeparator()

        add_action = QAction("添加闹钟...", menu)
        add_action.triggered.connect(self.add_alarm_requested.emit)
        menu.addAction(add_action)

        manage_action = QAction("管理闹钟...", menu)
        manage_action.triggered.connect(self.manage_alarm_requested.emit)
        menu.addAction(manage_action)

        menu.addSeparator()
        close_action = QAction("关闭闹钟悬浮球", menu)
        close_action.triggered.connect(self.close_requested.emit)
        menu.addAction(close_action)

        menu.exec(global_pos)

    def _toggle_alarm(self, index, enabled):
        alarms = self.config.get_alarms()
        if 0 <= index < len(alarms):
            alarms[index]["enabled"] = enabled
            self.config.set_alarms(alarms)
            self.config.save()
            self.alarm_toggled.emit(index, enabled)


class ClockFloatingBall(QWidget):
    """A small draggable clock that opens the full clock panel on double-click."""

    clock_requested = Signal()
    close_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ball_size = 82
        self.dragging = False
        self.drag_offset = QPoint()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFixedSize(self.ball_size, self.ball_size)
        self.label = QLabel(self)
        self.label.setGeometry(0, 0, self.ball_size, self.ball_size)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.label.setStyleSheet("""
            QLabel {
                color: #f5e0dc; font-size: 17px; font-weight: bold;
                background-color: qradialgradient(cx: 0.35, cy: 0.25, radius: 0.8,
                    stop: 0 #585b70, stop: 0.55 #313244, stop: 1 #181825);
                border: 2px solid #89b4fa; border-radius: 41px;
            }
        """)
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._tick)
        self._tick()

    def start(self):
        screen = QApplication.primaryScreen()
        if screen:
            area = screen.availableGeometry()
            self.move(area.right() - self.ball_size - 20, area.top() + 20)
        self.show()
        self.timer.start()

    def stop(self):
        self.timer.stop()
        self.hide()

    def _tick(self):
        from datetime import datetime
        self.label.setText(datetime.now().strftime("%H:%M\\n%S"))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        elif event.button() == Qt.MouseButton.RightButton:
            self._show_context_menu(event.globalPosition().toPoint())
            event.accept()

    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_offset)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.dragging:
            self.dragging = False
            event.accept()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clock_requested.emit()
            event.accept()

    def _show_context_menu(self, global_pos):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background: #1e1e2e; color: #cdd6f4; border: 1px solid #45475a;
                    border-radius: 8px; padding: 5px; }
            QMenu::item { padding: 7px 24px; border-radius: 4px; }
            QMenu::item:selected { background: #89b4fa; color: #1e1e2e; }
        """)
        open_action = menu.addAction("打开时钟面板")
        open_action.triggered.connect(self.clock_requested.emit)
        close_action = menu.addAction("关闭时钟悬浮球")
        close_action.triggered.connect(self.close_requested.emit)
        menu.exec(global_pos)


class _TimeFloatingBall(QWidget):
    """Base widget for countdown and stopwatch floating balls."""

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.title = title
        self.dragging = False
        self.drag_offset = QPoint()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(108, 78)
        self.label = QLabel(self)
        self.label.setGeometry(0, 0, 108, 78)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.label.setStyleSheet("""
            QLabel { color: #cdd6f4; font-size: 18px; font-weight: bold;
                     background: rgba(30, 30, 46, 235); border: 2px solid #a6e3a1;
                     border-radius: 14px; }
        """)
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._tick)

    def _place(self):
        screen = QApplication.primaryScreen()
        if screen:
            area = screen.availableGeometry()
            self.move(area.right() - self.width() - 25, area.top() + 115)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        elif event.button() == Qt.MouseButton.RightButton:
            menu = QMenu(self)
            close_action = menu.addAction(f"关闭{self.title}悬浮球")
            close_action.triggered.connect(self.stop)
            menu.exec(event.globalPosition().toPoint())
            event.accept()

    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_offset)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            event.accept()


class TimerFloatingBall(_TimeFloatingBall):
    def __init__(self, parent=None):
        super().__init__("倒计时", parent)
        self.remaining = 0

    def start(self, seconds):
        self.remaining = seconds
        self._place()
        self._tick()
        self.show()
        self.timer.start()

    def _tick(self):
        if self.remaining <= 0:
            self.timer.stop()
            self.label.setText("倒计时\n完成！")
            return
        h, rest = divmod(self.remaining, 3600)
        m, s = divmod(rest, 60)
        self.label.setText(f"倒计时\n{h:02d}:{m:02d}:{s:02d}")
        self.remaining -= 1

    def stop(self):
        self.timer.stop()
        self.hide()


class StopwatchFloatingBall(_TimeFloatingBall):
    def __init__(self, parent=None):
        super().__init__("秒表", parent)
        self.elapsed = 0

    def start(self):
        self.elapsed = 0
        self._place()
        self._tick()
        self.show()
        self.timer.start()

    def _tick(self):
        self.elapsed += 1
        minutes, seconds = divmod(self.elapsed, 60)
        self.label.setText(f"秒表\n{minutes:02d}:{seconds:02d}")

    def stop(self):
        self.timer.stop()
        self.hide()


class AlarmBanner(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 18px;
                font-weight: bold;
                background-color: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(220, 50, 50, 220),
                    stop:1 rgba(180, 30, 30, 220)
                );
                padding: 14px 32px;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }
        """)
        self.layout.addWidget(self.label)

    def show_alarm(self, label):
        self.label.setText(f"⏰  {label}  时间到了！")
        self.adjustSize()
        self._position_at_bottom()
        self.show()
        self.raise_()

    def _position_at_bottom(self):
        screen = QApplication.primaryScreen()
        if screen:
            sg = screen.availableGeometry()
            self.setFixedWidth(sg.width())
            self.adjustSize()
            self.move(sg.left(), sg.bottom() - self.height())

    def hide_banner(self):
        self.hide()
