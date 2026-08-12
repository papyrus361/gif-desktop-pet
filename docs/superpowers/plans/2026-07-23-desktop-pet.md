# DesktopPet Windows GIF桌宠 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Windows desktop pet application that displays transparent GIF pets with mouse interaction, alarm clock, system tray, and configuration persistence.

**Architecture:** PySide6 (Qt6) application with modular single-file-per-class design. QMainWindow-less approach using QWidget with frameless transparent window. Signal/slot for inter-module communication. JSON file for config persistence.

**Tech Stack:** Python 3.13, PySide6, pywin32, QMovie, PyInstaller

---

### Task 1: Project Scaffold & Core Infrastructure

**Files:**
- Create: `C:\Users\31960\Desktop\桌宠\DesktopPet\requirements.txt`
- Create: `C:\Users\31960\Desktop\桌宠\DesktopPet\config.py`
- Create: `C:\Users\31960\Desktop\桌宠\DesktopPet\logger.py`
- Create: `C:\Users\31960\Desktop\桌宠\DesktopPet\utils.py`

- [ ] **Step 1: Write requirements.txt**

```
PySide6>=6.6.0
pywin32>=306
```

- [ ] **Step 2: Write config.py** - ConfigManager singleton that loads/saves `config.json` with fields: x, y, scale, currentGif, alwaysTop, autoStart, clickThrough, alarmEnabled, soundEnabled, autoSwitch, defaultScale, defaultVolume, alarms[]. Uses Python json module.

- [ ] **Step 3: Write logger.py** - Logger class that writes to `logs/YYYY-MM-DD.log` with levels: INFO, WARNING, ERROR. Logs: startup, shutdown, GIF switch, alarm trigger, exceptions.

- [ ] **Step 4: Write utils.py** - Resource path helper (compatible with PyInstaller), find_data_dir() for locating qinren/ folder relative to executable.

---

### Task 2: GIF Manager

**Files:**
- Create: `C:\Users\31960\Desktop\桌宠\DesktopPet\gif_manager.py`

- [ ] **Step 1: Write GifManager class**
  - Scans `qinren/` directory for `*.gif` files on init
  - Maintains list of GIF file paths
  - Provides `get_current()`, `next()`, `switch_to(index)` methods
  - Emits `gif_changed(path)` signal when switched
  - Handles empty directory (raises descriptive error)
  - Skips corrupted GIFs silently

---

### Task 3: Animation System

**Files:**
- Create: `C:\Users\31960\Desktop\桌宠\DesktopPet\animation.py`

- [ ] **Step 1: Write AnimationManager class**
  - `scale_to(widget, from_scale, to_scale, duration_ms)` - smooth scale animation at 60fps using QVariantAnimation
  - `shake(widget, duration_ms=8000, fps=25)` - horizontal shake oscillation with decaying amplitude
  - `bounce(widget)` - placeholder for vertical bounce (future use)
  - `fade_in(widget)`, `fade_out(widget)` - window opacity transitions

---

### Task 4: Pet Window

**Files:**
- Create: `C:\Users\31960\Desktop\桌宠\DesktopPet\pet_window.py`

- [ ] **Step 1: Write PetWindow (QWidget)**
  - Frameless, always-on-top, transparent background (WA_TranslucentBackground)
  - QLabel with QMovie for GIF display
  - No taskbar icon (Qt.Tool flag)
  - Mouse drag support (mousePressEvent, mouseMoveEvent, mouseReleaseEvent)
  - Double-click to cycle GIFs
  - WheelEvent for zoom (30%-500% range, 10% steps, centered)
  - Scale is stored as factor, applied via widget resize
  - Right-click context menu: 切换桌宠 > (submenu of all GIFs), 闹钟, 设置, 关于, 退出
  - Signals: position_changed(x,y), scale_changed(scale), gif_switch_requested, alarm_clicked, settings_requested, quit_requested
  - Method: `show_alarm_bubble(text)` - shows overlay text bubble
  - Method: `clear_alarm()` - removes bubble, restores state

---

### Task 5: Alarm System

**Files:**
- Create: `C:\Users\31960\Desktop\桌宠\DesktopPet\alarm.py`

- [ ] **Step 1: Write AlarmManager class**
  - Loads alarms from config (list of {time, label})
  - Runs a QTimer checking every 30s if any alarm matches current time
  - When alarm triggers: emit `alarm_triggered(alarm_label)` signal
  - Phase sequence:
    1. Scale up 100% -> 400% over 0.5s
    2. Shake for 8s at 25fps
    3. Play alarm sound (supports .wav and .mp3 via QSoundEffect or pygame)
    4. Show bubble text: "主人！\n到时间啦！\n快去完成{alarm_label}！"
  - Click on pet during alarm: emit `alarm_dismissed`, stop sound, restore scale
  - Methods: `start()`, `stop()`, `dismiss()`, `play_sound()`, `stop_sound()`

---

### Task 6: System Tray

**Files:**
- Create: `C:\Users\31960\Desktop\桌宠\DesktopPet\tray.py`

- [ ] **Step 1: Write TrayManager class**
  - QSystemTrayIcon with icon from assets/icon.ico
  - Context menu: 显示桌宠, 隐藏桌宠, -, 切换桌宠 > (submenu), 闹钟, 设置, -, 退出
  - Signals: show_requested, hide_requested, switch_gif_requested(index), alarm_requested, settings_requested, quit_requested
  - Window close event -> hide to tray (override closeEvent in main)

---

### Task 7: Settings Dialog

**Files:**
- Create: `C:\Users\31960\Desktop\桌宠\DesktopPet\settings.py`

- [ ] **Step 1: Write SettingsDialog (QDialog)**
  - Checkboxes: 开机启动, 永远置顶, 点击穿透, 开启闹钟, 开启声音, 自动切换桌宠
  - SpinBox/Slider: 默认缩放 (30-500%), 默认音量 (0-100)
  - Save button writes to config and emits settings_changed(config_dict) signal
  - Cancel button reverts changes
  - Opens with current config values pre-filled

---

### Task 8: Main Entry Point

**Files:**
- Create: `C:\Users\31960\Desktop\桌宠\DesktopPet\main.py`

- [ ] **Step 1: Write main.py**
  - QApplication setup with app.setQuitOnLastWindowClosed(False)
  - Initialize Logger, ConfigManager, GifManager
  - Create PetWindow, TrayManager, AlarmManager, AnimationManager
  - Wire all signals/slots between components
  - Restore window position and scale from config
  - Handle alarm flow: trigger -> animate -> sound -> bubble -> dismiss
  - Handle settings changes (alwaysTop, clickThrough, etc.)
  - On quit: save config, stop alarm, close log

---

### Task 9: Packaging Script

**Files:**
- Create: `C:\Users\31960\Desktop\桌宠\DesktopPet\build.bat`
- Create: `C:\Users\31960\Desktop\桌宠\DesktopPet\DesktopPet.spec`

- [ ] **Step 1: Write build.bat** - PyInstaller one-file build script
- [ ] **Step 2: Write .spec file** - Include data dirs (qinren, assets)
