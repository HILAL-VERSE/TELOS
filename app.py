import instaloader
import os
import glob
from dotenv import load_dotenv

load_dotenv() 

#text extraction
from moviepy import VideoFileClip
import speech_recognition as sr

from google import genai
client = genai.Client()

from colorama import init, Fore, Back, Style
init(autoreset=True)


L = instaloader.Instaloader(
    download_pictures=False,
    download_geotags=False,
    download_comments=False,
    save_metadata=False,
    post_metadata_txt_pattern=""
)

#Extracting Shortcode from reel's url
def extractShortcode(url):
    parts = url.split("/")
    return parts[4]


#deleting the audio file at last the program
def deleteAudioFile():
    file = glob.glob(r"C:\Users\CELLFI\OneDrive\Desktop\saved_reel_manage\*.wav")
    if not file:
        print(Fore.RED + "Not audio file founded")
    else:
        print("\n")
        print(Fore.GREEN+f"Found {len(file)} files")
        for file_path in file:
            os.remove(file_path)
            print(Fore.GREEN+f"\nDeleted audio file : {os.path.basename(file_path)}")


# main function
def main():
    #Login required
    username = "hilal.verse"
    L.load_session_from_file(username)
    print(Back.GREEN+L.test_login())

    #Invoking the function to get Shortcode:
    rUrl = input("Enter your url: ")
    my_shortcode = extractShortcode(rUrl)
    print(Fore.GREEN+my_shortcode)

    try:
        post = instaloader.Post.from_shortcode(L.context, my_shortcode)

        if post.is_video:
            L.download_post(post, target="Reels_Download")
            print(Fore.GREEN+"\nDownload succesful!")
        else:
            print(Fore.RED+"\nThe specified post is not a video, skipping download.")

    except Exception as e:
        print(Fore.RED+f"An error occurred: {e}")

    #folder path
    folder_path = r'C:\Users\CELLFI\OneDrive\Desktop\saved_reel_manage\Reels_Download\*.mp4'

    #getting all mp4 files
    mp4_files = glob.glob(folder_path)

    if mp4_files:
        latest_file = max(mp4_files, key=os.path.getctime)
        print(f"\nThe latest MP4 file is: {latest_file}")
    else:
        print(Fore.RED+"No MP4 files found in the directory.")

    video = VideoFileClip(latest_file)
    audio_file = video.audio
    audio_file.write_audiofile("extracted_audio.wav")

    r = sr.Recognizer()

    with sr.AudioFile("extracted_audio.wav") as source:
        data = r.record(source)

    text = r.recognize_google(data)

    print(Back.WHITE+Fore.GREEN+"\n EXTRACTED TEXT IS \n")
    print(text)
    
    prompt = f"""
    Act as a Forensic Content Analyst. I will provide you with a transcript from a saved video. Your goal is to extract every specific detail to fulfill a high-precision knowledge graph.

    Analyze the transcript and provide the output in the following format:

    1. **The "Why":** In one sentence, identify the specific utility or value proposition of this video (e.g., "A tutorial on specific FFmpeg commands for audio merging").
    2. **Entity Manifest:** List every specific Tool, Person, Brand, Library, or Location mentioned.
    3. **Chronological Breakdown:** A step-by-step list of every action or point made, in order.
    4. **Implicit Context:** Based on the tone and content, what was the user likely trying to solve or learn by saving this?
    5. **Data Points:** Extract any specific numbers, prices, dates, or code-like snippets mentioned in the audio.

    Transcript:{text}
        """

    interaction = client.interactions.create(
    model="gemini-3.6-flash",
    input=prompt
    )
    print("\n RESULT \n ")
    print(Back.WHITE+Fore.GREEN+interaction.output_text)

    #Invoking the function to delete the extracted audio file and delete the downloaded reel file
    deleteVideoFile()
    deleteAudioFile()
if __name__ == "__main__":
    main()

