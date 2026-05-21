import sys

if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(
        asyncio.WindowsSelectorEventLoopPolicy()
    )

import os
import io
import json
import time
import fal_client
import base64
import random
import requests
import urllib.parse
import gradio as gr
import boto3
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN", "")
CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID", "")
CF_API_TOKEN = os.getenv("CF_API_TOKEN", "")
AI_HORDE_API_KEY = os.getenv("AI_HORDE_API_KEY", "0000000000")
IMAGEROUTER_API_KEY = os.getenv("IMAGEROUTER_API_KEY","")
FAL_KEY = os.getenv("FAL_KEY","")

bedrock_default = boto3.client(
    service_name="bedrock-runtime",
    region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
)

bedrock_west = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-west-2",   
)

# ==========================================
# STARTUP DEBUG
# ==========================================

print("\n========== API STATUS ==========")
print("HF_TOKEN :", "FOUND" if HF_TOKEN  else "MISSING")
print("CF_ACCOUNT_ID :", "FOUND" if CF_ACCOUNT_ID  else "MISSING")
print("CF_API_TOKEN :", "FOUND" if CF_API_TOKEN  else "MISSING")
print("AI_HORDE_API_KEY:", "FOUND" if AI_HORDE_API_KEY else "MISSING")
print("FAL_KEY:", "FOUND" if FAL_KEY else "MISSING")
print("Bedrock default region :", os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
print("Bedrock Stability region: us-west-2 (hardcoded)")
print("================================\n")

NUM_MODELS = 11

# ==========================================
# HELPERS
# ==========================================
def create_placeholder(text: str = "Generation Failed") -> Image.Image:
    img  = Image.new("RGB", (512, 512), color=(40, 40, 40))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.load_default()
        draw.text((20, 236), text, fill=(255, 80, 80), font=font)
    except Exception:
        pass
    return img

def decode_base64_image(b64: str) -> Image.Image:
    return Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGB")

#FAL GENERATOR

def generate_fal(prompt: str):
    platform = "fal.ai"
    start_time = time.time()
    try:
        if not FAL_KEY:
            raise ValueError(
                "FAL_KEY missing"
            )
        os.environ["FAL_KEY"] = FAL_KEY
        result = fal_client.subscribe(
            "fal-ai/flux/schnell",
            arguments={
                "prompt": prompt
            },
            with_logs=False
        )
        image_url = result["images"][0]["url"]
        img_response = requests.get(
            image_url,
            timeout=180
        )
        image = Image.open(
            io.BytesIO(img_response.content)
        ).convert("RGB")
        total_time = round(
            time.time() - start_time,
            2
        )
        return (
            platform,
            image,
            f"{platform}: Success ({total_time}s)"
        )
    except Exception as e:
        total_time = round(
            time.time() - start_time,
            2
        )
        return (
            platform,
            create_placeholder(
                f"fal.ai Error\n{str(e)[:60]}"
            ),
            f"{platform}: Error — {e} ({total_time}s)"
        )
# ==========================================
# GENERATOR — HUGGING FACE  (index 0)
# Model: black-forest-labs/FLUX.1-schnell
# ==========================================
def generate_hf(prompt: str):
    platform = "Hugging Face"
    start_time = time.time()
    try:
        resp = requests.post(
            "https://router.huggingface.co/hf-inference/models/"
            "black-forest-labs/FLUX.1-schnell",
            headers={
                "Authorization": f"Bearer {HF_TOKEN}",
                "Content-Type": "application/json",
            },
            json={"inputs": prompt},
            timeout=120,
        )
        resp.raise_for_status()
        image = Image.open(
            io.BytesIO(resp.content)
        ).convert("RGB")
        total_time = round(
            time.time() - start_time,
            2
        )
        return (
            platform,
            image,
            f"{platform}: Success ({total_time}s)"
        )
    except Exception as e:
        total_time = round(
            time.time() - start_time,
            2
        )
        return (
            platform,
            create_placeholder(
                f"HF Error\n{str(e)[:60]}"
            ),
            f"{platform}: Error — {e} ({total_time}s)"
        )
# ==========================================
# GENERATOR — CLOUDFLARE  (index 1)
# Model: @cf/stabilityai/stable-diffusion-xl-base-1.0
# ==========================================
def generate_cf(prompt: str):
    platform = "Cloudflare"
    start_time = time.time()
    try:
        url = (
            f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}"
            "/ai/run/@cf/stabilityai/stable-diffusion-xl-base-1.0"
        )
        resp = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {CF_API_TOKEN}"
            },
            json={"prompt": prompt},
            timeout=120,
        )
        resp.raise_for_status()
        image = Image.open(
            io.BytesIO(resp.content)
        ).convert("RGB")
        total_time = round(
            time.time() - start_time,
            2
        )
        return (
            platform,
            image,
            f"{platform}: Success ({total_time}s)"
        )
    except Exception as e:
        total_time = round(
            time.time() - start_time,2)
        return (
            platform,
            create_placeholder(
                f"CF Error\n{str(e)[:60]}"
            ),
            f"{platform}: Error — {e} ({total_time}s)"
        )
