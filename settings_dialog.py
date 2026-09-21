from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QCheckBox, QDialog, QDialogButtonBox, QFormLayout, QSlider


class SettingsDialog(QDialog):
    def __init__(self, parent, size, opacity, autostart):
        super().__init__(parent)
        self.setWindowTitle("肥咕嘎设置")
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setRange(120, 400)
        self.size_slider.setValue(size)
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(30, 100)
        self.opacity_slider.setValue(round(opacity * 100))
        self.autostart = QCheckBox("登录 Windows 后自动启动")
        self.autostart.setChecked(autostart)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout = QFormLayout(self)
        layout.addRow("大小", self.size_slider)
        layout.addRow("透明度", self.opacity_slider)
        layout.addRow(self.autostart)
        layout.addRow(buttons)
