import sys
import os 
from PyQt5.QtWidgets import QApplication, QComboBox, QHBoxLayout, QPushButton, QTableView, QVBoxLayout, QWidget, QLabel
# from PyQt5 import QtCore

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Speech to Text Program")
        self.setGeometry(500, 500,500,500)
        self.set_up_ui()
        self.show()
    
    def set_up_ui(self):
        lang_dict = {
            "US English":"en-US",
            "UK English":"en-GB",
            "Indonesian":"id-ID",
            "Javanese":"jv-ID"
            }
        lang_lb = QLabel("Language:")
        lang_combo = QComboBox()
        lang_combo.addItems(lang_dict.keys())
        sub_layout = QHBoxLayout()
        sub_layout.addWidget(lang_lb)
        sub_layout.addWidget(lang_combo)

        single_file_btn = QPushButton("Select Single Audio File")
        folder_btn = QPushButton("Select all Audio Files From Folder")

        job_view = QTableView()

        layout = QVBoxLayout()
        layout.addLayout(sub_layout)
        # layout.addChildLayout(sub_layout)
        layout.addWidget(single_file_btn)
        layout.addWidget(folder_btn)
        layout.addWidget(job_view)
        self.setLayout(layout)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())
