"""AI content generation utilities using MistralAI and OpenAI."""

import os
import json
import hashlib
import logging
import time
import requests

from flask import current_app

logger = logging.getLogger(__name__)


def generate_article(prompt):
    """Generate a health blog article using MistralAI.

    Returns a dict with title, excerpt, content, tags, and reading_time.
    """
    api_key = current_app.config.get("MISTRAL_API_KEY", "")
    if not api_key:
        raise ValueError("MISTRAL_API_KEY is not configured")

    system_prompt = (
        "You are an expert health and wellness writer for Contemporary Hippie, "
        "a modern health blog. Write engaging, well-researched articles that are "
        "informative yet concise. Use a warm, approachable tone. Include practical "
        "tips readers can apply immediately. Structure articles with clear headings "
        "using markdown (## for sections). Keep articles between 800-1200 words."
    )

    user_prompt = (
        f"Write a complete blog article about: {prompt}\n\n"
        "Respond in JSON format with these fields:\n"
        '- "title": An engaging, SEO-friendly title\n'
        '- "excerpt": A compelling 1-2 sentence summary (max 200 chars)\n'
        '- "content": The full article in markdown format\n'
        '- "tags": An array of 3-5 relevant tags\n'
        '- "meta_description": SEO meta description (max 160 chars)\n'
        '- "reading_time": Estimated reading time in minutes\n'
    )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "mistral-small-latest",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.7,
        "response_format": {"type": "json_object"},
    }

    resp = requests.post(
        "https://api.mistral.ai/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()

    content_str = data["choices"][0]["message"]["content"]
    article = json.loads(content_str)

    return {
        "title": article.get("title", "Untitled Article"),
        "excerpt": article.get("excerpt", ""),
        "content": article.get("content", ""),
        "tags": article.get("tags", []),
        "meta_description": article.get("meta_description", ""),
        "reading_time": article.get("reading_time", 5),
    }


def generate_images(prompt, count=3):
    """Generate images using OpenAI DALL-E based on a prompt.

    Returns a list of file paths for saved images.
    """
    api_key = current_app.config.get("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not configured")

    image_prompt = (
        f"A beautiful, modern, minimalist health and wellness photograph: {prompt}. "
        "Clean, bright, professional photography style. No text overlay."
    )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "dall-e-3",
        "prompt": image_prompt,
        "n": 1,
        "size": "1792x1024",
        "quality": "standard",
    }

    saved_paths = []
    upload_dir = os.path.join(current_app.static_folder, "uploads", "posts")
    os.makedirs(upload_dir, exist_ok=True)

    for i in range(count):
        try:
            resp = requests.post(
                "https://api.openai.com/v1/images/generations",
                headers=headers,
                json=payload,
                timeout=90,
            )
            resp.raise_for_status()
            data = resp.json()

            image_url = data["data"][0]["url"]

            # Download and save the image
            img_resp = requests.get(image_url, timeout=60)
            img_resp.raise_for_status()

            hash_input = f"{prompt}_{i}_{time.time()}"
            filename = hashlib.md5(hash_input.encode()).hexdigest()[:12] + ".png"
            filepath = os.path.join(upload_dir, filename)

            with open(filepath, "wb") as f:
                f.write(img_resp.content)

            saved_paths.append(f"uploads/posts/{filename}")
            logger.info("Generated image %d: %s", i + 1, filename)
        except Exception as e:
            logger.error("Image generation %d failed: %s", i + 1, str(e))
            saved_paths.append("")

    return saved_paths
