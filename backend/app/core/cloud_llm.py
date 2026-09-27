import os
import json
import re
import httpx
from typing import Optional, Dict, Any
from app.core.config import settings
from app.core.logging import logger

def _get_api_key() -> str:
    if settings.LLM_API_KEY:
        return settings.LLM_API_KEY
    if settings.VISION_API_KEY:
        return settings.VISION_API_KEY
    return (
        os.getenv("GEMINI_API_KEY") or 
        os.getenv("LLM_API_KEY") or 
        os.getenv("VISION_API_KEY") or 
        os.getenv("OPENAI_API_KEY") or 
        os.getenv("GROQ_API_KEY") or 
        ""
    )

async def generate_text(
    prompt: str,
    system_prompt: Optional[str] = None,
    temperature: float = 0.2
) -> str:
    """
    Generate text using cloud LLM provider (Gemini / OpenAI / Groq).
    Auto-detects provider based on API key prefix if needed.
    """
    provider = (settings.LLM_PROVIDER or "gemini").lower()
    api_key = _get_api_key()

    if not api_key:
        logger.warning("No LLM API Key provided. Returning structured cloud fallback response.")
        return f"[Cloud LLM Notice: API key missing for {provider}] Response based on input context:\n\n{prompt[:300]}..."

    # Auto-detect provider by key format if applicable
    if api_key.startswith("gsk_"):
        provider = "groq"
    elif api_key.startswith("AIza"):
        provider = "gemini"
    elif api_key.startswith("sk-"):
        provider = "openai"

    if provider == "groq":
        return await _call_groq_text(prompt, system_prompt, temperature, api_key)
    elif provider == "openai":
        return await _call_openai_text(prompt, system_prompt, temperature, api_key)
    else:
        return await _call_gemini_text(prompt, system_prompt, temperature, api_key)

