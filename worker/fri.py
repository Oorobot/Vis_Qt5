import time

from PyQt6.QtCore import QThread, pyqtSignal


class FRIWorker(QThread):
    finished = pyqtSignal(list)

    def __init__(self, image, model_path: str, parent=None) -> None:
        super().__init__(parent)
        self.image = image
        self.model_path = model_path

    def run(self) -> None:
        # TODO: 模型推理

        # 示例代码
        time.sleep(6)

        self.finished.emit([["a", 1, 2, 3, 4, 5, 6]])

    def create_model(self):
        pass

    def load_model(self):
        # TODO: 加载模型
        pass

    def preprocess(self):
        pass

    def inference(self):
        pass

    def postprocess(self):
        pass
