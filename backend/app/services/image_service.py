"""
Image Service for Zaik.

Handles image generation, storage, and retrieval for location images.
"""

import os
import base64
import hashlib
from pathlib import Path
from typing import Optional
import logging

from ..llm import ScoutLLMService, get_llm_service
from ..models.adventure import Location

logger = logging.getLogger(__name__)


class ImageService:
    """Service for managing location images"""

    def __init__(self, storage_dir: str = "data/images", llm_service: Optional[ScoutLLMService] = None):
        """
        Initialize the image service

        Args:
            storage_dir: Directory where images will be stored
            llm_service: LLM service for image generation (defaults to global instance)
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.llm_service = llm_service or get_llm_service()

    def _get_image_filename(self, session_id: str, location_id: str) -> str:
        """
        Generate a unique filename for a session's location image

        Args:
            session_id: Game session ID
            location_id: Location ID

        Returns:
            Filename for the image
        """
        # Create a hash of session + location for unique filename
        hash_input = f"{session_id}_{location_id}"
        hash_digest = hashlib.md5(hash_input.encode()).hexdigest()
        return f"{hash_digest}.png"

    def _get_image_path(self, filename: str) -> Path:
        """Get full path for an image file"""
        return self.storage_dir / filename

    def has_image(self, session_id: str, location_id: str) -> bool:
        """
        Check if an image already exists for this session and location

        Args:
            session_id: Game session ID
            location_id: Location ID

        Returns:
            True if image exists, False otherwise
        """
        filename = self._get_image_filename(session_id, location_id)
        return self._get_image_path(filename).exists()

    def get_image_filename(self, session_id: str, location_id: str) -> Optional[str]:
        """
        Get the filename for an existing image

        Args:
            session_id: Game session ID
            location_id: Location ID

        Returns:
            Filename if image exists, None otherwise
        """
        if self.has_image(session_id, location_id):
            return self._get_image_filename(session_id, location_id)
        return None

    async def generate_location_image(
        self,
        session_id: str,
        location: Location
    ) -> str:
        """
        Generate an image for a location

        Args:
            session_id: Game session ID
            location: Location object to generate image for

        Returns:
            Filename of the generated image
        """
        # Check if image already exists
        existing_filename = self.get_image_filename(session_id, location.id)
        if existing_filename:
            logger.info(f"Image already exists for location {location.id}: {existing_filename}")
            return existing_filename

        # Build detailed prompt for image generation
        prompt = self._build_image_prompt(location)

        try:
            # Generate image using LLM service
            logger.info(f"Generating image for location {location.id}")
            base64_image = await self.llm_service.generate_image(
                prompt=prompt,
                size="1024x1024",
                quality="standard"
            )

            # Save image to disk
            filename = self._get_image_filename(session_id, location.id)
            image_path = self._get_image_path(filename)

            # Decode base64 and save
            image_data = base64.b64decode(base64_image)
            with open(image_path, 'wb') as f:
                f.write(image_data)

            logger.info(f"Image saved: {filename} ({len(image_data)} bytes)")
            return filename

        except Exception as e:
            logger.error(f"Failed to generate image for location {location.id}: {e}")
            raise

    def _build_image_prompt(self, location: Location) -> str:
        """
        Build a detailed image generation prompt from location data

        Args:
            location: Location to build prompt for

        Returns:
            Detailed image generation prompt
        """
        # Start with base description
        prompt_parts = [
            "Create a detailed, atmospheric illustration in a dark fantasy style.",
            f"Scene: {location.name}",
            f"Description: {location.description}",
        ]

        # Add mood if available
        if location.mood:
            prompt_parts.append(f"Mood: {location.mood}")

        # Add style instructions
        prompt_parts.extend([
            "Style: Atmospheric, moody, cinematic lighting",
            "Perspective: Immersive first-person or wide establishing shot",
            "Details: Rich textures, dramatic shadows, evocative ambiance"
        ])

        return " ".join(prompt_parts)

    def read_image(self, filename: str) -> Optional[bytes]:
        """
        Read image file from storage

        Args:
            filename: Name of the image file

        Returns:
            Image bytes if found, None otherwise
        """
        image_path = self._get_image_path(filename)
        if image_path.exists():
            with open(image_path, 'rb') as f:
                return f.read()
        return None


# Global service instance
_image_service: Optional[ImageService] = None


def get_image_service() -> ImageService:
    """Get or create the global image service instance"""
    global _image_service
    if _image_service is None:
        _image_service = ImageService()
    return _image_service
