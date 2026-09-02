#!/usr/bin/env python3
"""
Model Weights Fetch & Integrity Verification Utility
ENUM Talent Intelligence Platform

Downloads required GGUF and ONNX models from verified mirrors and verifies
cryptographic SHA-256 checksums before deploying them to the runtime volume.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
import tempfile
import urllib.request
from pathlib import Path
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("model_fetcher")

CHUNK_SIZE = 1024 * 1024  # 1MB buffer


def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file with streaming chunks to minimize memory usage."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            hasher.update(chunk)
    return hasher.hexdigest()


def load_manifest(manifest_path: Path) -> list[dict[str, Any]]:
    """Load and validate the model weights manifest."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found at {manifest_path}")
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("models", [])


def download_file(url: str, dest_path: Path, expected_hash: str) -> bool:
    """Download a file atomically to a temporary location, verify checksum, and move to destination."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    temp_fd, temp_path_str = tempfile.mkstemp(
        dir=dest_path.parent, prefix=f".{dest_path.name}.", suffix=".tmp"
    )
    temp_path = Path(temp_path_str)
    os.close(temp_fd)

    try:
        logger.info("Downloading %s -> %s", url, dest_path.name)
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "ENUM-Model-Fetcher/1.0"},
        )

        with urllib.request.urlopen(req) as response, open(temp_path, "wb") as out_file:
            total_size = int(response.headers.get("Content-Length", 0))
            downloaded = 0
            while chunk := response.read(CHUNK_SIZE):
                out_file.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    pct = (downloaded / total_size) * 100
                    print(
                        f"\r  Progress: {pct:.1f}% ({downloaded / (1024*1024):.1f}/{total_size / (1024*1024):.1f} MB)",
                        end="",
                        flush=True,
                    )
            print()

        logger.info("Verifying SHA-256 checksum for %s...", dest_path.name)
        computed_hash = calculate_sha256(temp_path)

        if computed_hash.lower() != expected_hash.lower():
            logger.error(
                "Checksum mismatch for %s!\n  Expected: %s\n  Actual:   %s",
                dest_path.name,
                expected_hash,
                computed_hash,
            )
            temp_path.unlink(missing_ok=True)
            return False

        temp_path.replace(dest_path)
        logger.info("Successfully verified and saved %s", dest_path.name)
        return True

    except Exception as e:
        logger.error("Download failed for %s: %s", dest_path.name, e)
        temp_path.unlink(missing_ok=True)
        return False


def verify_model(model_dir: Path, model_info: dict[str, Any]) -> bool:
    """Check whether a model file exists and passes SHA-256 integrity validation."""
    name = model_info["name"]
    expected_hash = model_info["sha256"]
    file_path = model_dir / name

    if not file_path.exists():
        logger.warning("[MISSING] %s not found in %s", name, model_dir)
        return False

    computed_hash = calculate_sha256(file_path)
    if computed_hash.lower() == expected_hash.lower():
        logger.info("[VALID] %s passed SHA-256 checksum", name)
        return True
    else:
        logger.error(
            "[CORRUPT] %s failed checksum!\n  Expected: %s\n  Actual:   %s",
            name,
            expected_hash,
            computed_hash,
        )
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch and verify model weights for ENUM platform.")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "model-weights" / "manifest.json",
        help="Path to manifest.json",
    )
    parser.add_argument(
        "--model-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "model-weights",
        help="Directory where models should be stored",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify existing files on disk without downloading missing ones",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Display models to be downloaded without performing network requests",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-download even if model already exists and is valid",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Fetch/verify a specific model name only",
    )

    args = parser.parse_args()
    manifest_models = load_manifest(args.manifest)

    if args.model:
        manifest_models = [m for m in manifest_models if m["name"] == args.model]
        if not manifest_models:
            logger.error("Model '%s' not found in manifest", args.model)
            return 1

    logger.info("Loaded %d model definitions from %s", len(manifest_models), args.manifest.name)

    all_passed = True
    for model in manifest_models:
        name = model["name"]
        file_path = args.model_dir / name
        expected_hash = model["sha256"]

        if args.verify_only:
            if not verify_model(args.model_dir, model):
                all_passed = False
            continue

        if args.dry_run:
            status = "FOUND" if file_path.exists() else "MISSING"
            print(f"[{status}] {name} ({model['task']}) -> {model['url']}")
            continue

        if file_path.exists() and not args.force:
            if verify_model(args.model_dir, model):
                logger.info("Skipping %s (already valid). Use --force to re-download.", name)
                continue
            else:
                logger.warning("Existing %s is invalid, re-downloading...", name)

        success = download_file(model["url"], file_path, expected_hash)
        if not success:
            all_passed = False

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
