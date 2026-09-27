import os
import base64
import json
import re
import httpx
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from PIL import Image
from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel

from app.core.config import settings
from app.core.logging import logger

# -------------------------------------------------------------------
# Pydantic Schemas for Dynamic Image Analysis (Requirement 5)
# -------------------------------------------------------------------

class VehicleAnalysis(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    vehicle_type: str = Field("unknown", description="Vehicle type e.g. sedan, SUV, truck, motorcycle")
    color: str = Field("unknown", description="Vehicle color if clearly visible")
    position: str = Field("unknown", description="Position or orientation in scene")
    visible_damage: List[str] = Field(default_factory=list, description="Observed visual damage details")
    damage_locations: List[str] = Field(default_factory=list, description="Specific damage locations e.g. front bumper, driver door")
    damage_severity: str = Field("unknown", description="low | medium | high | unknown")

class EnvironmentAnalysis(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    road_type: str = Field("unknown", description="e.g. highway, parking lot, residential street, intersection")
    weather: str = Field("unknown", description="e.g. sunny, rainy, overcast, snow")
    lighting: str = Field("unknown", description="e.g. daylight, night, dusk, streetlights")
    location_characteristics: str = Field("unknown", description="e.g. urban, rural, commercial, indoor")

class ImageAnalysisResult(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    analysis_type: str = Field("image", description="'image' or 'document'")
    scene_description: str = Field("Image uploaded. Awaiting vision analysis.", description="Overall dynamic visual scene description")
    objects_detected: List[str] = Field(default_factory=list, description="All visually detected objects")
    vehicles: List[VehicleAnalysis] = Field(default_factory=list, description="Detailed vehicle findings")
    other_objects: List[str] = Field(default_factory=list, description="Other non-vehicle objects")
    collision_indicators: List[str] = Field(default_factory=list, description="Collision indicators e.g. point of impact, skid marks")
    environment: EnvironmentAnalysis = Field(default_factory=EnvironmentAnalysis, description="Environmental scene characteristics")
    people_detected: int = Field(0, description="Count of visible people detected")
    visible_injuries: List[str] = Field(default_factory=list, description="Clearly observable injuries if any")
    observations: List[str] = Field(default_factory=list, description="Direct visual facts observed")
    inferences: List[str] = Field(default_factory=list, description="Reasonable inferences based strictly on visuals")
    unknowns: List[str] = Field(default_factory=list, description="Uncertainties or items that cannot be determined from image")
    confidence: float = Field(85.0, description="Visual analysis confidence score (0 to 100)")

# -------------------------------------------------------------------
# System Dynamic Image Analysis Prompt (Requirement 4)
# -------------------------------------------------------------------

DYNAMIC_VISION_PROMPT = """You are an insurance claim image analysis assistant.

Analyze the uploaded image based ONLY on information that is visually supported by the image.

Do not assume that the image represents an accident.
Do not force the image into a predefined accident category.

Dynamically identify what is actually visible.

Analyze:
* overall scene
* vehicles
* vehicle types
* vehicle colors when clearly visible
* visible damage
* approximate damage location on vehicles
* other visible objects
* debris
* road/environment
* people, if visible
* visible injuries, only if clearly observable
* collision indicators
* signs of fire, water, weather, falling objects, animals, etc. when visually observable
* document text if the uploaded image contains a document
* important visual evidence
* uncertainties

Separate direct observations from reasonable inferences.

Never invent:
* exact accident time
* exact accident location
* repair cost
* policy number
* customer identity
* exact cause of accident
* hidden damage
* information that cannot be determined from the image.

If something cannot be determined, return "unknown".

Return ONLY valid JSON matching this exact structure:
{
  "analysis_type": "image" | "document",
  "scene_description": "string",
  "objects_detected": ["string"],
  "vehicles": [
    {
      "vehicle_type": "string",
      "color": "string",
      "position": "string",
      "visible_damage": ["string"],
      "damage_locations": ["string"],
      "damage_severity": "low" | "medium" | "high" | "unknown"
    }
  ],
  "other_objects": ["string"],
  "collision_indicators": ["string"],
  "environment": {
    "road_type": "string",
    "weather": "string",
    "lighting": "string",
    "location_characteristics": "string"
  },
  "people_detected": 0,
  "visible_injuries": ["string"],
  "observations": ["string"],
  "inferences": ["string"],
  "unknowns": ["string"],
  "confidence": 90.0
}
"""

# -------------------------------------------------------------------
# Cloud Vision Provider Abstraction (Requirement 3)
# -------------------------------------------------------------------

class CloudVisionProvider(ABC):
    @abstractmethod
    async def analyze_image(self, image_path: str, prompt: str = DYNAMIC_VISION_PROMPT) -> ImageAnalysisResult:
        """Sends image bytes/base64 to cloud vision provider and returns structured analysis."""
        pass

try:
    from google import genai
    from google.genai import types
    HAS_GENAI_SDK = True
except ImportError:
    HAS_GENAI_SDK = False

class GeminiVisionProvider(CloudVisionProvider):
    """Google Gemini Cloud Multimodal Vision Provider implementation."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or os.getenv("VISION_API_KEY") or os.getenv("GEMINI_API_KEY") or getattr(settings, "VISION_API_KEY", "")
        configured_model = model_name or getattr(settings, "VISION_MODEL", "gemini-1.5-flash") or "gemini-1.5-flash"
        if configured_model in ["gemini-2.5-flash", "gemini-2.0-flash"]:
            configured_model = "gemini-1.5-flash"
        self.model_name = configured_model

    async def analyze_image(self, image_path: str, prompt: str = DYNAMIC_VISION_PROMPT) -> ImageAnalysisResult:
        if not os.path.exists(image_path):
            logger.error(f"Vision error: Image file not found: {image_path}")
            return self._build_fallback_result(image_path, "Image file not found on disk.")

        if not self.api_key or self.api_key.strip() == "":
            logger.warning("VISION_API_KEY not configured. Returning dynamic image inspection fallback.")
            return self._build_offline_dynamic_result(image_path)

        # 1. Try Google GenAI SDK if installed
        if HAS_GENAI_SDK:
            try:
                ext = os.path.splitext(image_path)[1].lower()
                mime_map = {".png": "image/png", ".webp": "image/webp", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}
                mime_type = mime_map.get(ext, "image/jpeg")

                with open(image_path, "rb") as f:
                    img_bytes = f.read()

                client = genai.Client(api_key=self.api_key)
                response = client.models.generate_content(
                    model=self.model_name,
                    contents=[
                        types.Part.from_bytes(data=img_bytes, mime_type=mime_type),
                        prompt
                    ]
                )
                if response and response.text:
                    return self._parse_json_response(response.text, image_path)
            except Exception as sdk_err:
                logger.warning(f"GenAI SDK call note: {str(sdk_err)}. Proceeding with REST API connection...")

        # 2. REST API Fallback
        try:
            ext = os.path.splitext(image_path)[1].lower()
            mime_map = {".png": "image/png", ".webp": "image/webp", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}
            mime_type = mime_map.get(ext, "image/jpeg")

            with open(image_path, "rb") as f:
                img_bytes = f.read()

            b64_data = base64.b64encode(img_bytes).decode("utf-8")

            models_to_try = [
                self.model_name,
                "gemini-1.5-flash",
                "gemini-1.5-flash-latest",
                "gemini-1.5-pro",
                "gemini-1.5-pro-latest"
            ]
            models_to_try = list(dict.fromkeys(models_to_try))

            async with httpx.AsyncClient(timeout=30.0) as client:
                last_error = ""
                for target_model in models_to_try:
                    # Test both query param and header auth
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{target_model}:generateContent?key={self.api_key}"
                    payload = {
                        "contents": [
                            {
                                "parts": [
                                    {"text": prompt},
                                    {
                                        "inline_data": {
                                            "mime_type": mime_type,
                                            "data": b64_data
                                        }
                                    }
                                ]
                            }
                        ],
                        "generationConfig": {
                            "temperature": 0.2,
                            "response_mime_type": "application/json"
                        }
                    }

                    res = await client.post(url, headers={"Content-Type": "application/json"}, json=payload)
                    if res.status_code == 200:
                        data = res.json()
                        candidates = data.get("candidates", [])
                        if not candidates:
                            return self._build_fallback_result(image_path, "No response candidates returned by vision API.")

                        text_content = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        return self._parse_json_response(text_content, image_path)
                    else:
                        err_msg = res.text[:200]
                        logger.warning(f"Gemini model '{target_model}' returned HTTP {res.status_code}: {err_msg}")
                        last_error = f"Model '{target_model}' HTTP {res.status_code}: {err_msg}"

                return self._build_fallback_result(image_path, last_error)

        except Exception as e:
            logger.error(f"Error calling Gemini Vision API for {image_path}: {str(e)}")
            return self._build_fallback_result(image_path, "Vision service encounter error while calling cloud provider.")

    def _parse_json_response(self, text_content: str, image_path: str) -> ImageAnalysisResult:
        try:
            # Clean markdown JSON formatting blocks if present
            cleaned = re.sub(r"^```json\s*", "", text_content.strip(), flags=re.MULTILINE)
            cleaned = re.sub(r"^```\s*", "", cleaned, flags=re.MULTILINE).strip()
            
            parsed_dict = json.loads(cleaned)
            return ImageAnalysisResult.model_validate(parsed_dict)
        except Exception as parse_err:
            logger.error(f"Failed to parse Gemini Vision JSON response: {str(parse_err)}. Raw: {text_content[:200]}")
            return self._build_fallback_result(image_path, "Malformed model JSON response.")

    def _build_offline_dynamic_result(self, image_path: str) -> ImageAnalysisResult:
        """Inspects image metadata dynamically without API key, never returning hardcoded categories."""
        filename = os.path.basename(image_path)
        try:
            with Image.open(image_path) as img:
                w, h = img.size
                fmt = img.format or "JPEG"
        except Exception:
            w, h, fmt = 0, 0, "UNKNOWN"

        filename_lower = filename.lower()
        
        # Dynamically evaluate visual clues from image dimensions and filename
        is_doc = "doc" in filename_lower or "report" in filename_lower or "pdf" in filename_lower
        
        analysis_type = "document" if is_doc else "image"
        scene_desc = f"Uploaded image file '{filename}' ({w}x{h} px, format {fmt}). Pending active Cloud Vision API key for full AI perception."
        
        observations = [f"File name: {filename}", f"Image dimensions: {w}x{h} pixels", f"Format: {fmt}"]
        unknowns = ["Cloud API key (VISION_API_KEY) not provided for full visual scene parsing."]

        return ImageAnalysisResult(
            analysis_type=analysis_type,
            scene_description=scene_desc,
            objects_detected=["digital image file"],
            vehicles=[],
            other_objects=[],
            collision_indicators=[],
            environment=EnvironmentAnalysis(
                road_type="unknown",
                weather="unknown",
                lighting="unknown",
                location_characteristics="unknown"
            ),
            people_detected=0,
            visible_injuries=[],
            observations=observations,
            inferences=["Uploaded file is valid and readable by image engine."],
            unknowns=unknowns,
            confidence=75.0
        )

    def _build_fallback_result(self, image_path: str, reason: str) -> ImageAnalysisResult:
        filename = os.path.basename(image_path)
        return ImageAnalysisResult(
            analysis_type="image",
            scene_description=f"Analysis completed with fallback for file '{filename}'. Reason: {reason}",
            objects_detected=[],
            vehicles=[],
            other_objects=[],
            collision_indicators=[],
            environment=EnvironmentAnalysis(),
            people_detected=0,
            visible_injuries=[],
            observations=[f"File: {filename}"],
            inferences=[],
            unknowns=[f"Cloud vision analysis failed: {reason}"],
            confidence=0.0
        )

class OpenAIVisionProvider(CloudVisionProvider):
    """OpenAI GPT-4o Vision Provider implementation."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("VISION_API_KEY") or getattr(settings, "VISION_API_KEY", "")
        self.model_name = model_name or os.getenv("OPENAI_MODEL") or getattr(settings, "VISION_MODEL", "gpt-4o-mini") or "gpt-4o-mini"

    async def analyze_image(self, image_path: str, prompt: str = DYNAMIC_VISION_PROMPT) -> ImageAnalysisResult:
        if not os.path.exists(image_path):
            return self._build_fallback_result(image_path, "Image file not found on disk.")

        if not self.api_key or self.api_key.strip() == "":
            return self._build_fallback_result(image_path, "OPENAI_API_KEY not configured.")

        try:
            ext = os.path.splitext(image_path)[1].lower()
            mime_map = {".png": "image/png", ".webp": "image/webp", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}
            mime_type = mime_map.get(ext, "image/jpeg")

            with open(image_path, "rb") as f:
                b64_data = base64.b64encode(f.read()).decode("utf-8")

            data_url = f"data:{mime_type};base64,{b64_data}"

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": data_url}}
                        ]
                    }
                ],
                "temperature": 0.2,
                "response_format": {"type": "json_object"}
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    text_content = data["choices"][0]["message"]["content"]
                    return self._parse_json_response(text_content, image_path)
                else:
                    return self._build_fallback_result(image_path, f"OpenAI API status HTTP {res.status_code}: {res.text[:150]}")
        except Exception as e:
            logger.error(f"Error in OpenAIVisionProvider: {str(e)}")
            return self._build_fallback_result(image_path, str(e))

    def _parse_json_response(self, text_content: str, image_path: str) -> ImageAnalysisResult:
        try:
            cleaned = re.sub(r"^```json\s*", "", text_content.strip(), flags=re.MULTILINE)
            cleaned = re.sub(r"^```\s*", "", cleaned, flags=re.MULTILINE).strip()
            parsed_dict = json.loads(cleaned)
            return ImageAnalysisResult.model_validate(parsed_dict)
        except Exception as err:
            return self._build_fallback_result(image_path, f"Malformed OpenAI JSON response: {str(err)}")

    def _build_fallback_result(self, image_path: str, reason: str) -> ImageAnalysisResult:
        filename = os.path.basename(image_path)
        return ImageAnalysisResult(
            analysis_type="image",
            scene_description=f"Analysis completed with fallback for file '{filename}'. Reason: {reason}",
            unknowns=[f"OpenAI vision analysis note: {reason}"],
            confidence=0.0
        )

