import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QStackedWidget, QFrame)
from PyQt5.QtCore import Qt
from modules.order import OrderModule
from modules.income import IncomeModule

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("数据分析工具集")
        self.resize(1200, 800)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QPushButton {
                background-color: #e0e0e0;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 8px;
                text-align: left;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
            QPushButton:checked {
                background-color: #c0c0c0;
                border-left: 3px solid #0078d7;
            }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # 左侧按钮区域
        left_panel = QFrame()
        left_panel.setFrameShape(QFrame.StyledPanel)
        left_panel.setStyleSheet("background-color: #ffffff; border-radius: 8px;")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setAlignment(Qt.AlignTop)
        left_layout.setSpacing(8)

        self.module_buttons = []
        self.stacked = QStackedWidget()

        # 注册模块
        self.modules = {
            "专业安全服务订单报表": OrderModule,
            "专业安全服务收入报表": IncomeModule
        }

        for idx, (name, module_class) in enumerate(self.modules.items()):
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, i=idx: self.switch_module(i))
            left_layout.addWidget(btn)
            self.module_buttons.append(btn)
            # 实例化模块并添加到 stacked
            widget = module_class()
            self.stacked.addWidget(widget)

        left_layout.addStretch()
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(self.stacked, 4)

        # 默认选中第一个
        if self.module_buttons:
            self.module_buttons[0].setChecked(True)
            self.switch_module(0)

    def switch_module(self, index):
        self.stacked.setCurrentIndex(index)
        for i, btn in enumerate(self.module_buttons):
            btn.setChecked(i == index)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())