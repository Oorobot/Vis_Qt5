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
