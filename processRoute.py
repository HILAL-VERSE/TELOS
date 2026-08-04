from flask import Flask, request, jsonify

import instaloader
import os
import glob
#from dotenv import load_dotenv
import base64
import time
import sys

#load_dotenv() 

from google import genai
client = genai.Client()

L = instaloader.Instaloader(
    download_pictures=False,
    download_geotags=False,
    download_comments=False,
    save_metadata=False,
    post_metadata_txt_pattern=""
)


folder_path = r'C:\Users\CELLFI\OneDrive\Desktop\saved_reel_manage\Reels_Download\*.mp4'
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

def authentication():
    try:
        username = "yng.hiiilaaaal"
        L.load_session_from_file(username)
        return "DONE"
    except Exception as e:
        raise Exception("Authentication failed")


def extractShortcode(url):
    try:
        parts = url.split("/")
        return parts[4]
    except Exception:
        return 0

app = Flask(__name__)



@app.route("/process")
def process():
    data = request.get_json()
    if not data:
        return jsonify({
            "Message": "Not data provided"
        }), 400

    url = data.get('url')
    if not url:
        return jsonify({
            "Message" : "Url is not provided"
        }), 400

    auth = authentication()
    if auth == "DONE":
        shortcode = extractShortcode(url)

        if not shortcode:
            return jsonify({
                "Message": "Couldn't find any shortcode from provide url"
            }), 400

        post = instaloader.Post.from_shortcode(L.context, shortcode)

        if post.is_video:
            L.download_post(post,target="Reels_Download")
        else:
            return({
                "Error": "Provide url is not a video"
            }), 400

        mp4_files = glob.glob(folder_path)
        if not mp4_files:
            return jsonify({
                "Message": "Could Not Find ANy mp4 Files in the Directory"
            }), 400
        else:
            latest_file = max(mp4_files, key=os.path.getctime)
            latest_file_name = os.path.basename(latest_file)


        fileUpload = client.files.upload(file=latest_file)
        while not fileUpload.state or fileUpload.state.name != "ACTIVE":
            print("Video processing")
            time.sleep(5)
            fileUpload = client.files.get(name=fileUpload.name)

        interaction = client.interactions.create(
            model="gemini-3.6-flash",
            input=[
                {"type": "video", "uri": fileUpload.uri, "mime_type": fileUpload.mime_type},
                {"type": "text", "text": prompt}
            ]
        )
        finalOutput = interaction.output_text
        


        return jsonify({
            "Messaage" : "Succesfully downloaded video",
            "Video Name" : latest_file_name,
            "Output" : finalOutput
        }), 201
    else:
        return jsonify({
            "Error": "Authenticatio failed"
        }), 401




if __name__ == '__main__':
    app.run(debug=True)
