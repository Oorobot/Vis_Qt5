import time

from PyQt6.QtCore import QThread, pyqtSignal


class PJIWorker(QThread):
    finished = pyqtSignal(str)

    def __init__(self, image, body_part: str, body_direction=None, parent=None) -> None:
        super().__init__(parent)
        self.image = image
        if body_part == "knee":
            self.model_path = "./asset/model/PJI_knee_1.pth"
        if body_part == "hip":
            self.model_path = "./asset/model/PJI_hip_1.pth"

    def run(self) -> None:
        # TODO: 模型推理

        # 示例代码
        time.sleep(6)

        self.finished.emit("感染")

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
