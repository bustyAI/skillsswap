"""
Embedding generation using sentence-transformers/all-MiniLM-L6-v2.

Memory footprint:
- Model weights: ~90MB on disk, ~400MB in RAM when loaded
- Inference: negligible additional RAM per request

The model is loaded lazily on first use and cached globally.
"""
