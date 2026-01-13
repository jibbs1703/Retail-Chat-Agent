# Retail Product Agent — Multimodal Product Discovery

An AI-powered conversational shopping assistant that helps users discover products via
**natural-language description** and/or **image upload**. 

Search using text, photos, or both to find relevant products instantly—no endless catalog
browsing required.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        MULTIMODAL PRODUCT DISCOVERY                             │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                              INITIALIZATION                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────────────┐  │
│  │   CLIP Model    │    │  CrossEncoder   │    │      Vector Database        │  │
│  │  (ViT-L/14)     │    │  (MS-MARCO)     │    │   (Cosine Similarity)       │  │
│  └─────────────────┘    └─────────────────┘    └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Tech Stack

- **Frontend**: React
- **Backend**: Python FastAPI
- **Embeddings**: OpenCLIP (image & text), BLIP (auto-captioning), SentenceTransformers
- **Re-ranking**: CrossEncoder

## Key Features

- **Multimodal search**: Search with text and/or images
- **Fast & scalable**: Vector Database indexing for 100K+ product catalogs
- **High-quality embeddings**: OpenCLIP + BLIP models
- **Smart ranking**: CrossEncoder re-ranking for better relevance
