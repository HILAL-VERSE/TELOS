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


L = instaloader.Instaloader(
    download_pictures=False,
    download_geotags=False,
    download_comments=False,
    save_metadata=False,
    post_metadata_txt_pattern=""
)


def extractShortcode(url):
    parts = url.split("/")
    return parts[4]



def main():
    #Login required
    username = "hilal.verse"
    L.load_session_from_file(username)
    print(L.test_login())

    #Getting Shortcode:
    rUrl = input("Enter your url: ")
    my_shortcode = extractShortcode(rUrl)
    print(my_shortcode)

    try:
        post = instaloader.Post.from_shortcode(L.context, my_shortcode)

        if post.is_video:
            L.download_post(post, target="Reels_Download")
            print("Download succesful!")
        else:
            print("The specified post is not a video, skipping download.")

    except Exception as e:
        print(f"An error occurred: {e}")

    #folder path
    folder_path = r'C:\Users\CELLFI\OneDrive\Desktop\saved_reel_manage\Reels_Download/*.mp4'

    #getting all mp4 files
    mp4_files = glob.glob(folder_path)

    if mp4_files:
        latest_file = max(mp4_files, key=os.path.getctime)
        print(f"The latest MP$ file is: {latest_file}")
    else:
        print("No MP4 files found in the directory.")

    video = VideoFileClip(latest_file)
    audio_file = video.audio
    audio_file.write_audiofile("extracted_audio.wav")

    r = sr.Recognizer()

    with sr.AudioFile("extracted_audio.wav") as source:
        data = r.record(source)

    text = r.recognize_google(data)

    print("Text is =================")
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
    print("====================")
    print(interaction.output_text)

if __name__ == "__main__":
    main()

