import sys
import os 
from PyQt5.QtWidgets import QApplication, QComboBox, QFileDialog, QHBoxLayout, QLineEdit, QPushButton, QTableView, QVBoxLayout, QWidget, QLabel
import json
# from PyQt5 import QtCore


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Speech to Text Program")
        self.setGeometry(500, 500,500,500)
        self.audio_formats = [".mp3",".wav", ".ogg",".wma",".flac",".mp4",".aac"]
        self.video_formats = [".mp4",".mov",".wmv",".avi"]
        # self.audio_formats = "*.mp3 *.wav *.ogg *.wma *.flac *.m4a *.mp4 *.aac"
        # self.video_formats = "*.mp4 *.mov *.wmv *.avi"
        self.set_up_ui()
        self.show()
    
    def set_up_ui(self):

        with open("lang_support.json") as f:
            lang_dict = json.load(f)

        lang_lb = QLabel("Language: ")
        lang_combo = QComboBox()
        lang_combo.addItems(lang_dict.keys())
        sub_layout = QHBoxLayout()
        sub_layout.addWidget(lang_lb)
        sub_layout.addWidget(lang_combo)

        self.indivdual_files_btn = QPushButton("Select Indivdual Audio Files")
        self.folder_btn = QPushButton("Select Folder (all files in folder)")

        job_view = QTableView()

        layout = QVBoxLayout()
        layout.addLayout(sub_layout)
        layout.addWidget(self.indivdual_files_btn)
        layout.addWidget(self.folder_btn)
        layout.addWidget(job_view)
        self.setLayout(layout)

        #connections
        self.indivdual_files_btn.clicked.connect(self.select_individual_files)
        self.folder_btn.clicked.connect(self.select_folder)

    def select_individual_files(self):
        # options = QFileDialog.Options()
        # options |= QFileDialog.DontUseNativeDialog
        audio_format_with_asterisk = " *" + " *".join(self.audio_formats)
        video_format_with_asterisk = " *" + " *".join(self.video_formats)
        print(audio_format_with_asterisk)
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Individual Audio Files (use ctrl or shift to select more than one file)",
            "",
            f"Audio Files ({audio_format_with_asterisk});;Video Files ({video_format_with_asterisk});",
            # options=options
            )

    def select_folder(self):
        path = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        if path:
            files = self.find_all_files_in_folder(path)
    
    def find_all_files_in_folder(self,path):
        list_of_files = []
        if os.path.exists(path):
            temp_list = os.listdir(path)
            for file in temp_list:
                file_type = os.path.splitext(file)[1]
                print(file_type)
                if file_type in self.audio_formats:
                    list_of_files.append(file)
                if file_type in self.video_formats:
                    list_of_files.append(file)
        return list_of_files

    



if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())
