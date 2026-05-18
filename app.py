import sys

if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(
        asyncio.WindowsSelectorEventLoopPolicy()
    )
import os
import io
import time
import requests
import urllib.parse
import gradio as gr
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
from concurrent.futures import ThreadPoolExecutor, as_completed
# LOAD ENV VARIABLES
load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN", "")
CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID", "")
CF_API_TOKEN = os.getenv("CF_API_TOKEN", "")
# DEBUG LOGGING
print("\n========== API STATUS ==========")
print(
    "HF_TOKEN:",
    "FOUND" if HF_TOKEN else "MISSING"
)
print(
    "CF_ACCOUNT_ID:",
    "FOUND" if CF_ACCOUNT_ID else "MISSING"
)
print(
    "CF_API_TOKEN:",
    "FOUND" if CF_API_TOKEN else "MISSING"
)
print("================================\n")
# PLACEHOLDER IMAGE
def create_placeholder(text="Generation Failed"):

    img = Image.new(
        "RGB",
        (512, 512),
        color=(40, 40, 40)
    )

    draw = ImageDraw.Draw(img)

    try:

        font = ImageFont.load_default()

        if hasattr(draw, "textbbox"):

            bbox = draw.textbbox(
                (0, 0),
                text,
                font=font
            )
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
        else:
            text_w, text_h = draw.textsize(
                text,
                font=font
            )
        draw.text(
            (
                (512 - text_w) / 2,
                (512 - text_h) / 2
            ),
            text,
            fill=(255, 80, 80),
            font=font,
        )
    except Exception:

        draw.text(
            (20, 250),
            text,
            fill=(255, 80, 80)
        )

    return img

# HUGGING FACE
def generate_hf(prompt):

    platform = "Hugging Face"

    try:

        if not HF_TOKEN:
            raise ValueError("HF_TOKEN not set")

        api_url = (
            "https://router.huggingface.co/"
            "hf-inference/models/"
            "black-forest-labs/FLUX.1-schnell"
        )

        headers = {
            "Authorization": f"Bearer {HF_TOKEN}",
            "Content-Type": "application/json"
        }

        payload = {
            "inputs": prompt
        }

        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=120
        )

        print("HF STATUS:", response.status_code)

        if response.status_code != 200:
            print(response.text)

        response.raise_for_status()

        image = Image.open(
            io.BytesIO(response.content)
        ).convert("RGB")

        return (
            platform,
            image,
            f"{platform}: Success"
        )

    except Exception as e:

        return (
            platform,
            create_placeholder(
                f"HF Error\n{str(e)[:40]}"
            ),
            f"{platform}: Error - {str(e)}"
        )
# CLOUDFLARE
def generate_cf(prompt):

    platform = "Cloudflare"

    try:

        if not CF_ACCOUNT_ID or not CF_API_TOKEN:
            raise ValueError(
                "Cloudflare credentials missing"
            )

        url = (
            "https://api.cloudflare.com/client/v4/"
            f"accounts/{CF_ACCOUNT_ID}/"
            "ai/run/"
            "@cf/stabilityai/stable-diffusion-xl-base-1.0"
        )

        headers = {
            "Authorization": f"Bearer {CF_API_TOKEN}"
        }

        payload = {
            "prompt": prompt
        }

        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=120
        )

        print("CF STATUS:", response.status_code)

        if response.status_code != 200:
            print(response.text)

        response.raise_for_status()

        image = Image.open(
            io.BytesIO(response.content)
        ).convert("RGB")

        return (
            platform,
            image,
            f"{platform}: Success"
        )

    except Exception as e:

        return (
            platform,
            create_placeholder(
                f"CF Error\n{str(e)[:40]}"
            ),
            f"{platform}: Error - {str(e)}"
        )