# ==========================================
# GENERATOR — POLLINATIONS  (index 2)
# ==========================================
def generate_pollinations(prompt: str):
    platform = "Pollinations.ai"
    start_time = time.time()
    try:
        seed = random.randint(1, 999_999)
        url = (
            f"https://image.pollinations.ai/prompt/"
            f"{urllib.parse.quote(prompt)}"
            f"?seed={seed}&width=1024&height=1024"
        )
        resp = requests.get(
            url,
            timeout=120,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )
        resp.raise_for_status()
        if not resp.headers.get(
            "Content-Type",
            ""
        ).startswith("image/"):
            raise ValueError(
                f"Non-image Content-Type: "
                f"{resp.headers.get('Content-Type')}"
            )
        image = Image.open(
            io.BytesIO(resp.content)
        ).convert("RGB")
        total_time = round(
            time.time() - start_time,
            2
        )
        return (
            platform,
            image,
            f"{platform}: Success ({total_time}s)"
        )
    except Exception as e:
        total_time = round(
            time.time() - start_time,
            2
        )
        return (
            platform,
            create_placeholder(
                f"Pollinations Error\n{str(e)[:60]}"
            ),
            f"{platform}: Error — {e} ({total_time}s)"
        ) 

# ==========================================
# GENERATOR — AI HORDE  (index 3)
# ==========================================
def generate_horde(prompt: str):
    platform = "AI Horde"
    start_time = time.time()
    try:
        resp = requests.post(
            "https://aihorde.net/api/v2/generate/async",
            headers={
                "apikey": AI_HORDE_API_KEY,
                "Client-Agent": "UnifiedAIPlatform:1.0"
            },
            json={
                "prompt": prompt,
                "params": {
                    "width": 512,
                    "height": 512,
                    "steps": 20
                }
            },
            timeout=120,
        )
        resp.raise_for_status()
        req_id = resp.json()["id"]
        status_url = (
            f"https://aihorde.net/api/v2/"
            f"generate/status/{req_id}"
        )
        for _ in range(20):
            time.sleep(8)
            poll = requests.get(status_url,timeout=60)
            if poll.status_code == 429:
                time.sleep(10)
                continue
            poll.raise_for_status()
            data = poll.json()
            if data.get("done"):
                generations = data.get("generations",[])
                if not generations:
                    raise ValueError(
                        "Empty generations list"
                    )
                img_resp = requests.get(
                    generations[0]["img"],
                    timeout=120
                )
                image = Image.open(
                    io.BytesIO(
                        img_resp.content
                    )
                ).convert("RGB")
                total_time = round(
                    time.time() - start_time,
                    2
                )
                return (platform,image,f"{platform}: Success ({total_time}s)")
        raise TimeoutError("Timed out after 160 s")
    except Exception as e:
        total_time = round(
            time.time() - start_time,
            2
        )
        return (
            platform,
            create_placeholder(
                f"AI Horde Error\n{str(e)[:60]}"
            ),
            f"{platform}: Error — {e} ({total_time}s)"
        )

