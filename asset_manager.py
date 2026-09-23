from pathlib import Path
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

from state_machine import STATE_ASSETS, PetState


class AssetManager:
    def __init__(self, asset_dir: Path, animation_dir: Path = None):
        self.asset_dir = asset_dir
        self.animation_dir = animation_dir
        self._originals = {}
        self._animation_key = None
        self._animation_frames = []

    def original(self, state: PetState) -> QPixmap:
        if state not in self._originals:
            path = self.asset_dir / STATE_ASSETS[state]
            pixmap = QPixmap(str(path))
            if pixmap.isNull():
                raise FileNotFoundError(f"无法加载素材：{path}")
            self._originals[state] = pixmap
        return self._originals[state]

    def scaled(self, state: PetState, size: int) -> QPixmap:
        return self.original(state).scaled(
            size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )

    def animation(self, state: PetState, size: int):
        """只缓存当前状态的 60 帧，状态切换时释放上一组。"""
        key = (state, size)
        if key == self._animation_key:
            return self._animation_frames
        frames = []
        folder = self.animation_dir / state.value if self.animation_dir else None
        if folder and folder.exists():
            for path in sorted(folder.glob("frame_*.png")):
                pixmap = QPixmap(str(path))
                if not pixmap.isNull():
                    frames.append(pixmap.scaled(
                        size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation
                    ))
        if not frames:
            frames = [self.scaled(state, size)]
        self._animation_key = key
        self._animation_frames = frames
        return frames