# POLLINATIONS
def generate_pollinations(prompt):

    platform = "Pollinations.ai"

    try:

        encoded_prompt = urllib.parse.quote(prompt)

        url = (
            "https://image.pollinations.ai/prompt/"
            f"{encoded_prompt}"
        )

        response = requests.get(
            url,
            timeout=120,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        print(
            "POLLINATIONS STATUS:",
            response.status_code
        )

        response.raise_for_status()

        content_type = response.headers.get(
            "Content-Type",
            ""
        )

        print(
            "POLLINATIONS CONTENT TYPE:",
            content_type
        )

        # Ensure response is image
        if not content_type.startswith("image/"):

            print("INVALID RESPONSE:")
            print(response.text[:300])

            raise ValueError(
                f"Expected image, got {content_type}"
            )

        image_bytes = io.BytesIO(
            response.content
        )

        try:

            image = Image.open(image_bytes)

            image.verify()

        except Exception:

            raise ValueError(
                "Corrupted or invalid image data"
            )

        image_bytes.seek(0)

        image = Image.open(
            image_bytes
        ).convert("RGB")

        return (
            platform,
            image,
            f"{platform}: Success"
        )

    except Exception as e:

        return (
            platform,
            create_placeholder(
                f"Pollinations Error\n{str(e)[:40]}"
            ),
            f"{platform}: Error - {str(e)}"
        )
# MASTER GENERATOR
def run_all_generators(prompt):

    logs = (
        f"[{time.strftime('%H:%M:%S')}] "
        f"🚀 Starting generation for:\n"
        f"'{prompt}'\n\n"
    )

    placeholder = create_placeholder(
        "Generating..."
    )

    results = [
        placeholder,
        placeholder,
        placeholder,
    ]

    yield tuple(results + [logs])

    adapters = [
        (generate_hf, 0),
        (generate_cf, 1),
        (generate_pollinations, 2),
    ]

    with ThreadPoolExecutor(
        max_workers=3
    ) as executor:

        future_to_idx = {
            executor.submit(func, prompt): idx
            for func, idx in adapters
        }

        for future in as_completed(
            future_to_idx
        ):

            idx = future_to_idx[future]

            try:

                platform, img, log_msg = (
                    future.result()
                )

                results[idx] = img

                logs += (
                    f"[{time.strftime('%H:%M:%S')}] "
                    f"✅ {log_msg}\n"
                )

            except Exception as e:

                results[idx] = create_placeholder(
                    "Critical Error"
                )

                logs += (
                    f"[{time.strftime('%H:%M:%S')}] "
                    f"❌ {str(e)}\n"
                )

            yield tuple(results + [logs])

    logs += (
        f"\n[{time.strftime('%H:%M:%S')}] "
        f"🎉 All generations completed."
    )

    yield tuple(results + [logs])

# UI
with gr.Blocks(
    title="Unified AI Generator"
) as demo:

    gr.Markdown(
        "# 🌌 Unified Text-to-Image Platform"
    )

    gr.Markdown(
        "Parallel image generation across "
        "multiple AI providers."
    )

    with gr.Row():

        # LEFT PANEL
        with gr.Column(scale=1):

            prompt_input = gr.Textbox(
                label="Prompt",
                lines=4,
                placeholder=(
                    "A futuristic neon cyberpunk city..."
                )
            )

            generate_btn = gr.Button(
                "🚀 Generate Images",
                variant="primary"
            )

            logs_output = gr.Textbox(
                label="Logs",
                lines=20,
                interactive=False,
                value="Waiting for prompt..."
            )

        # RIGHT PANEL
        with gr.Column(scale=3):

            with gr.Row():

                img_hf = gr.Image(
                    label="Hugging Face"
                )

                img_cf = gr.Image(
                    label="Cloudflare"
                )

                img_pollinations = gr.Image(
                    label="Pollinations.ai"
                )

    outputs = [
        img_hf,
        img_cf,
        img_pollinations,
        logs_output,
    ]

    generate_btn.click(
        fn=run_all_generators,
        inputs=prompt_input,
        outputs=outputs,
        concurrency_limit=None,
    )
# MAIN

if __name__ == "__main__":

    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False
    )