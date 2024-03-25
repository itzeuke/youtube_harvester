import customtkinter as ctk
import tkinter as tk
from PIL import Image, ImageTk
import os
from pytube import YouTube as yt
from pytube import Playlist as yt_pl
from io import BytesIO
import requests
import threading
from moviepy.editor import VideoFileClip, AudioFileClip
import shutil


STORE_PATH = os.path.expanduser("~") + r"\YT-Harvester"
basedir = os.path.dirname(__file__)

# classes
class queueEntry:
    def __init__(self, url, type, quality, item):
        self.url = url
        self.status = tk.StringVar(value="waiting...")
        self.type = type
        self.quality = quality
        self.item = item

# download_video_queue
def queue_video_status(title, quality, file_type="", image_url="", queue_id=1):
    title = title[0:20]  # + " (" + file_type + ")"

    print(queue_list)
    status = queue_list[queue_id].status

    video_info_frame = ctk.CTkFrame(queue_frame, fg_color=("#ffffff", "#232323"))
    video_info_title = ctk.CTkLabel(video_info_frame, text=title, font=("Bahnschrift Light", 15), pady=5)
    if file_type == "MP4":
        video_info_quality = ctk.CTkLabel(video_info_frame, text=f"Quality: ({file_type}) {quality}",
                                        font=("Bahnschrift Light", 12))
    else:
        video_info_quality = ctk.CTkLabel(video_info_frame, text=f"Quality: ({file_type})",
                                          font=("Bahnschrift Light", 12))

    video_info_status_frame = ctk.CTkFrame(video_info_frame, fg_color=("#ffffff", "#232323"))
    video_info_status_title = ctk.CTkLabel(video_info_status_frame, text="status: ", font=("Bahnschrift Light", 12))
    video_info_status_value = ctk.CTkLabel(video_info_status_frame, textvariable=status, font=("Bahnschrift Light", 12))
    if not image_url:
        if file_type == "MP3":
            video_info_img_init = ctk.CTkImage(light_image=Image.open("mp3_img.jpg"), size=(60, 50))
        else:
            video_info_img_init = ctk.CTkImage(light_image=Image.open("mp4_img.png"), size=(60, 50))
    else:
        fetched_thumbnail = requests.get(image_url, verify=False)
        image = Image.open(BytesIO(fetched_thumbnail.content))
        video_info_img_init = ctk.CTkImage(light_image=image, size=(65, 50))

    video_info_img = ctk.CTkLabel(video_info_frame, image=video_info_img_init, text="")
    video_info_stop = ctk.CTkButton(video_info_frame, text="X", command=lambda: stop_queue_entry(queue_id), width=10,
                                    height=10)

    video_info_frame.pack(fill="x", pady=5)
    video_info_title.grid(row=1, column=1, sticky="w")
    video_info_quality.grid(row=2, column=1, sticky="w")
    video_info_status_frame.grid(row=3, column=1, sticky="w")
    video_info_img.grid(row=0, column=0, rowspan=4, sticky="nswe", padx=(0, 10))
    video_info_stop.grid(row=1, column=2)

    video_info_status_title.grid(row=0, column=0)
    video_info_status_value.grid(row=0, column=1)


    video_info_status_frame.columnconfigure(0, weight=0)
    video_info_status_frame.columnconfigure(0, weight=1)

    video_info_frame.columnconfigure(0, weight=4)
    video_info_frame.columnconfigure(1, weight=8)
    video_info_frame.columnconfigure(2, weight=2)
    # use buttons which download IDs to stop download

def stop_queue_entry(queue_id):
    if queue_list[queue_id].status.get("done"):
        queue_list[queue_id].status.set("stopped")

def get_mp4():
    video_url = vid_url.get()
    #if not video_url:  # debugging
    #    video_url = "https://youtu.be/NcBjx_eyvxc?si=zIvl2R5aJn3zcEUh"
    #download_resource(video_url)
    download_resource_thread = threading.Thread(target=download_resource_container, args=(video_url, "MP4",), daemon=True)
    download_resource_thread.start()

def get_mp3():
    video_url = vid_url.get()
    #if not video_url:  # debugging
    #    video_url = "https://youtu.be/wbMJ3wQqPwI?si=m9aeRDyUyD5ETyzP"
    download_resource_thread = threading.Thread(target=download_resource_container, args=(video_url, "MP3",), daemon=True)
    download_resource_thread.start()


