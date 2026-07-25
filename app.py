import instaloader
import os
import glob

#text extraction
from moviepy import VideoFileClip
import speech_recognition as sr




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


    audio_file = latest_file.audio
    audio_file.write_audiofile("extracted_audio.wav")

    r = sr.Recognizer()

    with sr.AudioFile("extracted_audio.wav") as source:
        data = r.record(source)

    text = r.recognize_google(data)

    print("Text is =================")
    print(text)
    
    

if __name__ == "__main__":
    main()