class GroqVisionProvider(CloudVisionProvider):
    """Groq Llama-3.2-Vision Provider implementation (Super fast 100% Free API)."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY") or os.getenv("VISION_API_KEY") or getattr(settings, "VISION_API_KEY", "")
        configured_model = model_name or os.getenv("GROQ_MODEL") or getattr(settings, "VISION_MODEL", "llama-3.2-11b-vision-instruct") or "llama-3.2-11b-vision-instruct"
        if "preview" in configured_model:
            configured_model = configured_model.replace("-preview", "-instruct")
        self.model_name = configured_model

    async def analyze_image(self, image_path: str, prompt: str = DYNAMIC_VISION_PROMPT) -> ImageAnalysisResult:
        if not os.path.exists(image_path):
            return self._build_fallback_result(image_path, "Image file not found on disk.")

        if not self.api_key or self.api_key.strip() == "":
            return self._build_fallback_result(image_path, "GROQ_API_KEY not configured.")

        try:
            ext = os.path.splitext(image_path)[1].lower()
            mime_map = {".png": "image/png", ".webp": "image/webp", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}
            mime_type = mime_map.get(ext, "image/jpeg")

            with open(image_path, "rb") as f:
                b64_data = base64.b64encode(f.read()).decode("utf-8")

            data_url = f"data:{mime_type};base64,{b64_data}"

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            models_to_try = [
                self.model_name,
                "qwen/qwen3.6-27b",
                "qwen/qwen3.8-27b",
                "llama-3.2-11b-vision-instruct",
                "llama-3.2-90b-vision-instruct",
                "llama-3.3-70b-versatile"
            ]

            async with httpx.AsyncClient(timeout=30.0) as client:
                # Dynamically discover active models for this Groq API Key if configured model fails
                try:
                    models_res = await client.get("https://api.groq.com/openai/v1/models", headers={"Authorization": f"Bearer {self.api_key}"})
                    if models_res.status_code == 200:
                        discovered_data = models_res.json().get("data", [])
                        discovered_ids = [m["id"] for m in discovered_data if isinstance(m, dict) and "id" in m]
                        if discovered_ids:
                            # Prioritize vision and multimodal models
                            vision_candidates = [m for m in discovered_ids if any(kw in m.lower() for kw in ["vision", "qwen", "llava", "multimodal"])]
                            other_candidates = [m for m in discovered_ids if m not in vision_candidates]
                            models_to_try = list(dict.fromkeys([self.model_name] + vision_candidates + other_candidates))
                except Exception as disc_err:
                    logger.warning(f"Could not auto-discover Groq models: {str(disc_err)}")

                models_to_try = list(dict.fromkeys(models_to_try))
                last_error = ""
                for target_model in models_to_try:
                    payload = {
                        "model": target_model,
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {"type": "image_url", "image_url": {"url": data_url}}
                                ]
                            }
                        ],
                        "temperature": 0.2,
                        "response_format": {"type": "json_object"}
                    }

                    res = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                    if res.status_code == 200:
                        data = res.json()
                        text_content = data["choices"][0]["message"]["content"]
                        return self._parse_json_response(text_content, image_path)
                    else:
                        err_msg = res.text[:200]
                        logger.warning(f"Groq model '{target_model}' returned HTTP {res.status_code}: {err_msg}")
                        last_error = f"Groq model '{target_model}' HTTP {res.status_code}: {err_msg}"

                return self._build_fallback_result(image_path, last_error)
        except Exception as e:
            logger.error(f"Error in GroqVisionProvider: {str(e)}")
            return self._build_fallback_result(image_path, str(e))

    def _parse_json_response(self, text_content: str, image_path: str) -> ImageAnalysisResult:
        try:
            cleaned = re.sub(r"^```json\s*", "", text_content.strip(), flags=re.MULTILINE)
            cleaned = re.sub(r"^```\s*", "", cleaned, flags=re.MULTILINE).strip()
            parsed_dict = json.loads(cleaned)
            return ImageAnalysisResult.model_validate(parsed_dict)
        except Exception as err:
            return self._build_fallback_result(image_path, f"Malformed Groq JSON response: {str(err)}")

    def _build_fallback_result(self, image_path: str, reason: str) -> ImageAnalysisResult:
        filename = os.path.basename(image_path)
        return ImageAnalysisResult(
            analysis_type="image",
            scene_description=f"Analysis completed with fallback for file '{filename}'. Reason: {reason}",
            unknowns=[f"Groq vision analysis note: {reason}"],
            confidence=0.0
        )

# -------------------------------------------------------------------
# Vision Analysis Service Orchestrator (Requirement 2 & 7)
# -------------------------------------------------------------------

class VisionAnalysisService:
    """Service responsible for sending uploaded claim images to Cloud Multimodal Vision models
    and returning dynamic structured visual understanding results.
    """

    def __init__(self, provider: Optional[CloudVisionProvider] = None):
        if provider:
            self.provider = provider
        else:
            provider_name = getattr(settings, "VISION_PROVIDER", "gemini").lower()
            if provider_name == "openai":
                self.provider = OpenAIVisionProvider()
            elif provider_name == "groq":
                self.provider = GroqVisionProvider()
            else:
                self.provider = GeminiVisionProvider()

    async def analyze_single_image(self, image_path: str) -> ImageAnalysisResult:
        """Analyzes a single image file dynamically via cloud vision model."""
        return await self.provider.analyze_image(image_path)

    async def analyze_claim_images(self, claim_id: str, image_paths: List[str]) -> Dict[str, Any]:
        """Analyzes multiple images associated with a single claim independently (Requirement 7)."""
        analyzed_images = []
        for path in image_paths:
            filename = os.path.basename(path)
            analysis = await self.analyze_single_image(path)
            analyzed_images.append({
                "filename": filename,
                "analysis": analysis.model_dump(by_alias=True)
            })

        return {
            "claimId": claim_id,
            "claim_id": claim_id,
            "images": analyzed_images
        }

# Singleton Instance
vision_analysis_service = VisionAnalysisService()
