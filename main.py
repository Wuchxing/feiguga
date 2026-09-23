import math
import random
import sys
import time
from pathlib import Path

from PyQt5.QtCore import QEasingCurve, QPoint, QPropertyAnimation, QSettings, Qt, QTimer
from PyQt5.QtGui import QBitmap, QIcon, QPainter, QPixmap
from PyQt5.QtWidgets import (QAction, QApplication, QMenu, QMessageBox,
                             QSystemTrayIcon, QWidget)

from asset_manager import AssetManager
from settings_dialog import SettingsDialog
from state_machine import PetState, PetStateMachine

ROOT = Path(__file__).resolve().parent
PROCESSED = ROOT / "assets_processed"
ANIMATIONS = ROOT / "animations"


class PetWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("Feiguga", "DesktopPet")
        self.pet_size = self.settings.value("size", 200, int)
        self.base_opacity = self.settings.value("opacity", 0.95, float)
        self.assets = AssetManager(PROCESSED, ANIMATIONS)
        self.machine = PetStateMachine()
        self.pixmap = QPixmap()
        self.dragging = False
        self.drag_offset = QPoint()
        self.drag_target = QPoint()
        self.press_pos = QPoint()
        self.press_local = QPoint()
        self.last_drag_pos = QPoint()
        self.last_drag_time = 0.0
        self.last_activity = time.monotonic()
        self.hover_started = None
        self.temporary_until = 0.0
        self.walk_direction = -1
        self.auto_moving = False
        self.animation_frames = []
        self.animation_index = 0

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.resize(self.pet_size, self.pet_size + 6)
        self.setWindowOpacity(self.base_opacity)
        self._show_state(PetState.WAVE, animate=False, temporary=2.0)
        self._place_bottom_right()
        self._build_tray()

        self.tick = QTimer(self)
        self.tick.timeout.connect(self._update_motion)
        self.tick.start(33)
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self._advance_animation)
        self.animation_timer.start(33)
        self.idle_timer = QTimer(self)
        self.idle_timer.timeout.connect(self._update_idle)
        self.idle_timer.start(1000)
        self.hover_timer = QTimer(self)
        self.hover_timer.timeout.connect(self._check_hover)
        self.hover_timer.start(200)

    def _build_tray(self):
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(QIcon(self.assets.original(PetState.STANDARD)))
        menu = QMenu()
        show_action = menu.addAction("显示肥咕嘎")
        show_action.triggered.connect(self.show)
        menu.addAction("设置…", self.open_settings)
        menu.addAction("喂食", lambda: self._show_state(
            PetState.EAT, temporary=4.0, force=True))
        menu.addSeparator()
        menu.addAction("退出", QApplication.instance().quit)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(
            lambda reason: self.show() if reason == QSystemTrayIcon.DoubleClick else None
        )
        self.tray.show()

    def _place_bottom_right(self):
        area = QApplication.primaryScreen().availableGeometry()
        self.move(area.right() - self.width() - 20, area.bottom() - self.height() - 20)

    def _show_state(self, state, animate=True, temporary=0.0, force=False):
        if not self.machine.set(state, force=force) and not force:
            return
        if temporary:
            self.temporary_until = time.monotonic() + temporary
        self.animation_frames = self.assets.animation(state, self.pet_size)
        self.animation_index = 0
        new_pixmap = self.animation_frames[0]
        if animate and self.isVisible():
            fade_out = QPropertyAnimation(self, b"windowOpacity", self)
            fade_out.setDuration(150)
            fade_out.setEndValue(0.05)
            fade_out.finished.connect(lambda: self._swap_pixmap(new_pixmap, True))
            fade_out.start(QPropertyAnimation.DeleteWhenStopped)
            self._fade = fade_out
        else:
            self._swap_pixmap(new_pixmap, False)

    def _swap_pixmap(self, pixmap, fade_in):
        self.pixmap = pixmap
        self._update_input_mask()
        self.update()
        if fade_in:
            anim = QPropertyAnimation(self, b"windowOpacity", self)
            anim.setDuration(150)
            anim.setStartValue(0.05)
            anim.setEndValue(self.base_opacity)
            anim.start(QPropertyAnimation.DeleteWhenStopped)
            self._fade = anim

    def _update_input_mask(self):
        if self.pixmap.isNull():
            return
        mask = self.pixmap.mask()
        canvas = QPixmap(self.size())
        canvas.fill(Qt.color0)
        painter = QPainter(canvas)
        x = (self.width() - self.pixmap.width()) // 2
        painter.drawPixmap(x, 3, mask)
        painter.end()
        self.setMask(QBitmap(canvas))

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        x = (self.width() - self.pixmap.width()) // 2
        painter.drawPixmap(x, 3, self.pixmap)

    def mousePressEvent(self, event):
        self._touch()
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.press_pos = event.globalPos()
            self.press_local = event.pos()
            self.last_drag_pos = event.globalPos()
            self.last_drag_time = time.monotonic()
            self.drag_offset = event.globalPos() - self.frameGeometry().topLeft()
            self.drag_target = self.pos()
            self.machine.locked = True
            event.accept()

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.drag_target = event.globalPos() - self.drag_offset
            total = event.globalPos() - self.press_pos
            if total.manhattanLength() > 6:
                now = time.monotonic()
                elapsed = max(now - self.last_drag_time, 0.01)
                step = event.globalPos() - self.last_drag_pos
                speed = math.hypot(step.x(), step.y()) / elapsed
                if abs(total.y()) > abs(total.x()) * 0.75:
                    state = PetState.JUMP if total.y() < 0 else PetState.CLIMB_DOWN
                else:
                    state = PetState.RUN if speed >= 700 else PetState.JOG
                self._show_state(state, animate=False, force=True)
                self.last_drag_pos = event.globalPos()
                self.last_drag_time = now
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.dragging:
            moved = (event.globalPos() - self.press_pos).manhattanLength() > 6
            self.dragging = False
            self.machine.locked = False
            if moved:
                self._show_state(PetState.STANDARD, force=True)
            else:
                self._trigger_body_interaction(self.press_local)
            event.accept()

    def _trigger_body_interaction(self, point):
        """按角色身体比例识别额头、嘴部和腹部热点。"""
        nx = point.x() / max(self.width(), 1)
        ny = point.y() / max(self.height(), 1)
        if 0.25 <= nx <= 0.75 and 0.08 <= ny <= 0.29:
            self._show_state(PetState.ANGRY, temporary=3.0, force=True)
        elif 0.30 <= nx <= 0.72 and 0.29 < ny <= 0.50:
            self._show_state(PetState.COVER_MOUTH, temporary=3.0, force=True)
        elif 0.24 <= nx <= 0.78 and 0.50 < ny <= 0.84:
            self._show_state(PetState.EAT, temporary=4.0, force=True)
        else:
            self._show_state(random.choice([PetState.WAVE, PetState.ROLL]),
                             temporary=2.5, force=True)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.machine.locked = False
            self._touch()
            self._show_state(PetState.ROLL, temporary=3.0, force=True)

    def enterEvent(self, _event):
        self.hover_started = time.monotonic()

    def leaveEvent(self, _event):
        self.hover_started = None

    def contextMenuEvent(self, event):
        self._touch()
        menu = QMenu(self)
        expression = menu.addMenu("切换表情")
        for label, state in [("困倦", PetState.SLEEPY), ("哭泣", PetState.CRY),
                             ("生气", PetState.ANGRY), ("开心", PetState.HAPPY)]:
            action = QAction(label, menu)
            action.triggered.connect(lambda _checked=False, s=state: self._show_state(s, temporary=8, force=True))
            expression.addAction(action)
        menu.addAction("喂食", lambda: self._show_state(
            PetState.EAT, temporary=4.0, force=True))
        menu.addAction("设置…", self.open_settings)
        menu.addAction("隐藏到托盘", self.hide)
        menu.addSeparator()
        menu.addAction("退出", QApplication.instance().quit)
        menu.exec_(event.globalPos())

    def _touch(self):
        self.last_activity = time.monotonic()
        self.auto_moving = False

    def _advance_animation(self):
        if len(self.animation_frames) < 2:
            return
        self.animation_index = (self.animation_index + 1) % len(self.animation_frames)
        self.pixmap = self.animation_frames[self.animation_index]
        self.update()

    def _check_hover(self):
        if self.hover_started and time.monotonic() - self.hover_started >= 2:
            self.hover_started = None
            self._touch()
            self._show_state(PetState.WAVE, temporary=2.5, force=True)

    def _update_idle(self):
        now = time.monotonic()
        if self.dragging or now < self.temporary_until:
            return
        idle = now - self.last_activity
        if idle >= 300:
            self.auto_moving = True
            self._show_state(PetState.JOG)
        else:
            self._show_state(self.machine.idle_state(idle))

    def _update_motion(self):
        if self.dragging:
            current = self.pos()
            delta = self.drag_target - current
            self.move(current + QPoint(round(delta.x() * 0.38), round(delta.y() * 0.38)))
        elif self.auto_moving:
            screen = QApplication.screenAt(self.geometry().center()) or QApplication.primaryScreen()
            area = screen.availableGeometry()
            next_x = self.x() + self.walk_direction * 2
            if next_x < area.left() or next_x + self.width() > area.right():
                self.walk_direction *= -1
                next_x = self.x() + self.walk_direction * 2
            self.move(next_x, area.bottom() - self.height())

    def open_settings(self):
        dialog = SettingsDialog(self, self.pet_size, self.base_opacity, self._autostart_enabled())
        if dialog.exec_():
            self.pet_size = dialog.size_slider.value()
            self.base_opacity = dialog.opacity_slider.value() / 100
            self.settings.setValue("size", self.pet_size)
            self.settings.setValue("opacity", self.base_opacity)
            self.resize(self.pet_size, self.pet_size + 6)
            self.setWindowOpacity(self.base_opacity)
            self._show_state(self.machine.current, animate=False, force=True)
            self._set_autostart(dialog.autostart.isChecked())

    @staticmethod
    def _run_key():
        return QSettings(r"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run",
                         QSettings.NativeFormat)

    def _autostart_enabled(self):
        return self._run_key().contains("FeigugaDesktopPet")

    def _set_autostart(self, enabled):
        key = self._run_key()
        if enabled:
            if getattr(sys, "frozen", False):
                command = f'"{sys.executable}"'
            else:
                command = f'"{sys.executable}" "{ROOT / "main.py"}"'
            key.setValue("FeigugaDesktopPet", command)
        else:
            key.remove("FeigugaDesktopPet")


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    if not PROCESSED.exists():
        QMessageBox.critical(None, "素材未处理", "请先运行：python process_assets.py")
        return 1
    pet = PetWindow()
    pet.show()
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
