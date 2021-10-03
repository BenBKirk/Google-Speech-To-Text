import sys
import os
import tempfile
from PyQt5.QtCore import QThreadPool 
from PyQt5.QtWidgets import QApplication, QComboBox, QFileDialog, QHBoxLayout, QLineEdit, QProgressBar, QPushButton, QTableView, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QLabel
import json
from main import Transcriber
import time
import multi_threading
# from PyQt5 import QtCore


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Speech to Text Program")
        self.setGeometry(500, 500,1000,500)
        self.audio_formats = [".mp3",".wav", ".ogg",".wma",".flac",".mp4",".aac",".m4a"]
        self.video_formats = [".mp4",".mov",".wmv",".avi"]
        self.set_up_ui()
        self.show()
        self.transcriber = Transcriber()
    
    def set_up_ui(self):

        with open("lang_support.json") as f:
            self.lang_dict = json.load(f)

        lang_lb = QLabel("Language: ")
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(self.lang_dict.keys())
        sub_layout = QHBoxLayout()
        sub_layout.addWidget(lang_lb)
        sub_layout.addWidget(self.lang_combo)

        self.indivdual_files_btn = QPushButton("Transcribe Indivdual Audio Files")
        self.folder_btn = QPushButton("Transcribe Folder (all files in folder)")

        self.job_view = QTableWidget()
        self.job_view.setColumnCount(5)
        self.job_view.setRowCount(1)
        self.job_view.setCellWidget(0,0,QLabel("Name"))
        self.job_view.setCellWidget(0,1,QLabel("Loading Bar"))
        self.job_view.setCellWidget(0,2,QLabel("Status"))
        self.job_view.setCellWidget(0,3,QLabel("Length"))
        self.job_view.setCellWidget(0,4,QLabel("Transcription Time"))



        layout = QVBoxLayout()
        layout.addLayout(sub_layout)
        layout.addWidget(self.indivdual_files_btn)
        layout.addWidget(self.folder_btn)
        layout.addWidget(self.job_view)
        self.setLayout(layout)

        #connections
        self.indivdual_files_btn.clicked.connect(self.select_individual_files)
        self.folder_btn.clicked.connect(self.select_folder)

        self.threadpool = QThreadPool()

    def select_individual_files(self):
        # options = QFileDialog.Options()
        # options |= QFileDialog.DontUseNativeDialog
        audio_format_with_asterisk = " *" + " *".join(self.audio_formats)
        video_format_with_asterisk = " *" + " *".join(self.video_formats)
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Individual Audio Files (use ctrl or shift to select more than one file)",
            "",
            f"Audio Files ({audio_format_with_asterisk});;Video Files ({video_format_with_asterisk});",
            # options=options
            )
        if files:
            self.start_threading(files)

    def select_folder(self):
        path = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        if path:
            files = self.find_all_files_in_folder(path)
            if files != []:
                self.start_threading(files)
    
    def find_all_files_in_folder(self,path):
        list_of_files = []
        if os.path.exists(path):
            temp_list = os.listdir(path)
            for file in temp_list:
                full_path = os.path.join(path,file)
                file_type = os.path.splitext(file)[1]
                if file_type in self.audio_formats:
                    list_of_files.append(full_path)
                elif file_type in self.video_formats:
                    list_of_files.append(full_path)
        print(list_of_files)
        return list_of_files

    def start_threading(self,files):
        for file in files:
            lang = self.lang_dict[self.lang_combo.currentText()]
            worker = multi_threading.Worker(self.process_file,file,lang,self.job_view.rowCount())
            worker.signals.progress.connect(self.update_table_view)
            # worker.signals.result.connect(self.nothing)
            # worker.signals.finished.connect(self.nothing)
            self.threadpool.start(worker)
            print(f"thread count is {self.threadpool.activeThreadCount()}")

            self.job_view.setRowCount(self.job_view.rowCount() + 1)


                
    def process_file(self, file, lang, index_in_table, progress_callback):
            start_time = time.perf_counter()
            
            progress_callback.emit({"filename":file,"file_length":"","chunks":10,"current_chunk":0,"index_in_table":index_in_table ,"time_taken":0})
            with tempfile.TemporaryDirectory() as tempdir:
                ori_file_length_from_ffmpeg = self.transcriber.split_into_smaller_chunks(tempdir, file)
                if ori_file_length_from_ffmpeg is not None:
                    temp_file_names = os.listdir(tempdir)
                    full_paths = [os.path.join(tempdir,f) for f in temp_file_names]
                    dir_path, filename = os.path.split(file)

                    # clean up file name
                    for format in self.audio_formats:
                        if format in filename:
                            print(format)
                            clean_filename = filename.replace(format,"")
                            print(filename)
                        else:
                            for format in self.video_formats:
                                if format in filename:
                                    clean_filename = filename.replace(format,"")                    

                    if os.path.exists(file):
                        clean_filename = clean_filename + " (new)"

                    txt_full_path = os.path.join(dir_path, clean_filename)

                    for i, temp_file in enumerate(full_paths):
                        trans_results = self.transcriber.transcribe_temp_audio_file(temp_file,lang)
                        chunk_time = time.perf_counter()
                        time_taken = chunk_time - start_time
                        the_dict = {"filename":file,"file_length":ori_file_length_from_ffmpeg,"chunks":len(full_paths),"current_chunk":i+1,"index_in_table":index_in_table,"time_taken":time_taken}
                        progress_callback.emit(the_dict)
                        if trans_results != None:
                            self.transcriber.write_to_txt(txt_full_path + ".txt",trans_results)
                        else:
                            self.transcriber.write_to_txt(txt_full_path + ".txt"," ? ")



    
    def update_table_view(self,update):
        filename = os.path.split(update["filename"])[1]
        file_length = update["file_length"]
        chunks = update["chunks"]
        current_chunk = update["current_chunk"]
        index_in_job_view = update["index_in_table"]
        time_taken = update["time_taken"]

        progressbar = QProgressBar()
        progressbar.setMaximum(chunks)
        progressbar.setValue(current_chunk)

        if current_chunk == chunks:
            status = "DONE"
        else:
            status = "IN PROGRESS"
        
        self.job_view.setCellWidget(index_in_job_view,0,QLabel(filename))
        self.job_view.setCellWidget(index_in_job_view,1,progressbar)
        self.job_view.setCellWidget(index_in_job_view,2,QLabel(status))
        self.job_view.setCellWidget(index_in_job_view,3,QLabel(file_length))
        self.job_view.setCellWidget(index_in_job_view,4,QLabel(str(time_taken)))
        

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())
