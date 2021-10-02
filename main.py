import os
import pathlib
import subprocess as sp
import tempfile
import speech_recognition as sr
import time
import re 

def get_audio_files():
    "Returns a list of all audio files in current working directory"
    files_in_cwd = os.listdir(os.getcwd())
    return [f for f in files_in_cwd if pathlib.Path(f).suffix.lower() in [".mp3",".wav",".ogg",".mp4",".m4a"]]

def split_into_smaller_chunks(tempdir, audio_file):
    "Split up audio using ffmpeg and save to temp directory"
    output_file = os.path.join(tempdir,audio_file.split(".")[0])
    # process = sp.Popen(f'ffmpeg -i "{audio_file}" -f segment -segment_time 150 "{output_file}"%03d.wav"',stdout=sp.PIPE, stderr=sp.PIPE)
    process = sp.Popen(
            [
            "ffmpeg","-i",
            audio_file,
            "-f", "segment", "-segment_time", "150",
            f"{output_file}%03d.wav"
            ],
            stdout=sp.PIPE,
            stderr=sp.PIPE
            )

    try:
        stdout,stderr = process.communicate()
        pattern = re.compile(r"(?<=Duration:\s)\d+:\d+:\d+")
        length = re.match(pattern, stdout.decode())
        if length is None:
            length = re.search(pattern, stderr.decode())
        return length.group(0)
    except sp.TimeoutExpired as e:
        print(f"Timed out while tring to split up this file:{audio_file}")
        print(e)
        return None

def transcribe_temp_audio_file(file):
    "transcribe audio clip using google dev api"
    with sr.AudioFile(file) as source:
        r = sr.Recognizer()
        try:
            data = r.record(source)
            response = r.recognize_google(data,language="id-ID")
        except sr.UnknownValueError as e:
            print(f"UNKNOWN VALUE ERROR {e}")
            return None
        except sr.RequestError as e:
            print(f"REQUEST ERROR {e}")
            return None
        except Exception as e:
            print(f"ERROR FROM GOOGLE {e}")
            # answer = input('DO YOU WANT TO TRY AGAIN (y) or MOVE ON TO ANOTHER PART OF THE AUDIO (n)?')
            # if answer.lower().strip() == 'y':
            #     transcribe_temp_audio_file(file)
            # # elif answer.lower().strip() == 'n':
            # else:
            return None
        return response

def write_to_txt(txt_file_name,text):
    "append to txt file"
    with open(txt_file_name,"a",encoding="utf-8") as txt_file:
        txt_file.write("\n" + text)

def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):# 
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    # Print New Line on Complete
    if iteration == total: 
        pass
        # print("                                                         ")

def print_files_found(audio_files):
    "Prints audio file names to console"
    print(f"{len(audio_files)} FILES FOUND:")

    for i, f in enumerate(audio_files):
        print( f"{i+1}. " + f)
    print('-'*50)

def main():
    "main function that calls other functions"
    start_time = time.perf_counter()
    audio_files = get_audio_files()
    print_files_found(audio_files)

    for audio_file in audio_files:
        start_time_for_file =time.perf_counter()
        with tempfile.TemporaryDirectory() as tempdir:
            ori_length = split_into_smaller_chunks(tempdir,audio_file)
            if ori_length != None:
                temp_file_names = os.listdir(tempdir)
                full_paths = [os.path.join(tempdir,f) for f in temp_file_names]
                txt_file_name = audio_file.split(".")[0] + ".txt"
                printProgressBar(0,len(full_paths),prefix="TRANSCRIBING",suffix=audio_file,length=50,printEnd="\r")
                for i, file in enumerate(full_paths):
                    trans_results = transcribe_temp_audio_file(file)
                    while trans_results == None:
                        print("\a") # make alert noise
                        print("CHECK YOUR INTERNET CONNECTION")
                        answer = input('DO YOU WANT TO TRY AGAIN (y) or MOVE ON TO ANOTHER PART OF THE AUDIO (n)?')
                        if answer.lower().strip() == 'y' or answer.lower().strip() == 'yes':
                            trans_results = transcribe_temp_audio_file(file)
                        else:
                            trans_results = " |--THIS PART FAILED TO TRANSCRIBE (MAY HAVE LOST INTERNET)--| "
                            break
                    printProgressBar(i+1,len(full_paths),prefix="TRANSCRIBING",suffix=audio_file,length=50,printEnd = "\r")
                    write_to_txt(txt_file_name,trans_results)
                end_time_for_file = time.perf_counter()
                time_taken_for_file = time.gmtime(end_time_for_file-start_time_for_file)
                print(f'DONE | ORIGINAL FILE LENGTH {ori_length} | TIME TAKEN TO TRANSCRIBE {time.strftime("%H:%M:%S",time_taken_for_file)} | FILE NAME {audio_file}')
            else:
                print(f' FAILED | FILE NAME "{audio_file}"')

    end_time = time.perf_counter()
    time_taken = time.gmtime(end_time - start_time)
    print("Total time to complete all files: " + time.strftime("%H:%M:%S",time_taken))
    print("\a") # make alert noise


if __name__ == "__main__":
    main()
