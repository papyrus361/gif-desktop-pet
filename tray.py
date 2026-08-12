from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import QSystemTrayIcon, QMenu

from utils import resource_path


class TrayManager(QObject):
    show_requested = Signal()
    hide_requested = Signal()
    switch_gif_requested = Signal(int)
    alarm_requested = Signal()
    settings_requested = Signal()
    gif_folder_requested = Signal()
    default_gif_folder_requested = Signal()
    quit_requested = Signal()

    def __init__(self, gif_manager=None, parent=None):
        super().__init__(parent)
        self.gif_manager = gif_manager
        self.tray_icon = None
        self.menu = QMenu()
        self._setup()

    def _setup(self):
        icon_path = resource_path("assets/icon.ico")
        icon = QIcon(icon_path)
        self.tray_icon = QSystemTrayIcon(icon)
        self.tray_icon.setToolTip("DesktopPet")
        self._build_menu()
        self.tray_icon.setContextMenu(self.menu)
        self.tray_icon.activated.connect(self._on_activated)
        self.tray_icon.show()

    def _build_menu(self):
        self.menu.clear()

        self.show_action = QAction("显示桌宠")
        self.show_action.triggered.connect(self.show_requested.emit)
        self.menu.addAction(self.show_action)

        self.hide_action = QAction("隐藏桌宠")
        self.hide_action.triggered.connect(self.hide_requested.emit)
        self.menu.addAction(self.hide_action)

        self.menu.addSeparator()

        switch_menu = self.menu.addMenu("切换桌宠")
        self._build_switch_submenu(switch_menu)

        alarm_action = QAction("闹钟")
        alarm_action.triggered.connect(self.alarm_requested.emit)
        self.menu.addAction(alarm_action)

        settings_action = QAction("设置")
        settings_action.triggered.connect(self.settings_requested.emit)
        self.menu.addAction(settings_action)

        gif_folder_action = QAction("切换 GIF 文件夹...")
        gif_folder_action.triggered.connect(self.gif_folder_requested.emit)
        self.menu.addAction(gif_folder_action)

        default_folder_action = QAction("使用默认：秦始皇")
        default_folder_action.triggered.connect(self.default_gif_folder_requested.emit)
        self.menu.addAction(default_folder_action)

        self.menu.addSeparator()

        quit_action = QAction("退出")
        quit_action.triggered.connect(self.quit_requested.emit)
        self.menu.addAction(quit_action)

    def _build_switch_submenu(self, menu):
        if not self.gif_manager:
            return
        names = self.gif_manager.get_all_names()
        current = self.gif_manager.get_current_name()
        for i, name in enumerate(names):
            action = QAction(name)
            action.setCheckable(True)
            action.setChecked(name == current)
            idx = i
            action.triggered.connect(lambda checked, ix=idx: self.switch_gif_requested.emit(ix))
            menu.addAction(action)

    def refresh_switch_menu(self):
        self._build_menu()

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_requested.emit()

    def set_visible(self, visible):
        self.show_action.setEnabled(not visible)
        self.hide_action.setEnabled(visible)

    def show_message(self, title, message, duration_ms=3000):
        if self.tray_icon:
            self.tray_icon.showMessage(
                title, message, QSystemTrayIcon.MessageIcon.Information, duration_ms
            )