# ==========================================
# STABILITY AI SHARED HELPER
#
# All Stability models on Bedrock share the
# same invoke pattern and us-west-2 endpoint.
# Every payload requires "mode": "text-to-image".
# ==========================================
def _invoke_stability(prompt: str, model_id: str, extra: dict | None = None) -> Image.Image:
    payload: dict = {
        "prompt": prompt,
        "mode": "text-to-image",   
        "output_format": "png",
    }
    if extra:
        payload.update(extra)
    resp = bedrock_west.invoke_model(   # ← us-west-2 required
        modelId=model_id,
        body=json.dumps(payload),
        accept="application/json",
        contentType="application/json",
    )
    body_out = json.loads(resp["body"].read())
    return decode_base64_image(body_out["images"][0])

# ==========================================
# GENERATOR — STABLE IMAGE CORE  (index 4)
# Model ID : stability.stable-image-core-v1:0
# Region   : us-west-2 ONLY
# ==========================================
def generate_stable_core(prompt: str):
    platform = "Stable Core"
    start_time = time.time()
    try:
        image = _invoke_stability(
            prompt,
            "stability.stable-image-core-v1:1",
            extra={
                "aspect_ratio": "1:1"
            },
        )
        end_time = time.time()
        total_time = round(end_time - start_time, 2)
        return (
            platform,
            image,
            f"{platform}: Success ({total_time}s)"
        )
    except Exception as e:
        end_time = time.time()
        total_time = round(end_time - start_time, 2)
        return (
            platform,
            create_placeholder(
                f"Stable Core Error\n{str(e)[:60]}"
            ),
            f"{platform}: Error — {e} ({total_time}s)"
        )

# ==========================================
# GENERATOR — STABLE IMAGE ULTRA  (index 5)
# Model ID : stability.stable-image-ultra-v1:0
# Region   : us-west-2 ONLY
# ==========================================
def generate_stable_ultra(prompt: str):
    platform = "Stable Ultra"
    start_time = time.time()
    try:
        image = _invoke_stability(
            prompt,
            "stability.stable-image-ultra-v1:1",
            extra={"aspect_ratio": "1:1"},
        )
        end_time = time.time()
        total_time = round(end_time - start_time, 2)
        return platform, image, f"{platform}: Success ({total_time}s)"
    except Exception as e:
        end_time = time.time()
        total_time = round(end_time - start_time, 2)
        return platform, create_placeholder(f"Stable Ultra Error\n{str(e)[:60]}"), f"{platform}: Error — {e} ({total_time}s)"

# ==========================================
# GENERATOR — SD3 LARGE  (index 6)
# Model ID : stability.sd3-large-v1:0
# Region   : us-west-2 ONLY
# ==========================================
def generate_sd3(prompt: str):
    platform = "SD3 Large"
    start_time = time.time()
    try:
        image = _invoke_stability(
            prompt,
            "stability.sd3-large-v1:0",
            extra={"aspect_ratio": "1:1"},
        )
        end_time = time.time()
        total_time = round(end_time - start_time, 2)
        return platform, image, f"{platform}: Success ({total_time}s)"
    except Exception as e:
        end_time = time.time()
        total_time = round(end_time - start_time, 2)
        return platform, create_placeholder(f"SD3 Error\n{str(e)[:60]}"), f"{platform}: Error — {e} ({total_time}s)"

