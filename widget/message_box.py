from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QMessageBox


def information(text: str):
    messageBox = QMessageBox(QMessageBox.Icon.Information, "信息", text, QMessageBox.StandardButton.Ok)
    messageBox.exec()


def question(text: str):
    messageBox = QMessageBox(QMessageBox.Icon.Question, "问题", text, QMessageBox.StandardButton.Yes)
    messageBox.exec()


def warning(text: str):
    messageBox = QMessageBox(QMessageBox.Icon.Warning, "警告", text, QMessageBox.StandardButton.Ok)
    messageBox.exec()


def error(text: str):
    messageBox = QMessageBox(QMessageBox.Icon.Critical, "错误", text, QMessageBox.StandardButton.Abort)
    messageBox.exec()


class TimerMessageBox(QMessageBox):
    def __init__(self, icon: QMessageBox.Icon, title: str):
        super().__init__()
        self.setText("已用时：   0秒.")
        self.setIcon(icon)
        self.setWindowTitle(title)
        # 设置为始终在最顶层
        # self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        # 移除所有按钮
        self.setStandardButtons(QMessageBox.StandardButton.NoButton)

        # 计时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_message)
        self.seconds = 0

    def exec(self) -> int:
        self.timer.start(1000)
        return super().exec()

    def accept(self) -> None:
        self.timer.stop()
        self.seconds = 0
        self.setText("已用时：   0秒.")
        return super().accept()

    def update_message(self):
        self.seconds += 1
        self.setText(f"已用时：{self.seconds:>4d}秒.")