def download_resource_container(video_url, file_type):
    error_display.set("") # clear error display

    # get all urls (if playlist) and put into array
    youtube_urls = get_video_urls(video_url)
    if youtube_urls:

        # do for all urls in array
        for youtube_url in youtube_urls:
            yt_data = get_resource(youtube_url)  # get the video

            if yt_data:

                video_quality = get_right_video_resolution(yt_data)
                if video_quality:
                    # add to download queue
                    new_queue_entry = queueEntry(url=video_url, type=file_type, quality=video_quality, item=yt_data)
                    queue_list.append(new_queue_entry)
                    queue_entry_id = len(queue_list) - 1

                    # add to queue
                    queue_video_status(title=yt_data.title,
                                        quality=video_quality,
                                        file_type=file_type,
                                        image_url=yt_data.thumbnail_url,
                                        queue_id=queue_entry_id)

                    download_video_thread = threading.Thread(target=download_video, args=(queue_entry_id,), daemon=True)
                    download_video_thread.start()



def download_video(queue_id):
    if queue_list[queue_id].status.get() == "stopped":
        return
    queue_list[queue_id].status.set("downloading...")
    queue_entry = queue_list[queue_id]

    item = queue_entry.item
    quality = queue_entry.quality
    streams = item.streams

    audio_stream = streams.get_audio_only()

    if queue_entry.type == "MP4":
        progressive_streams = streams.filter(progressive=True).filter(res=quality)
        if progressive_streams:
            if queue_list[queue_id].status.get() == "stopped":
                return

            progressive_streams[0].download(filename=validate_file_name(progressive_streams[0].title + ".mp4"), output_path=STORE_PATH + "\\MP4")
            queue_list[queue_id].status.set("done")
        else:
            video_stream = item.streams.filter(adaptive="True").filter(res=quality)[0]


            if not os.path.exists(STORE_PATH + r"\.tmp"):
                os.makedirs(STORE_PATH + r"\.tmp")
                os.system(f'attrib +h "{STORE_PATH + r"\.tmp"}"')

            audio_stream.download(filename=f"vid_{queue_id}.mp3", output_path=STORE_PATH + r"\.tmp")
            video_stream.download(filename=f"vid_{queue_id}.mp4", output_path=STORE_PATH + r"\.tmp")


            finished_download(video_stream, STORE_PATH + f"\\.tmp\\vid_{queue_id}.mp4", queue_id)

    elif queue_entry.type == "MP3":

        if queue_list[queue_id].status.get() == "stopped":
            return

        audio_stream.download(filename=validate_file_name(audio_stream.title + ".mp3"), output_path=STORE_PATH + "\\MP3")
        queue_list[queue_id].status.set("done")




def get_right_video_resolution(item):
    try:
        video_quality = vid_quality_var.get()

        # get selected video quality
        if video_quality == "specific":
            video_quality = vid_quality_specific_var.get()
        else:
            video_quality = video_quality_translator(video_quality)

        # check if resolution is available:
        available_streams = get_available_resolutions(item)

        if video_quality in available_streams:
            return video_quality
        else:
            return available_streams[-1]
    except Exception as error:
        error_display.set("Error: " + str(error))
        return False

def get_available_resolutions(item):
    available_streams = []
    for streams in item.streams.filter(adaptive="True"):
        if streams.resolution is not None:
            resolution = int(streams.resolution[0:-1])
            if resolution not in available_streams:
                available_streams.append(resolution)
    available_streams.sort()
    index = 0
    while index < len(available_streams):
        available_streams[index] = str(available_streams[index]) + "p"
        index += 1
    return available_streams

# def get_right_video_stream(item):
#     video_quality = get_right_video_resolution(item)
#
#     available_streams = get_available_resolutions(item)
#
#     if video_quality in ["144p", "240p", "360p", "480p", "720p"]:
#         return [item.streams.get_by_resolution(video_quality), video_quality]
#
#     elif video_quality in available_streams:
#         return [item.streams.get_by_resolution(video_quality), video_quality]
#
#     else: # best video quality # Needs to be an adaptive stream. Connect audio and video
#         return [item.streams.get_by_resolution(available_streams[-1]), available_streams[-1]]