# ==========================================
# GENERATOR — SD3.5 LARGE  (index 7)
# Model ID : stability.sd3-5-large-v1:0
# Region   : us-west-2 ONLY
# Replaces the EOL Titan v1
# ==========================================
def generate_sd35(prompt: str):
    platform = "SD3.5 Large"
    start_time = time.time()
    try:
        image = _invoke_stability(
            prompt,
            "stability.sd3-5-large-v1:0",
            extra={"aspect_ratio": "1:1"},
        )
        end_time = time.time()
        total_time = round(end_time - start_time, 2)
        return platform, image, f"{platform}: Success ({total_time}s)"
    except Exception as e:
        end_time = time.time()
        total_time = round(end_time - start_time, 2)
        return platform, create_placeholder(f"SD3.5 Error\n{str(e)[:60]}"), f"{platform}: Error — {e} ({total_time}s)"
    try:
        image = _invoke_stability(
            prompt,
            "stability.sd3-5-large-v1:0",
            extra={"aspect_ratio": "1:1"},
        )
        return platform, image, f"{platform}: Success"
    except Exception as e:
        return platform, create_placeholder(f"SD3.5 Error\n{str(e)[:60]}"), f"{platform}: Error — {e}"

# ==========================================
# GENERATOR — TITAN v2  (index 8) ← was index 5
# ==========================================
def generate_titan_v2(prompt: str):
    platform = "Titan v2"
    start_time = time.time()
    try:
        body = json.dumps({
            "taskType": "TEXT_IMAGE",
            "textToImageParams": {
                "text": prompt
            },
            "imageGenerationConfig": {
                "numberOfImages": 1,
                "height": 1024,
                "width": 1024,
                "cfgScale": 8.0,
            },
        })
        resp = bedrock_default.invoke_model(
            modelId="amazon.titan-image-generator-v2:0",
            body=body,
        )
        body_out = json.loads(
            resp["body"].read()
        )
        image = decode_base64_image(
            body_out["images"][0]
        )
        end_time = time.time()
        total_time = round(
            end_time - start_time,
            2
        )
        return (
            platform,
            image,
            f"{platform}: Success ({total_time}s)"
        )
    except Exception as e:
        end_time = time.time()
        total_time = round(
            end_time - start_time,
            2
        )
        return (
            platform,
            create_placeholder(
                f"Titan v2 Error\n{str(e)[:60]}"
            ),
            f"{platform}: Error — {e} ({total_time}s)"
        )    
# ==========================================
# Amazon Nova
# ========================================== 
def generate_nova_canvas(prompt: str):
    platform = "Nova Canvas"
    start_time = time.time()
    try:
        body = json.dumps({
            "taskType": "TEXT_IMAGE",
            "textToImageParams": {
                "text": prompt
            },
            "imageGenerationConfig": {
                "numberOfImages": 1,
                "height": 1024,
                "width": 1024,
                "cfgScale": 8.0,
                "seed": random.randint(0, 999999)
            }
        })
        response = bedrock_default.invoke_model(
            modelId="amazon.nova-canvas-v1:0",
            body=body,
            contentType="application/json",
            accept="application/json"
        )
        response_body = json.loads(
            response["body"].read()
        )
        image_base64 = response_body["images"][0]
        image = decode_base64_image(
            image_base64
        )
        end_time = time.time()
        total_time = round(
            end_time - start_time,
            2
        )
        return (
            platform,
            image,
            f"{platform}: Success ({total_time}s)"
        )
    except Exception as e:
        end_time = time.time()
        total_time = round(
            end_time - start_time,
            2
        )
        return (
            platform,
            create_placeholder(
                f"Nova Canvas Error\n{str(e)[:60]}"
            ),
            f"{platform}: Error — {e} ({total_time}s)"
        )  
