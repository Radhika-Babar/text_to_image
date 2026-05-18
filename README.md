# 🌌 Unified Text-to-Image Platform

A multi-provider AI image generation application built with Python and Gradio that generates images simultaneously using multiple AI providers.

## ✨ Preview

This application:

* accepts a text prompt
* sends it to multiple AI image providers in parallel
* displays generated images side-by-side
* shows real-time logs and provider status

Designed for:

* AI experimentation
* portfolio projects
* internship projects
* learning API orchestration
* learning parallel processing

---

## 🚀 Supported Providers

| Provider              | Model / Service     | Type                     |
| --------------------- | ------------------- | ------------------------ |
| Hugging Face          | FLUX.1-schnell      | AI Image Generation      |
| Cloudflare Workers AI | Stable Diffusion XL | AI Image Generation      |
| Pollinations.ai       | Public AI Endpoint  | Free AI Image Generation |

A multi-provider AI image generation application built using Python and Gradio.

This project generates images in parallel using multiple AI providers:

* Hugging Face
* Cloudflare Workers AI
* Pollinations.ai

The system is designed with:

* parallel image generation
* fault tolerance
* fallback handling
* real-time logs
* multi-provider architecture

---

# 🚀 Features

## ✅ Multi-Provider AI Generation

Generate images simultaneously using:

* Hugging Face FLUX.1-schnell
* Cloudflare Stable Diffusion XL
* Pollinations.ai

---

## ✅ Parallel Processing

Uses Python ThreadPoolExecutor to:

* send requests simultaneously
* reduce waiting time
* improve responsiveness

---

## ✅ Real-Time Logs

Displays:

* provider status
* success messages
* API errors
* generation progress

inside the Gradio UI.

---

## ✅ Fault Tolerant Architecture

If one provider fails:

* app does NOT crash
* placeholder images are shown
* other providers continue working

---

## ✅ Environment Variable Security

API keys are securely loaded using `.env`.

---

# 🖼️ Providers Used

| Provider        | Model               | Purpose                    |
| --------------- | ------------------- | -------------------------- |
| Hugging Face    | FLUX.1-schnell      | High-quality AI generation |
| Cloudflare      | Stable Diffusion XL | Stable and fast inference  |
| Pollinations.ai | Public AI endpoint  | Free fallback generation   |

---

# 📦 Installation

## 1. Clone the Repository

```bash
git clone <your-repo-url>
cd <your-project-folder>
```

---

## 2. Create Virtual Environment (Recommended)

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install gradio requests pillow python-dotenv
```

---

# 🔑 API Key Setup

Create a `.env` file in the SAME folder as `app.py`.

Example:

```env
HF_TOKEN=your_huggingface_token
CF_ACCOUNT_ID=your_cloudflare_account_id
CF_API_TOKEN=your_cloudflare_api_token
```

---

# 🔹 Hugging Face Setup

## Step 1

Create an account:

[https://huggingface.co/](https://huggingface.co/)

---

## Step 2

Go to:

Settings → Access Tokens

---

## Step 3

Create a new token.

Recommended permissions:

* Inference Providers
* Read Access

---

## Step 4

Copy token into `.env`

```env
HF_TOKEN=hf_xxxxxxxxxxxxxxxxx
```

---

# 🔹 Cloudflare Setup

## Step 1

Create account:

[https://dash.cloudflare.com/](https://dash.cloudflare.com/)

---

## Step 2

Enable Workers AI.

---

## Step 3

Get:

* Account ID
* API Token

---

## Step 4

Add to `.env`

```env
CF_ACCOUNT_ID=xxxxxxxxxxxx
CF_API_TOKEN=xxxxxxxxxxxx
```

---

# ▶️ Running the Project

Run:

```bash
python app.py
```

Then open:

```text
http://127.0.0.1:7860
```

---

# 🧠 How the System Works

## Step 1 — User Enters Prompt

Example:

```text
A futuristic cyberpunk city during heavy rain
```

---

## Step 2 — Requests Sent in Parallel

The application sends the prompt simultaneously to:

* Hugging Face
* Cloudflare
* Pollinations.ai

using threads.

---

## Step 3 — AI Generates Images

Each provider returns:

* generated image
* error
* timeout

---

## Step 4 — UI Updates Incrementally

Results appear live in the Gradio interface.

---

# 🏗️ Architecture Overview

```text
User Prompt
     ↓
Master Generator
     ↓
ThreadPoolExecutor
     ↓
 ┌──────────────┬──────────────┬──────────────┐
 │ HuggingFace │ Cloudflare   │ Pollinations │
 └──────────────┴──────────────┴──────────────┘
     ↓
Collect Results
     ↓
Gradio UI
```

---

# ⚠️ Common Errors

## 1. 401 Unauthorized

### Cause

Invalid API token.

### Fix

Check `.env` credentials.

---

## 2. 429 Too Many Requests

### Cause

Free-tier rate limit exceeded.

### Fix

Wait before retrying.

---

## 3. Pollinations Invalid Image Error

### Cause

Pollinations returned HTML or invalid data instead of an image.

### Fix

The application already handles this using image validation.

---

# 🔒 Why API Keys Are Stored in .env

Using `.env` helps:

* protect credentials
* avoid exposing secrets on GitHub
* keep configuration clean

---

# 📁 Recommended Project Structure

```text
project/
│
├── app.py
├── .env
├── .gitignore
├── README.md
└── requirements.txt
```

---

# 🧾 Example .gitignore

```gitignore
.env
.venv/
__pycache__/
*.pyc
```

---

# 🌟 Example Prompts

## Cyberpunk City

```text
A futuristic cyberpunk city during heavy rain at night, neon holograms, flying cars, cinematic lighting, ultra detailed, Blade Runner style, 8k
```

---

## Space Battle

```text
A massive interstellar war near a collapsing star, ultra realistic sci-fi scene, cinematic explosions, detailed spacecraft, 8k
```

---

## Fantasy Dragon Temple

```text
Ancient dragon temple hidden in snowy mountains, glowing lanterns, fantasy realism, cinematic atmosphere
```

---

# 📊 Free Tier Comparison

| Provider        | Free Tier          | Reliability | Notes                |
| --------------- | ------------------ | ----------- | -------------------- |
| Hugging Face    | Moderate           | Good        | Shared GPU inference |
| Cloudflare      | Moderate           | Very High   | Most stable provider |
| Pollinations.ai | Public Free Access | Medium      | Sometimes unstable   |

---

# 🎯 Best Use Cases

This project is ideal for:

* AI learning
* portfolio projects
* internship demonstrations
* college projects
* experimentation with multi-provider AI systems

---

# 🔮 Future Improvements

Possible upgrades:

* image download support
* image history
* prompt presets
* model selection
* async queue system
* user authentication
* deployment to cloud
* Docker support
* database integration
* prompt enhancement AI

---

# 🛠️ Technologies Used

| Technology         | Purpose                         |
| ------------------ | ------------------------------- |
| Python             | Backend logic                   |
| Gradio             | Web UI                          |
| Requests           | API communication               |
| Pillow             | Image processing                |
| dotenv             | Environment variable management |
| ThreadPoolExecutor | Parallel execution              |

---

# 📜 License

This project is intended for:

* educational purposes
* experimentation
* learning AI APIs

Always review provider-specific terms of service before commercial deployment.

---

# 👨‍💻 Author

Built as a multi-provider AI image generation system for learning modern AI infrastructure and parallel API orchestration.
