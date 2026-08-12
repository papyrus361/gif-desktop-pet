import os
from PySide6.QtCore import QObject, Signal

from utils import find_data_dir
from logger import Logger


class GifManager(QObject):
    gif_changed = Signal(str, int)

    def __init__(self, gif_dir=None, parent=None):
        super().__init__(parent)
        self.logger = Logger()
        self.default_gif_dir = find_data_dir()
        self.gif_dir = gif_dir or self.default_gif_dir
        self.gif_files = []
        self.current_index = 0
        self._scan()

    def _scan(self):
        try:
            self.gif_files = sorted(
                entry.path for entry in os.scandir(self.gif_dir)
                if entry.is_file() and entry.name.lower().endswith(".gif")
            )
        except OSError:
            self.gif_files = []
        if not self.gif_files:
            self.logger.warning("未找到GIF文件")
        else:
            self.logger.info(f"扫描到 {len(self.gif_files)} 个GIF文件")

    def refresh(self):
        old_index = self.current_index
        old_file = self.get_current()
        self._scan()
        if old_file in self.gif_files:
            self.current_index = self.gif_files.index(old_file)
        else:
            self.current_index = 0

    def set_gif_dir(self, gif_dir):
        self.gif_dir = gif_dir or self.default_gif_dir
        self.current_index = 0
        self._scan()

    def is_default_dir(self):
        return os.path.normcase(os.path.abspath(self.gif_dir)) == os.path.normcase(os.path.abspath(self.default_gif_dir))

    def get_count(self):
        return len(self.gif_files)

    def get_current(self):
        if not self.gif_files:
            return None
        return self.gif_files[self.current_index]

    def get_current_name(self):
        path = self.get_current()
        if path is None:
            return ""
        return os.path.basename(path)

    def get_all_names(self):
        return [os.path.basename(p) for p in self.gif_files]

    def get_all_paths(self):
        return list(self.gif_files)

    def next(self):
        if not self.gif_files:
            return None
        self.current_index = (self.current_index + 1) % len(self.gif_files)
        path = self.get_current()
        self.gif_changed.emit(path, self.current_index)
        self.logger.info(f"切换到GIF: {os.path.basename(path)}")
        return path

    def switch_to(self, index):
        if not self.gif_files or index < 0 or index >= len(self.gif_files):
            return None
        self.current_index = index
        path = self.get_current()
        self.gif_changed.emit(path, index)
        self.logger.info(f"切换到GIF: {os.path.basename(path)}")
        return path

    def switch_to_name(self, name):
        for i, p in enumerate(self.gif_files):
            if os.path.basename(p) == name:
                return self.switch_to(i)
        return None
