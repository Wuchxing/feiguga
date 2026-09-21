from pathlib import Path
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

from state_machine import STATE_ASSETS, PetState


class AssetManager:
    def __init__(self, asset_dir: Path):
        self.asset_dir = asset_dir
        self._originals = {}

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
