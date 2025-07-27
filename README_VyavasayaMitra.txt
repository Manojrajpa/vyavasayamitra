# VyavasayaMitra – WhatsApp AI Assistant 🌾📲

This project is a **WhatsApp-based advisory assistant** for farmers that processes incoming **text**, **image**, and **audio** messages and responds with intelligent replies using your AI backend. Built using **Flask**, this project is deployed on **Google Cloud Run** and integrated with **Meta's WhatsApp Business Cloud API**.

---

## 🧠 How It Works

- A user (farmer/tester) sends a message (text/image/audio) to a **temporary WhatsApp number**.
- The Flask app receives this via a webhook set in the Meta Developer dashboard.
- The message is forwarded to an **AI backend** (ADK or your model).
- The response (text/audio/image) is sent back to the same user via WhatsApp.

---

## ⚙️ Tech Stack

| Component   | Tech Used                        |
|------------|----------------------------------|
| Backend    | Flask (Python)                   |
| Server     | Gunicorn                         |
| Container  | Docker, Cloud Run (GCP)          |
| Media Proc | `speechrecognition`, `pydub`, `gTTS` |
| Messaging  | Meta WhatsApp Business API       |
| Deployment | Google Cloud Build + GitHub      |

---

## 🔄 Temporary WhatsApp Number Logic

- Meta provides a **sandbox environment** for developers to test their WhatsApp integration.
- It includes a **temporary number** you can message.
- To use it:
  1. Join the sandbox by sending a `join <code>` message to the temporary number.
  2. Only **registered tester numbers** can interact with the number.
  3. You can add testers from your **Meta Developer dashboard**.

---

## 🧪 Local Testing with `ngrok`

### 🔧 Requirements

- Python 3.9+
- `ngrok`
- Meta Developer App with WhatsApp product enabled
- Your number added as a tester

### 🛠️ Steps

```bash
# Clone this repo or navigate to your project directory
cd whatsapp_flask_cloudrun_deploy

# Install dependencies
pip install -r requirements.txt

# Run locally
python app.py
```

Now in another terminal:

```bash
# Start ngrok tunnel on port 5000
ngrok http 5000
```

You’ll get an HTTPS URL like `https://abc123.ngrok.io`.

---

### 🔗 Set Webhook in Meta Dashboard

Go to:
```
Meta Developer Dashboard → WhatsApp → Configuration → Webhook
```

- **Callback URL**: `https://abc123.ngrok.io/webhook`
- **Verify Token**: Should match the value in your `app.py` (e.g., `"vyavasaya"`)

---

## 🚀 Deploy to Google Cloud Run

> Already deployed on GCP via Cloud Run : vm-wa-f

To deploy using **GitHub + Cloud Build**:

1. Push your code to a GitHub repository
2. Go to [Google Cloud Console → Cloud Run](https://console.cloud.google.com/run)
3. Click **"Create Service"**
4. Choose **"Continuously deploy from GitHub"**
5. Choose project, repo, and branch
6. Confirm the region and service name
7. Set container port: `8080`
8. Allow public access
9. Click **Create**

---

## 🐳 Docker Setup (used in deployment)

### Dockerfile
```dockerfile
FROM python:3.9

WORKDIR /app
COPY . .

RUN apt-get update && apt-get install -y ffmpeg
RUN pip install --no-cache-dir -r requirements.txt

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
```

### entrypoint.sh
Make sure this file is executable:

```bash
#!/bin/bash
exec gunicorn --bind 0.0.0.0:8080 app:app
```

Set permissions:
```bash
chmod +x entrypoint.sh
```

---

## 📁 Project Structure

```
.
├── app.py
├── Dockerfile
├── entrypoint.sh
├── requirements.txt
└── README.md
```

---

## 📦 `requirements.txt` (Sample)

```text
Flask==2.3.3
gunicorn==21.2.0
requests==2.31.0
gTTS==2.5.1
pydub==0.25.1
speechrecognition==3.10.1
```

---

## 🧾 Logs & Debugging

To view logs:

- Go to Cloud Console → Cloud Run → Select service
- Click on **"Logs"** tab to view traceback errors

Common errors:
- `Permission denied for entrypoint.sh` → Add `chmod +x entrypoint.sh`
- `No module named 'audioop'` → Check `requirements.txt` and base image
- `PORT not found` → Ensure app uses `PORT=8080`

---

## 🧪 Manual API Testing

Use Postman or `curl` to send test POST payloads to:

```
https://your-cloud-run-service-url/webhook
```

---

## 📬 Maintainer

**Manoj Raj**  
📧 Email: manoj.raj@example.com  
🔗 Cloud Run Endpoint: [VyavasayaMitra](https://vyavasayamitra-wa-<unique>.run.app)

---

## ✅ Future Plans

- Permanent WhatsApp number setup
- User data & preferences storage
- Language support (multi-lingual)
- Logging dashboard

---

## 🧡 License

MIT License – Free to use with credits.
