"""Retail Product Agent Backend Embedding Services Module."""

import hashlib
import os

import numpy as np
import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

_clip_model = None
_clip_processor = None


def get_device() -> torch.device:
    """Get the appropriate device for model inference."""
    return (
        torch.device("cuda")
        if torch.cuda.is_available()
        else torch.device("mps")
        if torch.backends.mps.is_available()
        else torch.device("cpu")
    )


def load_clip_model() -> CLIPModel:
    """
    Load CLIP model from pretrained checkpoint.

    Returns:
        CLIPModel: Loaded CLIP model on appropriate device.
    """
    global _clip_model
    if _clip_model is None:
        device = get_device()
        model_name = os.getenv("clip_model_name")
        _clip_model = CLIPModel.from_pretrained(model_name).to(device)
    return _clip_model


def load_clip_processor() -> CLIPProcessor:
    """
    Load CLIP processor from pretrained checkpoint.

    Returns:
        CLIPProcessor: Loaded CLIP processor.
    """
    global _clip_processor
    if _clip_processor is None:
        model_name = os.getenv("clip_model_name")
        _clip_processor = CLIPProcessor.from_pretrained(model_name)
    return _clip_processor


def embed_query(query: str | Image.Image) -> np.ndarray:
    """
    Embed either text or image query using CLIP model.

    The function also normalizes the resulting embedding vector.

    Args:
        query (str | Image.Image): Text or image query to embed.

    Returns:
        np.ndarray: Normalized embedding vector.

    Raises:
        ValueError: If query is neither string nor image.
    """
    device = get_device()
    clip_model = load_clip_model()
    clip_processor = load_clip_processor()

    if isinstance(query, Image.Image):
        inputs = clip_processor(images=query, return_tensors="pt").to(device)
        with torch.no_grad():
            emb = clip_model.get_image_features(**inputs)
    elif isinstance(query, str):
        inputs = clip_processor(
            text=[query], return_tensors="pt", padding=True, truncation=True, max_length=77
        ).to(device)
        with torch.no_grad():
            emb = clip_model.get_text_features(**inputs)
    else:
        raise ValueError("Query must be either a string or an image")
    emb = emb / emb.norm(dim=-1, keepdim=True)
    return emb.cpu().numpy()[0].astype("float32")


def generate_vector_id(product_title: str, embedding_type: str, index: int = 0) -> str:
    """Generate a vector ID based on product title."""
    content = f"{product_title}_{embedding_type}_{index}"
    return int(hashlib.sha256(content.encode()).hexdigest(), 16) % (2**63)


print(get_device())