def video_quality_translator(quality):
    if quality == "good":
        return "720p"
    elif quality == "low":
        return "360p"
    else:
        return "best"


def get_resource(url):
    try:
        yt_video = yt(url)
        return yt_video
    except Exception as error:
        error_display.set("Error: " + str(error))
        return False

def finished_download(stream, path, queue_id):
    extension = path[-4:None]
    if extension == ".mp4":
        merge_video(stream, path, queue_id)
        queue_list[queue_id].status.set("done")
def merge_video(stream, path, queue_id):
    path_without_extension = path[0:-4]
    input_video_path = path_without_extension + ".mp4"
    input_audio_path = path_without_extension + ".mp3"
    output_path = STORE_PATH + r"\MP3\test.mp4"

    if queue_list[queue_id].status.get() == "stopped":
        os.remove(input_video_path)
        os.remove(input_audio_path)
        return

    queue_list[queue_id].status.set("converting...")

    print(path_without_extension)
    print(input_video_path)
    print(input_audio_path)
    input_video = VideoFileClip(input_video_path)
    input_audio = AudioFileClip(input_audio_path)

    final_video = input_video.set_audio(input_audio)

    file_title = validate_file_name(stream.title)

    if not os.path.exists(STORE_PATH + "\\MP4"):
        os.makedirs(STORE_PATH + "\\MP4")
    final_video.write_videofile(STORE_PATH + "\\MP4\\" + file_title + ".mp4")
    print(input_video, input_audio)
    os.remove(input_video_path)
    os.remove(input_audio_path)



def validate_file_name(name):
    allowed_name = ""
    for symbol in name.lower():
        if symbol in "abcdefghijklmnopqrstufvxyz1234567890_-.":
            allowed_name += symbol
    if not allowed_name:
        allowed_name += "download"
    print(allowed_name)
    return allowed_name
def open_files():
    if not os.path.exists(STORE_PATH):
        os.makedirs(STORE_PATH)
    os.startfile(STORE_PATH)


def get_video_urls(url):
    try:
        fetched_playlist = yt_pl(url)
        print(fetched_playlist)
        return fetched_playlist
    except:
        try:
            fetched_video = yt(url)
            return [url]
        except Exception as error:
            error_display.set("Error: Could not find resource: " + url)
            return False

# startup #
if os.path.exists(STORE_PATH + "\\.tmp"):
    shutil.rmtree(STORE_PATH + "\\.tmp\\")

# window settings
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme(os.path.join(basedir, "./red_theme.json"))

# create main window
window = ctk.CTk()
window.geometry("1200x700")
window.title("Youtube Harvester")
window.minsize(1200, 600)
window.iconbitmap(os.path.join(basedir, "logo.ico"))

# global vars
vid_quality_var = tk.StringVar(value="good")
vid_quality_specific_var = tk.StringVar(value="720p")
vid_url = tk.StringVar()
queue_list = []
error_display = tk.StringVar()

# window grid settings
window.columnconfigure(0, weight=2)
window.columnconfigure(1, weight=5)
window.rowconfigure(0, weight=1)

# create frames
queue_frame = ctk.CTkScrollableFrame(window, fg_color=("#ffffff", "#1f1f1f"))
enter_media_frame = ctk.CTkFrame(window, fg_color=("#ffffff", "#242424"))
get_media_frame_container = ctk.CTkFrame(enter_media_frame, fg_color=("#ffffff", "#242424"))
get_media_frame = ctk.CTkFrame(get_media_frame_container)
vid_quality_selection_frame = ctk.CTkFrame(enter_media_frame, fg_color=("#ffffff", "#242424"))
specific_vid_quality_selection_frame = ctk.CTkFrame(vid_quality_selection_frame, fg_color=("#ffffff", "#242424"))

# frames grid settings
enter_media_frame.columnconfigure(0, weight=4) # title
enter_media_frame.columnconfigure(1, weight=4) # url input
enter_media_frame.columnconfigure(2, weight=4) # quality selection

enter_media_frame.rowconfigure(0, weight=1)
enter_media_frame.rowconfigure(1, weight=1)
enter_media_frame.rowconfigure(2, weight=1)

get_media_frame.columnconfigure(0, weight=1)
get_media_frame.columnconfigure(1, weight=1)
get_media_frame.rowconfigure(0, weight=1)
get_media_frame.rowconfigure(0, weight=1)

