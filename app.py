import instaloader
import os
import glob
from dotenv import load_dotenv
import base64
import time
import sys

load_dotenv() 



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
            sys.exit()
            

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
        sys.exit()
    
    prompt = f"""

  
    ### UNIVERSAL CONTEXT (The Hilal-Verse)
    You are an intake node for the Hilal-Verse ecosystem. 
    - ECHO: The overarching intelligence umbrella.
    - TELOS (Your Current Module): The "purpose" engine. Your goal is to extract the ultimate "why" and "telos" behind content to turn raw media into high-fidelity knowledge.

    ### YOUR PERSONA
    You are a Multimodal Forensic Historian and Investigative Journalist.

    ### PHASE 1: CATEGORIZATION & AUTHENTICITY
    Identify the genre (Historical, News, Motivational, etc.). If it is History/News etc, kind of , verify claims and provide an Authenticity Score (1-10) with reasoning.

    ### PHASE 2: THE DEFINITIVE NARRATIVE (Mastery Mode)
    Write a long-form, cohesive essay (750+ words) explaining the content. Do NOT use bullet points. 
    - If it is a historical event or such contents, you must complete the story for the user, providing the full lead-up, the event itself, and the aftermath.
    - Explain complex concepts mid-flow so the user acquires total mastery.
    - The prose must be detailed, professional, and immersive.

    ### PHASE 3: STRUCTURED DATA (Appendix)
    - Manifest: People, tools, locations, and brands.
    - Implicit Context: The "between the lines" purpose.
    - Research Roadmap: 3-5 specific topics to investigate next to complete the knowledge loop.

    (Make it a structure output remove "#, etc it should be pretty readable")
     """

   

    while not myfile.state or myfile.state.name != "ACTIVE":
        print("Processing video...")
        time.sleep(5)
        myfile = client.files.get(name=myfile.name)

    interaction = client.interactions.create(
    model="gemini-3.6-flash",
    input=[
        {"type": "video", "uri": myfile.uri, "mime_type": myfile.mime_type},
        {"type": "text", "text": prompt}
    ]
    )
    print("\n RESULT \n ")
    print(Back.WHITE+Fore.GREEN+interaction.output_text)


if __name__ == "__main__":
    main()