# ==========================================
# MASTER GENERATOR
# ==========================================
ADAPTERS = [
    (generate_hf,0),   # Hugging Face · FLUX.1-schnell
    (generate_cf,1),   # Cloudflare · SDXL
    (generate_pollinations,2),   # Pollinations.ai
    (generate_horde,3),   # AI Horde
    (generate_stable_core,4),   # Stable Image Core v1 (us-west-2)
    (generate_stable_ultra,5),   # Stable Image Ultra v1 (us-west-2)
    (generate_sd3,6),   # SD3 Large v1 (us-west-2)
    (generate_sd35,7),   # SD3.5 Large v1  (us-west-2)
    (generate_titan_v2,8),
    (generate_nova_canvas,9),
    (generate_fal, 10),   # fal.ai
]
assert len(ADAPTERS) == NUM_MODELS, (
    f"ADAPTERS has {len(ADAPTERS)} entries but NUM_MODELS={NUM_MODELS}. "
    "Update NUM_MODELS or fix the ADAPTERS list."
)
def run_all_generators(prompt: str):
    ts = lambda: time.strftime("%H:%M:%S")  # noqa: E731
    overall_start = time.time()
    logs = (
        f"[{ts()}] 🚀 Prompt: '{prompt}'\n\n"
    )
    pending = create_placeholder(
        "Generating…"
    )
    results = [pending] * NUM_MODELS
    yield (*results, logs)
    with ThreadPoolExecutor(
        max_workers=NUM_MODELS
    ) as executor:
        future_map = {
            executor.submit(fn, prompt): idx
            for fn, idx in ADAPTERS
        }
        for future in as_completed(
            future_map
        ):
            idx = future_map[future]
            try:
                platform, img, msg = (
                    future.result()
                )
                results[idx] = img
                logs += (
                    f"[{ts()}] ✅ {msg}\n"
                )
            except Exception as exc:
                results[idx] = create_placeholder(
                    "Critical Error"
                )
                logs += (
                    f"[{ts()}] ❌ "
                    f"Slot {idx}: {exc}\n"
                )
            yield (*results, logs)
    overall_end = time.time()
    total_runtime = round(
        overall_end - overall_start,
        2
    )
    logs += (
        f"\n[{ts()}] 🎉 "
        f"All generations completed "
        f"in {total_runtime}s"
    )
    yield (*results, logs)
# ==========================================
# UI
# ==========================================
with gr.Blocks(title="Unified AI Image Generator") as demo:
    gr.Markdown(
        "# 🌌 Unified Multi-Model AI Image Generator\n"
        "Generates images from **9 models** in parallel."
    )
    gr.Markdown()
    with gr.Row():
        prompt_input = gr.Textbox(
            label="Prompt",
            lines=3,
            placeholder="A futuristic cyberpunk city at night with neon lights…",
            scale=5,
        )
        generate_btn = gr.Button("🚀 Generate All", variant="primary", scale=1, min_width=140)
    logs_output = gr.Textbox(label="📋 Generation Logs", lines=10, interactive=False)
    # ── Free / external APIs ─────────────────────────────────────────────────
    gr.Markdown("### 🌐 Free / External APIs")
    with gr.Row():
        img_hf = gr.Image(label="Hugging Face · FLUX.1-schnell")
        img_cf = gr.Image(label="Cloudflare · SDXL")
        img_poll = gr.Image(label="Pollinations.ai")
        img_horde = gr.Image(label="AI Horde")
        img_fal = gr.Image(label="fal.ai")
    # ── Stability AI on Bedrock (us-west-2) ───────────────────────────────────
    gr.Markdown("### 🟣 AWS Bedrock — Stability AI  *(us-west-2)*")
    with gr.Row():
        img_score = gr.Image(label="Stable Image Core v1")
        img_sultra = gr.Image(label="Stable Image Ultra v1")
        img_sd3 = gr.Image(label="SD3 Large v1")
        img_sd35 = gr.Image(label="SD3.5 Large v1")
    # ── Amazon Titan ──────────────────────────────────────────────────────────
    gr.Markdown("### 🟠 AWS Bedrock — Amazon Titan  *(default region · needs enabling)*")
    with gr.Row():
        img_titan2 = gr.Image(label="Titan v2 · 1024 px")
        img_nova = gr.Image(label="Nova Canvas . 1024 px")
    # ── Wire up ───────────────────────────────────────────────────────────────
    # Order must match ADAPTERS indices 0-8, then logs at position 9.
    outputs = [
        img_hf, 
        img_cf, 
        img_poll, 
        img_horde,
        img_score,
        img_sultra,
        img_sd3,
        img_sd35,
        img_titan2,
        img_nova,
        img_fal,
        logs_output,
    ]
    generate_btn.click(fn=run_all_generators, inputs=prompt_input, outputs=outputs)
# ==========================================
# MAIN
# ==========================================
if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", share=False)