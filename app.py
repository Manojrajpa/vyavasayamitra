from flask import Flask, request, jsonify
import requests
import tempfile
import base64
import json
import os
import uuid
from pydub import AudioSegment
from gtts import gTTS
import speech_recognition as sr

app = Flask(__name__)

# Meta credentials
WHATSAPP_TOKEN = "EAA5up1wUFK0BPGRGsJ98SXVUAoZCo2ZCbYKSDP1kQJBteMWbZBtJWzVP7FrfMBWOu3mYZAUjbdZChfy5UlnEaQg08Fg1yaAZBxJ1eswhSgEfVmCSK3V5XRGLJMYl4MH8FDBnkBdgZAsxKfKLRhb4wTgs26KYOoEKPQ3dXY3NVO6WZASwsTMutTseNvJtX78ZBr705bb0TROZBFYYBepeODnSF50sojX9mDUGWpZA8VZCC6qQ3qZAgJFkZD"
VERIFY_TOKEN = "testtoken123"
PHONE_NUMBER_ID = "643030762237160"

# AI backend endpoints
SESSION_START_URL = "https://mcp-707891837593.us-central1.run.app/apps/mcp/users/{mobile_no}/sessions"
CHAT_API_URL = "https://mcp-707891837593.us-central1.run.app/run_sse"

# Session management
user_sessions = {}  # mobile_no -> {'session_id': ..., 'user_id': ...}
processed_message_ids = set()

def download_media(media_id):
    media_url = f"https://graph.facebook.com/v19.0/{media_id}"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    res = requests.get(media_url, headers=headers)
    if res.status_code == 200:
        file_url = res.json().get("url")
        file_res = requests.get(file_url, headers=headers)
        if file_res.status_code == 200:
            return file_res.content
    return None

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        return "Invalid verification token", 403

    if request.method == "POST":
        data = request.get_json()
        print("Incoming:", data)

        try:
            entry = data["entry"][0]
            value = entry["changes"][0]["value"]
            messages = value.get("messages", [])

            if not messages:
                return "OK", 200

            message = messages[0]
            message_id = message["id"]
            mobile_no = message["from"]
            msg_type = message["type"]

            if message_id in processed_message_ids:
                return "Duplicate skipped", 200
            processed_message_ids.add(message_id)

            if mobile_no not in user_sessions:
                session_res = requests.post(
                    SESSION_START_URL.format(mobile_no=mobile_no),
                    headers={"Content-Type": "application/json"},
                    verify=False
                )
                session_data = session_res.json()
                user_sessions[mobile_no] = {
                    "session_id": session_data.get("id"),
                    "user_id": mobile_no
                }

            session_id = user_sessions[mobile_no]["session_id"]
            user_id = user_sessions[mobile_no]["user_id"]

            if msg_type == "text":
                user_msg = message["text"]["body"]
                payload = build_payload(user_id, session_id, [{"text": user_msg}])
                handle_chat_api(payload, mobile_no, also_send_audio=False)

            elif msg_type == "image":
                media_id = message["image"]["id"]
                caption = message["image"].get("caption", "Image")
                image_bytes = download_media(media_id)
                if image_bytes:
                    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
                    parts = [
                        {"text": caption},
                        {"inlineData": {
                            "displayName": "uploaded_image.jpg",
                            "data": image_b64,
                            "mimeType": "image/jpeg"
                        }}
                    ]
                    payload = build_payload(user_id, session_id, parts)
                    handle_chat_api(payload, mobile_no, also_send_audio=False)

            elif msg_type == "audio":
                media_id = message["audio"]["id"]
                audio_bytes = download_media(media_id)
                if audio_bytes:
                    filename = str(uuid.uuid4())
                    ogg_path = os.path.join(tempfile.gettempdir(), f"{filename}.ogg")
                    wav_path = ogg_path.replace(".ogg", ".wav")

                    with open(ogg_path, "wb") as f:
                        f.write(audio_bytes)

                    AudioSegment.from_file(ogg_path).export(wav_path, format="wav")

                    recognizer = sr.Recognizer()
                    try:
                        with sr.AudioFile(wav_path) as source:
                            audio_data = recognizer.record(source)
                            transcribed_text = recognizer.recognize_google(audio_data)
                    except sr.UnknownValueError:
                        send_whatsapp_text(mobile_no, "Sorry, I couldn't understand your audio message.")
                        return "OK", 200

                    parts = [{"text": transcribed_text}]
                    payload = build_payload(user_id, session_id, parts)
                    handle_chat_api(payload, mobile_no, also_send_audio=True)

                    os.remove(ogg_path)
                    os.remove(wav_path)

        except Exception as e:
            print("Webhook Error:", e)

        return "OK", 200

def build_payload(user_id, session_id, parts):
    return {
        "appName": "mcp",
        "userId": user_id,
        "sessionId": session_id,
        "newMessage": {"role": "user", "parts": parts},
        "streaming": False
    }

def handle_chat_api(payload, mobile_no, also_send_audio=False):
    try:
        res = requests.post(CHAT_API_URL, json=payload, verify=False)
        if res.status_code != 200:
            print("Chat API Error:", res.text)
            return

        full_reply = ""
        for line in res.text.strip().split("\n"):
            if line.startswith("data:"):
                content_data = json.loads(line.replace("data: ", ""))
                if "content" in content_data:
                    part = content_data["content"]["parts"][0]
                    if "text" in part:
                        full_reply += part["text"] + " "

        full_reply = full_reply.strip()
        send_whatsapp_text(mobile_no, full_reply)

        if also_send_audio:
            send_whatsapp_audio(mobile_no, full_reply)

    except Exception as e:
        print("handle_chat_api error:", e)

def send_whatsapp_text(recipient_id, message):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_id,
        "type": "text",
        "text": {"body": message[:4096]}
    }
    r = requests.post(url, json=payload, headers=headers)
    print("Text sent:", r.status_code)

def send_whatsapp_audio(recipient_id, message):
    try:
        tts = gTTS(message, lang='en', tld='co.in')  # Indian accent
        audio_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.mp3")
        tts.save(audio_path)

        # Optional: Increase speed using pydub
        fast_audio_path = audio_path.replace(".mp3", "_fast.mp3")
        sound = AudioSegment.from_file(audio_path)
        faster = sound.speedup(playback_speed=1.3)
        faster.export(fast_audio_path, format="mp3")

        upload_url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/media"
        headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
        with open(fast_audio_path, "rb") as f:
            files = {"file": ("response.mp3", f, "audio/mpeg")}
            data = {
                "messaging_product": "whatsapp",
                "type": "audio",
            }
            res = requests.post(upload_url, data=data, files=files, headers=headers)
            print("Upload audio response:", res.status_code, res.text)
            media_id = res.json().get("id")

        if not media_id:
            print("Failed to upload audio. No media_id received.")
            return

        send_url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
        headers["Content-Type"] = "application/json"
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "audio",
            "audio": {"id": media_id}
        }
        r = requests.post(send_url, json=payload, headers=headers)
        print("Audio send response:", r.status_code, r.text)

        os.remove(audio_path)
        os.remove(fast_audio_path)

    except Exception as e:
        print("send_whatsapp_audio error:", e)

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(port=5050, debug=True)