get_media_frame_container.columnconfigure(0, weight=2)
get_media_frame_container.columnconfigure(1, weight=1)
get_media_frame_container.rowconfigure(0, weight=1)
get_media_frame_container.rowconfigure(1, weight=1)



vid_quality_selection_frame.columnconfigure(0, weight=1)
vid_quality_selection_frame.columnconfigure(1, weight=1)
vid_quality_selection_frame.columnconfigure(2, weight=1)
vid_quality_selection_frame.columnconfigure(3, weight=1)
vid_quality_selection_frame.rowconfigure(0, weight=1)
vid_quality_selection_frame.rowconfigure(1, weight=1)

specific_vid_quality_selection_frame.columnconfigure(0, weight=1)
specific_vid_quality_selection_frame.columnconfigure(1, weight=1)
specific_vid_quality_selection_frame.rowconfigure(0, weight=1)

### create widgets ###
#  frame titles
queue_title = ctk.CTkLabel(queue_frame, text="Queue", bg_color="#fa4b4b", font=("Bahnschrift Light", 16), pady=10)
download_frame_title = ctk.CTkLabel(enter_media_frame, text="YouTube-Harvester", font=("Bahnschrift Light", 40))

quality_selection_title = ctk.CTkLabel(vid_quality_selection_frame, text="Quality:", font=("Bahnschrift Light", 16),
                                       pady=30)
error_lable = ctk.CTkLabel(get_media_frame_container, textvariable=error_display, font=("Bahnschrift Light", 12), pady=0, fg_color=("#ffffff", "#242424"))

version_label = ctk.CTkLabel(enter_media_frame, text="alpha v1.0.0", font=("Bahnschrift Light", 12))

#  entry & checkbox
input_link = ctk.CTkEntry(get_media_frame_container, width=400, textvariable=vid_url)

# quality selection
quality_radio_button1 = ctk.CTkRadioButton(vid_quality_selection_frame, text="low", variable=vid_quality_var,
                                           value="low")
quality_radio_button2 = ctk.CTkRadioButton(vid_quality_selection_frame, text="good", variable=vid_quality_var,
                                           value="good")
quality_radio_button3 = ctk.CTkRadioButton(vid_quality_selection_frame, text="best", variable=vid_quality_var,
                                           value="best")
quality_radio_button4 = ctk.CTkRadioButton(specific_vid_quality_selection_frame, text="specific (MP4)",
                                           variable=vid_quality_var, value="specific")
quality_specific_selection = ctk.CTkOptionMenu(specific_vid_quality_selection_frame,
                                               values=["144p", "240p", "360p", "480p", "720p", "1080p", "1440p",
                                                       "2160p"], variable=vid_quality_specific_var)

# buttons
get_mp4_button = ctk.CTkButton(get_media_frame, text="MP4", command=get_mp4)
get_mp3_button = ctk.CTkButton(get_media_frame, text="MP3", command=get_mp3)

open_files_button = ctk.CTkButton(queue_frame, text="Open Files", command=open_files)

### add to window ###

# queue frame
queue_frame.grid(row=0, column=0, sticky="nsew")
enter_media_frame.grid(row=0, column=1, sticky="nsew")
open_files_button.pack(fill="x")

# media input frame

get_media_frame_container.grid(row=1, column=0, columnspan=4)
get_media_frame.grid(row=0, column=1, sticky="w")
input_link.grid(row=0, column=0, sticky="we")
error_lable.grid(row=1, column=0, columnspan=2, pady=(5, 0))

vid_quality_selection_frame.grid(row=2, column=0, columnspan=4)
specific_vid_quality_selection_frame.grid(row=1, column=4)

quality_selection_title.grid(row=0, column=2)

download_frame_title.grid(row=0, column=0, columnspan=4, sticky="nsew")

get_mp3_button.grid(row=0, column=0, padx=10)
get_mp4_button.grid(row=0, column=1)

version_label.place(relx=0.98, rely=0.97, anchor="e")

#
# #  checkboxes
quality_radio_button1.grid(row=1, column=0)
quality_radio_button2.grid(row=1, column=1)
quality_radio_button3.grid(row=1, column=2)
quality_radio_button4.grid(row=0, column=1)
quality_specific_selection.grid(row=0, column=2, padx=(10, 0))

window.mainloop()
