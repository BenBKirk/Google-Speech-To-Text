import sys
import os
import tempfile
from PyQt5.QtCore import QThreadPool 
from PyQt5.QtWidgets import QApplication, QComboBox, QFileDialog, QHBoxLayout, QLineEdit, QProgressBar, QPushButton, QTableView, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QLabel
import json
from main import Transcriber
import time
import multi_threading


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
        self.job_list = []
    
    def set_up_ui(self):
        with open("lang_support.json") as f:
            self.lang_dict = json.load(f)
        lang_lb = QLabel("Language: ")
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(self.lang_dict.keys())
        if os.path.exists("settings.json"):
            with open("settings.json") as f:
                json_data = json.load(f)
                self.lang_combo.setCurrentText(json_data["language"])
        sub_layout = QHBoxLayout()
        sub_layout.addWidget(lang_lb)
        sub_layout.addWidget(self.lang_combo)
        self.indivdual_files_btn = QPushButton("Transcribe Indivdual Audio Files")
        self.folder_btn = QPushButton("Transcribe Folder (all files in folder)")
        self.job_view = QTableWidget()
        layout = QVBoxLayout()
        layout.addLayout(sub_layout)
        layout.addWidget(self.indivdual_files_btn)
        layout.addWidget(self.folder_btn)
        layout.addWidget(self.job_view)
        self.setLayout(layout)

        #connections
        self.indivdual_files_btn.clicked.connect(self.select_individual_files)
        self.folder_btn.clicked.connect(self.select_folder)
        self.lang_combo.currentTextChanged.connect(lambda: self.save_settings(self.lang_combo.currentText()))

        self.threadpool = QThreadPool()
        self.threadpool.setMaxThreadCount(3)
    
    def save_settings(self, current_text):
        if os.path.exists("settings.json"):
            os.remove("settings.json")
        the_dict = {"language":current_text}
        with open("settings.json", "w") as f:
            json.dump(the_dict,f)

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
            index_in_table = self.job_view.rowCount()
            worker = multi_threading.Worker(self.process_file,file,lang)
            worker.signals.progress.connect(self.update_job_list)
            # worker.signals.result.connect(self.nothing)
            # worker.signals.finished.connect(self.nothing)
            self.threadpool.start(worker)
            print(f"thread count is {self.threadpool.activeThreadCount()}")
            self.add_job(file)
            self.refresh_job_view()

    def add_job(self,file):
        job = {
            "full_file_path":file,
            "status":"In queue",
            "number_of_chunks":10,
            "current_chunk":0,
            "file_length":"...",
            "time_taken":"...",
            "errors":["..."],
        }
        self.job_list.append(job)
    
    def refresh_job_view(self):
        self.job_view.clear()
        self.job_view.setColumnCount(6)
        self.job_view.setCellWidget(0,0,QLabel("Name"))
        self.job_view.setCellWidget(0,1,QLabel("Loading Bar"))
        self.job_view.setCellWidget(0,2,QLabel("Status"))
        self.job_view.setCellWidget(0,3,QLabel("File Length"))
        self.job_view.setCellWidget(0,4,QLabel("Transcription Time"))
        self.job_view.setCellWidget(0,5,QLabel("Error Message"))
        self.job_view.setRowCount(len(self.job_list)+1)
        for i, job in enumerate(self.job_list,start=1):
            name = os.path.split(job["full_file_path"])[1]
            status = job["status"]
            progressbar = QProgressBar()
            progressbar.setMaximum(job["number_of_chunks"])
            progressbar.setValue(job["current_chunk"])
            file_length = job["file_length"]
            time_taken = job["time_taken"]
            errors = job['errors']
            errors = errors[::-1]
            errors = "\n".join(errors)
            self.job_view.setCellWidget(i,0,QLabel(name))
            self.job_view.setCellWidget(i,1,progressbar)
            self.job_view.setCellWidget(i,2,QLabel(status))
            self.job_view.setCellWidget(i,3,QLabel(file_length))
            self.job_view.setCellWidget(i,4,QLabel(str(time_taken)))
            self.job_view.setCellWidget(i,5,QLabel(str(errors)))
            self.job_view.resizeColumnsToContents()

    def update_job_list(self,update):
        for job in self.job_list:
            if job['full_file_path'] == update['full_file_path']:
                job['status'] = update['status']
                job['number_of_chunks'] = update['number_of_chunks']
                job['current_chunk'] = update['current_chunk']
                job['file_length'] = update['file_length']
                job['time_taken'] = update['time_taken']
                job['errors'].append(update['errors'])
        self.remove_duplicates_from_job_list()
        self.refresh_job_view()
    
    def remove_duplicates_from_job_list(self):
        seen_before = []
        for i, job in enumerate(self.job_list):
            if job['full_file_path'] not in seen_before:
                seen_before.append(job["full_file_path"])
            else:
                del self.job_list[i]
                
    def process_file(self, file, lang, progress_callback):
            start_time = time.perf_counter()
            update = {
                "full_file_path":file,
                "status":"Preparing files",
                "number_of_chunks":10,
                "current_chunk":0,
                "file_length":"...",
                "time_taken":"...",
                "errors":"...",
            }
            
            progress_callback.emit(update)
            with tempfile.TemporaryDirectory() as tempdir:
                ori_file_length_from_ffmpeg = self.transcriber.split_into_smaller_chunks(tempdir, file)
                if ori_file_length_from_ffmpeg is not None:
                    temp_file_names = os.listdir(tempdir)
                    full_paths = [os.path.join(tempdir,f) for f in temp_file_names]
                    dir_path, filename = os.path.split(file)
                    # clean up file name
                    for format in self.audio_formats:
                        if format in filename:
                            clean_filename = filename.replace(format,"")
                        else:
                            for format in self.video_formats:
                                if format in filename:
                                    clean_filename = filename.replace(format,"")                    

                    if os.path.exists(os.path.join(dir_path,clean_filename + ".txt")):
                        error_text = f"Cannot transcribe because a txt file with the same name already exists in the folder."
                        update = {
                            "full_file_path":file,
                            "status":"Failed",
                            "number_of_chunks":len(full_paths),
                            "current_chunk":0,
                            "file_length":str(ori_file_length_from_ffmpeg),
                            "time_taken":"...",
                            "errors":error_text,
                        }
                        progress_callback.emit(update)
                        return

                    txt_full_path = os.path.join(dir_path, clean_filename)

                    for i, temp_file in enumerate(full_paths,start=1):
                        flag = True
                        while flag: 
                            trans_results = self.transcriber.transcribe_temp_audio_file(temp_file,lang)
                            chunk_time = time.perf_counter()
                            time_taken = chunk_time - start_time
                            time_taken = time.strftime("%H:%M:%S", time.gmtime(time_taken))
                            status = "In progress"

                            if type(trans_results) == list:
                                if trans_results[0] == "NOT UNDERSTOOD":
                                    print(len(full_paths))
                                    print(i)
                                    error_text = f"Hmm... a whole section was not able to be transcribed at about {i * 3} minutes into the audio. Make sure the correct language is selected. {trans_results[1]}"
                                    flag = False # don't try again
                                    self.transcriber.write_to_txt(txt_full_path + ".txt","|-?-|")
                                    if len(full_paths) == 1:
                                        status = "Failed"
                                    if i+1 == len(full_paths):
                                        status = "finished"
                                elif trans_results[0] == "NO CONNECTION":
                                    error_text = f"There is a problem with the connection, maybe you lost internet connection? {trans_results[1]}"
                                elif trans_results[0] == "OTHER ERROR":
                                    error_text = f"There was an error: {trans_results[1]}"
                                update = {
                                    "full_file_path":file,
                                    "status":status,
                                    "number_of_chunks":len(full_paths),
                                    "current_chunk":i,
                                    "file_length":str(ori_file_length_from_ffmpeg),
                                    "time_taken":str(time_taken),
                                    "errors":error_text,
                                }
                                progress_callback.emit(update)
                            
                            else:
                                self.transcriber.write_to_txt(txt_full_path + ".txt",trans_results)
                                flag = False
                                if i == len(full_paths):
                                    status = "Finished"
                                update = {
                                    "full_file_path":file,
                                    "status":status,
                                    "number_of_chunks":len(full_paths),
                                    "current_chunk":i,
                                    "file_length":str(ori_file_length_from_ffmpeg),
                                    "time_taken":str(time_taken),
                                    "errors":"...",
                                }
                                progress_callback.emit(update)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())
