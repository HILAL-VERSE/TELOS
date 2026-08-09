from flask import Flask, request, jsonify, render_template

import instaloader
import os
import glob
#from dotenv import load_dotenv
import base64
import time
import sys

import tempfile
temp_dir = tempfile.mkdtemp()

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
        session_data = os.getenv("SESSION_DATA")
        username = "yng.hiiilaaaal"
        raw_bytes = base64.b64decode(session_data)

        with tempfile.NamedTemporaryFile(delete=False) as temp_session_file:
            temp_session_file.write(raw_bytes)
            temp_session_path = temp_session_file.name
        
        L.load_session_from_file(username, filename=temp_session_path)
        os.remove(temp_session_path)
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



@app.route("/")
def home():
    return render_template("index.html")


@app.route("/share-target")
def share_target():
    shared_url = request.args.get('url') or request.args.get('text', '')
    return render_template("index.html", prefill_url=shared_url)

@app.route("/process", methods=["POST"])
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

        with tempfile.TemporaryDirectory() as temp_dir:
            L.dirname_pattern = temp_dir
            post = instaloader.Post.from_shortcode(L.context, shortcode)

            if post.is_video:
                L.download_post(post,target="reel")
            else:
                return({
                    "Error": "Provide url is not a video"
                }), 400

            filename = os.listdir(temp_dir)[0]
            video_file = os.path.join(temp_dir, filename)
            if not video_file:
                return jsonify({
                    "Message": "Could Not Find ANy mp4 Files in the Directory"
                }), 400


            fileUpload = client.files.upload(file=video_file)
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
            client.files.delete(name=fileUpload.name)
            


            return jsonify({
                "Messaage" : "Succesfully downloaded video",
                "Output" : finalOutput
            }), 201
    else:
        return jsonify({
            "Error": "Authenticatio failed"
        }), 401




if __name__ == '__main__':
    app.run(debug=True)
