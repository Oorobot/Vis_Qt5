import time

from PyQt6.QtCore import QThread, pyqtSignal


class FRIWorker(QThread):
    finished = pyqtSignal(list)

    def __init__(self, image, parent=None) -> None:
        super().__init__(parent)
        self.image = image
        self.model_path_det = "asset/model/FRI_det.pth"
        self.model_path_cls = "asset/model/FRI_cls.pth"

    def run(self) -> None:
        # TODO: 模型推理

        # 示例代码
        time.sleep(6)

        self.finished.emit(
            [
                {"class_name": "infected", "bbox": [144, 271, 150, 219, 316, 199]},
                {"class_name": "bladder", "bbox": [228, 251, 234, 287, 304, 243]},
            ]
        )

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