async def generate_json(
    prompt: str,
    system_prompt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate structured JSON response using cloud LLM provider.
    """
    json_prompt = f"{prompt}\n\nIMPORTANT: Respond ONLY with valid JSON, no additional prose or code fence formatting."
    text = await generate_text(json_prompt, system_prompt=system_prompt, temperature=0.1)
    
    # Clean text from markdown code fences if present
    cleaned = re.sub(r"^```json\s*", "", text.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r"^```\s*", "", cleaned, flags=re.MULTILINE).strip()
    
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse cloud LLM JSON output: {e}. Output was: {text[:200]}")
        return {"error": "Failed to parse JSON response", "raw_output": text}

async def _call_groq_text(
    prompt: str,
    system_prompt: Optional[str],
    temperature: float,
    api_key: str
) -> str:
    aliases = {
        "llama-3.2-11b-vision-instruct": "llama-3.2-11b-vision-preview",
        "llama-3.2-90b-vision-instruct": "llama-3.2-90b-vision-preview",
        "llama-3.2-11b": "llama-3.2-11b-vision-preview",
    }

    valid_groq_models = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "llama-3.2-11b-vision-preview",
        "llama-3.2-90b-vision-preview",
        "llama3-70b-8192",
        "llama3-8b-8192",
        "mixtral-8x7b-32768",
        "gemma2-9b-it",
        "deepseek-r1-distill-llama-70b"
    ]

    models_to_try = []

    # Map user or env requested model if valid for Groq
    user_configured = settings.LLM_MODEL or settings.VISION_MODEL or ""
    mapped = aliases.get(user_configured, user_configured)
    if mapped in valid_groq_models:
        models_to_try.append(mapped)

    for m in valid_groq_models:
        if m not in models_to_try:
            models_to_try.append(m)

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    async with httpx.AsyncClient(timeout=10.0) as client:
        # Dynamic model discovery
        try:
            m_res = await client.get("https://api.groq.com/openai/v1/models", headers={"Authorization": f"Bearer {api_key}"})
            if m_res.status_code == 200:
                disc_data = m_res.json().get("data", [])
                disc_ids = [m["id"] for m in disc_data if isinstance(m, dict) and "id" in m]
                if disc_ids:
                    # Prioritize versatile text models and requested model
                    versatile = [m for m in disc_ids if any(kw in m.lower() for kw in ["versatile", "instant", "8b", "70b"])]
                    others = [m for m in disc_ids if m not in versatile]
                    ordered_disc = versatile + others
                    if mapped in disc_ids:
                        ordered_disc = [mapped] + [m for m in ordered_disc if m != mapped]
                    models_to_try = ordered_disc
        except Exception as disc_err:
            logger.warning(f"Could not auto-discover Groq models: {disc_err}")
        first_error = ""
        last_error = ""
        for model in models_to_try:
            try:
                res = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": messages,
                        "temperature": temperature
                    }
                )
                if res.status_code == 200:
                    data = res.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    err_detail = f"Model '{model}' HTTP {res.status_code}: {res.text[:200]}"
                    if not first_error:
                        first_error = err_detail
                    last_error = err_detail
                    logger.warning(f"Groq API call to {model} returned {res.status_code}: {res.text[:200]}")
                    if res.status_code in (401, 403):
                        # Invalid API Key or Unauthorized - stop retrying
                        break
            except Exception as e:
                err_detail = f"Model '{model}' exception: {str(e)}"
                if not first_error:
                    first_error = err_detail
                last_error = err_detail
                logger.error(f"Error calling Groq API {model}: {e}")

        # Check if Gemini key is available as secondary cloud fallback
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key and not gemini_key.startswith("gsk_"):
            logger.info("Attempting Gemini cloud fallback after Groq error...")
            try:
                res = await _call_gemini_text(prompt, system_prompt, temperature, gemini_key)
                if res and not res.startswith("[Cloud LLM fallback"):
                    return res
            except Exception:
                pass

        return f"[Groq Cloud fallback due to API error: {first_error or last_error}]"

async def _call_gemini_text(
    prompt: str,
    system_prompt: Optional[str],
    temperature: float,
    api_key: str
) -> str:
    models_to_try = [
        settings.LLM_MODEL or "gemini-1.5-flash",
        "gemini-1.5-flash",
        "gemini-1.5-flash-latest",
        "gemini-1.5-pro"
    ]
    models_to_try = list(dict.fromkeys(models_to_try))

    contents = []
    if system_prompt:
        contents.append({"role": "user", "parts": [{"text": f"System Context: {system_prompt}"}]})
        contents.append({"role": "model", "parts": [{"text": "Understood. I will follow these guidelines."}]})
    
    contents.append({"role": "user", "parts": [{"text": prompt}]})

    async with httpx.AsyncClient(timeout=30.0) as client:
        last_error = ""
        for model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            payload = {
                "contents": contents,
                "generationConfig": {
                    "temperature": temperature
                }
            }
            try:
                res = await client.post(url, headers={"Content-Type": "application/json"}, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "")
                else:
                    last_error = f"HTTP {res.status_code}: {res.text[:150]}"
                    logger.warning(f"Gemini LLM model {model} returned {last_error}")
            except Exception as ex:
                last_error = str(ex)
                logger.error(f"Error calling Gemini LLM {model}: {ex}")

        return f"[Cloud LLM fallback due to API error: {last_error}]"

async def _call_openai_text(
    prompt: str,
    system_prompt: Optional[str],
    temperature: float,
    api_key: str
) -> str:
    model = settings.LLM_MODEL or "gpt-4o-mini"
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            res = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature
                }
            )
            if res.status_code == 200:
                data = res.json()
                return data["choices"][0]["message"]["content"]
            else:
                logger.warning(f"OpenAI API returned HTTP {res.status_code}: {res.text[:150]}")
                return f"[OpenAI Cloud fallback HTTP {res.status_code}]"
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            return f"[OpenAI Cloud error: {e}]"
