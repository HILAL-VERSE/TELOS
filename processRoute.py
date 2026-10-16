from flask import Flask, request, jsonify, render_template
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import json
import datetime
from pymongo import MongoClient
import instaloader
import os
import glob
from dotenv import load_dotenv
import base64
import time
import sys

import tempfile
temp_dir = tempfile.mkdtemp()


load_dotenv() 

from google import genai
from google.genai import types, errors
client = genai.Client()

mongo_client = MongoClient(os.environ["MONGO_URI"])
db = mongo_client["telosDb"]
collection = db["CoreData"]

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

    ### PHASE 1: INTENT CATEGORIZATION & AUTHENTICITY
    Classify this content into exactly ONE of these categories: Learn, Try, Visit, Buy, Watch-again, Mixed.
    - Use "Mixed" only if none of the other categories genuinely fit.
    - If genre is Historical/News/factual, verify claims and provide an Authenticity Score (1-10) with reasoning. Otherwise, set authenticity_score to "N/A".

    ### PHASE 2: THE DEFINITIVE NARRATIVE (Mastery Mode)
    Write a long-form, cohesive essay (750+ words) explaining the content. Do NOT use bullet points. 
    - If it is a historical event or such contents, you must complete the story for the user, providing the full lead-up, the event itself, and the aftermath.
    - Explain complex concepts mid-flow so the user acquires total mastery.
    - The prose must be detailed, professional, and immersive.

    ### PHASE 3: STRUCTURED DATA (Appendix)
    - Manifest: People, tools, locations, and brands.
    - Implicit Context: The "between the lines" purpose.
    - Research Roadmap: 3-5 specific topics to investigate next to complete the knowledge loop.

    ### OUTPUT FORMAT
    Respond ONLY with valid JSON matching the provided schema. Do not include markdown formatting, code fences, or any text outside the JSON object.
     """


@retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=16),
        retry=retry_if_exception_type(errors.ServerError),
        reraise=True
)
def generate_with_retry(client, fileUpload, prompt, types):
    return client.models.generate_content(
        model="gemini-3.6-flash",
        contents=[
            types.Part.from_uri(file_uri=fileUpload.uri, mime_type=fileUpload.mime_type),
            prompt
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": ["Learn", "Try", "Visit", "Buy", "Watch_again", "Mixed"]
                        },
                    "type_genre": {"type": "string"},
                    "authenticity_score": {"type": "string"},
                    "reasoning": {"type": "string"},
                    "definitive_narrative": {"type": "string"},
                    "structured_data": {"type": "string"},
                    "implicit_context": {"type": "string"},
                    "research_roadmap": {"type": "string"}
                },
                "required": ["category", "type_genre", "authenticity_score", "reasoning", "definitive_narrative", "structured_data", "implicit_context", "research_roadmap"]
            }
        )
    )



def authentication():
    try:
        session_data = os.getenv("SESSION_DATA")        
        username = os.getenv("USER_NAME")

        if not session_data or not username:
            raise ValueError("Could not find session data or username")

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
    CoreDataCollection = collection.find()
    return render_template("index.html", items = CoreDataCollection)


@app.route("/share-target")
def share_target():
    CoreDataCollection = collection.find()
    shared_url = request.args.get('url') or request.args.get('text', '')
    return render_template("index.html", prefill_url=shared_url, items = CoreDataCollection)

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
        print("Logged")
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
            

            try:
                response = generate_with_retry(client, fileUpload, prompt, types)
            except errors.ServerError as e:
                print(f"Failed after multiple retries: {e}")

            finalOutput = json.loads(response.text)
            client.files.delete(name=fileUpload.name)
            try:
                document = {
                    "category":finalOutput.get("category"),
                    "type_genre":finalOutput.get("type_genre"),
                    "authenticity_score": finalOutput.get("authenticity_score"),
                    "definitive_narrative": finalOutput.get("definitive_narrative"),
                    "structured_data": finalOutput.get("structured_data"),
                    "implicit_context": finalOutput.get("implicit_context"),
                    "research_roadmap": finalOutput.get("research_roadmap"),
                    "reasoning": finalOutput.get("reasoning"),
                    "timestamp": datetime.datetime.utcnow()
                }

                collection.insert_one(document)
                print(f"Data inserted succefully : {document}" )
            except Exception as e:
                    raise Exception("Failed to insert document into MongoDB: " + str(e))
                    return jsonify({
                        "Error": "Failed to insert document into MongoDB"
                    }), 500

            return jsonify({
                "Messaage" : "Succesfully downloaded video",
                "Output" : finalOutput
            }), 201
    else:
        return jsonify({
            "Error": "Authentication failed"
        }), 401



'''
if __name__ == '__main__':
    app.run(debug=True)
'''