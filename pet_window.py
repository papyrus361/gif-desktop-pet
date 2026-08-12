from PySide6.QtCore import Qt, QPoint, Signal
from PySide6.QtGui import QMovie, QAction, QImageReader
from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QMenu, QApplication
)

from config import ConfigManager
from gif_manager import GifManager
from logger import Logger


class PetWindow(QWidget):
    alarm_dialog_requested = Signal()
    add_alarm_requested = Signal()
    alarm_toggled = Signal(int, bool)
    clock_requested = Signal()
    settings_dialog_requested = Signal()
    clone_requested = Signal(object)
    close_requested = Signal(object)
    gif_folder_requested = Signal(object)
    default_gif_folder_requested = Signal(object)

    def __init__(self, gif_manager=None, parent=None):
        super().__init__(parent)
        self.config = ConfigManager()
        self.logger = Logger()
        self.gif_manager = gif_manager or GifManager()

        self.pet_scale = self.config.get("scale", 1.0)
        self.dragging = False
        self.drag_offset = QPoint()
        self.movie = None
        self.alarm_active = False
        self.gif_size = (200, 200)
        self.normalized_scale = 1.0
        self._frame_loaded = False

        self._setup_window()
        self._setup_ui()
        self._setup_context_menu()
        self._load_gif()
        self._restore_position()

    def _setup_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.gif_label = QLabel(self)
        self.gif_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.gif_label.setScaledContents(True)
        self.gif_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.layout.addWidget(self.gif_label)

        self.countdown_bubble = None

    def _setup_context_menu(self):
        self.context_menu = QMenu(self)
        self.context_menu.setStyleSheet("""
            QMenu {
                background-color: #1e1e2e;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 8px;
                padding: 6px;
            }
            QMenu::item {
                padding: 8px 28px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #89b4fa;
                color: #1e1e2e;
            }
            QMenu::separator {
                height: 1px;
                background: #45475a;
                margin: 4px 10px;
            }
            QMenu {
                font-size: 13px;
            }
        """)

    def show_context_menu(self, pos):
        self.context_menu.clear()

        switch_menu = QMenu("切换桌宠 ▶", self)
        self._build_switch_menu(switch_menu)
        self.context_menu.addMenu(switch_menu)

        clock_action = QAction("⏰ 时钟", self)
        clock_action.triggered.connect(self._on_clock_clicked)
        self.context_menu.addAction(clock_action)

        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self._on_settings_clicked)
        self.context_menu.addAction(settings_action)

        clone_action = QAction("克隆桌宠", self)
        clone_action.triggered.connect(lambda: self.clone_requested.emit(self))
        self.context_menu.addAction(clone_action)

        gif_folder_action = QAction("切换 GIF 文件夹...", self)
        gif_folder_action.triggered.connect(lambda: self.gif_folder_requested.emit(self))
        self.context_menu.addAction(gif_folder_action)

        default_folder_action = QAction("使用默认：秦始皇", self)
        default_folder_action.triggered.connect(lambda: self.default_gif_folder_requested.emit(self))
        self.context_menu.addAction(default_folder_action)

        about_action = QAction("关于", self)
        about_action.triggered.connect(self._on_about_clicked)
        self.context_menu.addAction(about_action)

        self.context_menu.addSeparator()

        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self._on_quit_clicked)
        self.context_menu.addAction(quit_action)

        self.context_menu.exec(self.mapToGlobal(pos))

    def _build_switch_menu(self, menu):
        names = self.gif_manager.get_all_names()
        current_name = self.gif_manager.get_current_name()
        for i, name in enumerate(names):
            action = QAction(name, self)
            action.setCheckable(True)
            action.setChecked(name == current_name)
            idx = i
            action.triggered.connect(lambda checked, ix=idx: self._switch_by_index(ix))
            menu.addAction(action)

    def _switch_by_index(self, index):
        self.gif_manager.switch_to(index)

    def _build_alarm_menu(self, menu):
        alarms = self.config.get_alarms()
        for i, alarm in enumerate(alarms):
            action = QAction(f"{alarm['time']}  {alarm['label']}", self)
            action.setCheckable(True)
            action.setChecked(alarm.get("enabled", True))
            idx = i
            action.triggered.connect(lambda checked, ix=idx: self._toggle_alarm(ix, checked))
            menu.addAction(action)

        menu.addSeparator()
        add_action = QAction("添加闹钟...", self)
        add_action.triggered.connect(self.add_alarm_requested.emit)
        menu.addAction(add_action)

        manage_action = QAction("管理闹钟...", self)
        manage_action.triggered.connect(self._on_alarm_clicked)
        menu.addAction(manage_action)

    def _toggle_alarm(self, index, enabled):
        alarms = self.config.get_alarms()
        if 0 <= index < len(alarms):
            alarms[index]["enabled"] = enabled
            self.config.set_alarms(alarms)
            self.config.save()
            self.alarm_toggled.emit(index, enabled)

    def _on_alarm_clicked(self):
        self.alarm_dialog_requested.emit()

    def _on_clock_clicked(self):
        self.clock_requested.emit()

    def _on_settings_clicked(self):
        self.settings_dialog_requested.emit()

    def _on_about_clicked(self):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.about(self, "关于",
                          "DesktopPet v1.0\n"
                          "Windows GIF桌宠\n"
                          "PySide6 构建")

    def _on_quit_clicked(self):
        self.close_requested.emit(self)

    def _compute_normalized_scale(self):
        base_w, base_h = self.gif_size
        if base_w <= 0 or base_h <= 0:
            self.normalized_scale = 1.0
            return
        target_diagonal = 250.0
        gif_diagonal = (base_w ** 2 + base_h ** 2) ** 0.5
        self.normalized_scale = (target_diagonal / gif_diagonal) ** 0.5

    def _load_gif(self):
        path = self.gif_manager.get_current()
        if not path:
            self.gif_label.setText("未找到GIF")
            self.resize(200, 200)
            return

        reader = QImageReader(path)
        size = reader.size()
        if size.isValid() and size.width() > 0 and size.height() > 0:
            self.gif_size = (size.width(), size.height())
            self._compute_normalized_scale()
            self._frame_loaded = True
        else:
            self._frame_loaded = False

        self.movie = QMovie(path)
        self.movie.setCacheMode(QMovie.CacheMode.CacheAll)
        self.movie.frameChanged.connect(self._on_frame_changed)
        self.movie.start()

        self._update_size()
        self.gif_label.setMovie(self.movie)

    def _on_frame_changed(self, frame):
        if not self.movie:
            return
        if self._frame_loaded:
            return
        sender = self.sender()
        if sender is not self.movie:
            return
        size = self.movie.currentImage().size()
        if size.isValid() and size.width() > 0 and size.height() > 0:
            self.gif_size = (size.width(), size.height())
            self._compute_normalized_scale()
            self._update_size()
            self._frame_loaded = True

    def _update_size(self, anchor_center=None):
        base_w, base_h = self.gif_size
        display_scale = self.pet_scale * self.normalized_scale
        w = max(1, int(base_w * display_scale))
        h = max(1, int(base_h * display_scale))

        center = anchor_center or self.frameGeometry().center()
        self.resize(w, h)
        self.move(center - self.rect().center())

    def set_pet_scale(self, scale):
        self.pet_scale = max(0.3, min(5.0, scale))
        self._update_size()
        self.config.set("scale", self.pet_scale)

    def _restore_position(self):
        x = self.config.get("x")
        y = self.config.get("y")
        screen = QApplication.primaryScreen()
        if screen:
            sg = screen.availableGeometry()
            if x is None:
                x = sg.width() - self.width() - 50
            if y is None:
                y = sg.height() - self.height() - 80
            x = max(0, min(x, sg.width() - self.width()))
            y = max(0, min(y, sg.height() - self.height()))
            self.move(x, y)

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def mousePressEvent(self, event):
        if self.alarm_active and event.button() == Qt.MouseButton.LeftButton:
            app = QApplication.instance()
            if hasattr(app, '_pet_app') and app._pet_app:
                app._pet_app.dismiss_alarm()
            event.accept()
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_offset)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.dragging:
            self.dragging = False
            self.config.set("x", self.x())
            self.config.set("y", self.y())
            event.accept()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.gif_manager.next()
            event.accept()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()

        # 记录缩放前的浮点中心，确保缩放后中心位置不变
        center = self.frameGeometry().center()

        if delta > 0:
            new_scale = self.pet_scale + 0.1
        else:
            new_scale = self.pet_scale - 0.1

        self.pet_scale = max(0.3, min(5.0, new_scale))
        self._update_size(anchor_center=center)
        self.config.set("scale", self.pet_scale)
        event.accept()

    def contextMenuEvent(self, event):
        self.show_context_menu(event.pos())

    def switch_gif(self, path):
        if self.movie:
            self.movie.stop()
            self.movie.frameChanged.disconnect(self._on_frame_changed)
        self._frame_loaded = False
        self._load_gif()

    def set_always_top(self, enabled):
        flags = self.windowFlags()
        if enabled:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()

    def set_click_through(self, enabled):
        if enabled:
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        else:
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
