import os
import json
import re
import httpx
from typing import List, Tuple, Dict, Any, Optional
from pydantic import BaseModel
from app.core.config import settings
from app.core.logging import logger

class ExtractedField(BaseModel):
    field_name: str
    extracted_value: str
    confidence: float  # 0 to 100
    status: str  # 'Verified', 'Extracted', 'Flagged'
    warning: Optional[str] = None

class InformationExtractor:
    """Extracts structured key fields from document text using Dynamic Cloud LLMs (Groq / Gemini / OpenAI)
    for ANY document type (claim forms, police reports, repair estimates, medical bills, invoices),
    falling back to intelligent regex pattern rules if offline.
    """

    @staticmethod
    async def extract_fields_async(raw_text: str, category: str = "Unknown") -> Tuple[List[ExtractedField], List[str]]:
        """Dynamically extracts fields using Cloud LLMs for any document format,
        falling back to pattern rules if offline.
        """
        if not raw_text or not raw_text.strip():
            return InformationExtractor.extract_fields(raw_text, category)

        api_key = getattr(settings, "VISION_API_KEY", "") or os.getenv("GROQ_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
        provider = getattr(settings, "VISION_PROVIDER", "groq").lower()

        if api_key and api_key.strip():
            try:
                llm_fields = await InformationExtractor._call_llm_field_extraction(raw_text, provider, api_key)
                if llm_fields:
                    normalized_fields: List[ExtractedField] = []
                    field_names = set()

                    for f in llm_fields:
                        fname = f.field_name.lower().strip()
                        fval = f.extracted_value.strip()

                        # Normalize policy_number if trapped in generic field name
                        if ("policy" in fname or "policy" in fval.lower()) and "policy_number" not in field_names:
                            fname = "policy_number"
                            pol_match = re.search(r"(?:policy\s*(?:no|num|number|#)?\s*[:|-]?\s*)?([A-Z0-9-]{5,35})", fval, re.IGNORECASE)
                            if pol_match and len(pol_match.group(1)) >= 5:
                                fval = pol_match.group(1).upper()

                        if ("customer" in fname or "insured" in fname) and "name" in fname:
                            fname = "customer_name"
                        elif "email" in fname:
                            fname = "email"
                        elif "phone" in fname or "mobile" in fname or "contact" in fname:
                            fname = "phone"
                        elif ("vehicle" in fname or "registration" in fname or "plate" in fname) and ("number" in fname or "no" in fname or "reg" in fname):
                            fname = "vehicle_number"
                        elif "chassis" in fname or "vin" in fname:
                            fname = "chassis_number"

                        field_names.add(fname)
                        normalized_fields.append(ExtractedField(
                            field_name=fname,
                            extracted_value=fval,
                            confidence=f.confidence,
                            status=f.status
                        ))

                    # If customer_name or policy_number still missing from LLM output, supplement via pattern regex
                    fallback_fields, _ = InformationExtractor.extract_fields(raw_text, category)
                    fb_dict = {fb.field_name: fb for fb in fallback_fields}

                    if "customer_name" not in field_names and "customer_name" in fb_dict:
                        if fb_dict["customer_name"].status != "Flagged":
                            normalized_fields.append(fb_dict["customer_name"])
                            field_names.add("customer_name")

                    if "policy_number" not in field_names and "policy_number" in fb_dict:
                        if fb_dict["policy_number"].status != "Flagged":
                            normalized_fields.append(fb_dict["policy_number"])
                            field_names.add("policy_number")

                    warnings: List[str] = []
                    if "customer_name" not in field_names or any(f.field_name == "customer_name" and f.status == "Flagged" for f in normalized_fields):
                        warnings.append("Customer name missing from document text.")
                    if "policy_number" not in field_names or any(f.field_name == "policy_number" and f.status == "Flagged" for f in normalized_fields):
                        warnings.append("Policy number missing from document text.")

                    return normalized_fields, warnings
            except Exception as err:
                logger.warning(f"Dynamic LLM field extraction note: {str(err)}. Falling back to pattern rules.")

        return InformationExtractor.extract_fields(raw_text, category)

    @staticmethod
    async def _call_llm_field_extraction(raw_text: str, provider: str, api_key: str) -> List[ExtractedField]:
        prompt = f"""You are an expert insurance claim document analyst.
Analyze the following document text and dynamically extract ALL key fields present in the text.

Common fields to look for (extract these and any other relevant fields present):
- customer_name (e.g. Name under Insured Details)
- policy_number (e.g. Policy No)
- claim_number (e.g. Claim No)
- vehicle_number (e.g. Vehicle No / Registration No)
- engine_number (e.g. Engine No)
- chassis_number (e.g. Chassis No)
- incident_date (e.g. Date & Time of Accident/Occurrence)
- place_of_loss / incident_location
- driver_name
- driving_license_no
- claim_amount / estimated_cost_of_repairs
- damaged_parts
- short_description

RULES:
1. Extract ONLY values that are visually/textually present in the document. Do NOT invent data.
2. Format field_name as lower_snake_case (e.g. customer_name, policy_number, vehicle_number, chassis_number, engine_number, driver_name, driving_license_no, claim_amount).
3. Return ONLY a valid JSON array of objects matching this format:
[
  {{
    "field_name": "string",
    "extracted_value": "string",
    "confidence": 98.0,
    "status": "Verified"
  }}
]

Document Text:
\"\"\"
{raw_text[:4000]}
\"\"\"
"""
        async with httpx.AsyncClient(timeout=25.0) as client:
            text_content = ""

            # 1. Groq Provider
            if provider == "groq" or os.getenv("GROQ_API_KEY"):
                key = os.getenv("GROQ_API_KEY") or api_key
                models_to_try = ["qwen/qwen3.6-27b", "llama-3.3-70b-versatile", "llama-3.2-11b-vision-instruct"]
                try:
                    models_res = await client.get("https://api.groq.com/openai/v1/models", headers={"Authorization": f"Bearer {key}"})
                    if models_res.status_code == 200:
                        disc = [m["id"] for m in models_res.json().get("data", []) if isinstance(m, dict) and "id" in m]
                        if disc:
                            models_to_try = list(dict.fromkeys(disc + models_to_try))
                except Exception:
                    pass

                for model in models_to_try:
                    res = await client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                        json={
                            "model": model,
                            "messages": [{"role": "user", "content": prompt}],
                            "temperature": 0.1,
                            "response_format": {"type": "json_object"}
                        }
                    )
                    if res.status_code == 200:
                        data = res.json()
                        text_content = data["choices"][0]["message"]["content"]
                        break

            # 2. Gemini Provider
            elif provider == "gemini" or os.getenv("GEMINI_API_KEY"):
                key = os.getenv("GEMINI_API_KEY") or api_key
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}"
                res = await client.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"temperature": 0.1, "response_mime_type": "application/json"}
                    }
                )
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        text_content = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")

            # 3. OpenAI Provider
            elif provider == "openai" or os.getenv("OPENAI_API_KEY"):
                key = os.getenv("OPENAI_API_KEY") or api_key
                res = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.1,
                        "response_format": {"type": "json_object"}
                    }
                )
                if res.status_code == 200:
                    data = res.json()
                    text_content = data["choices"][0]["message"]["content"]

            if text_content:
                cleaned = re.sub(r"^```json\s*", "", text_content.strip(), flags=re.MULTILINE)
                cleaned = re.sub(r"^```\s*", "", cleaned, flags=re.MULTILINE).strip()
                parsed = json.loads(cleaned)
                if isinstance(parsed, dict) and "fields" in parsed:
                    parsed = parsed["fields"]
                if isinstance(parsed, list):
                    result_fields = []
                    for item in parsed:
                        if isinstance(item, dict) and "field_name" in item and "extracted_value" in item:
                            result_fields.append(ExtractedField(
                                field_name=str(item["field_name"]),
                                extracted_value=str(item["extracted_value"]),
                                confidence=float(item.get("confidence", 95.0)),
                                status=str(item.get("status", "Verified"))
                            ))
                    return result_fields

        return []

    @staticmethod
    def extract_fields(raw_text: str, category: str = "Unknown") -> Tuple[List[ExtractedField], List[str]]:
        extracted_fields: List[ExtractedField] = []
        warnings: List[str] = []

        # 1. Customer Name Extraction
        cust_match = re.search(r"(?:name|insured\s*name|customer\s*name|insured)\s*[:|-]\s*([A-Za-z\s'-]{2,35})", raw_text, re.IGNORECASE)
        if cust_match and cust_match.group(1).strip():
            val = cust_match.group(1).strip().split("\n")[0].split("Address")[0].split("Mobile")[0].strip()
            extracted_fields.append(ExtractedField(
                field_name="customer_name",
                extracted_value=val,
                confidence=98.0,
                status="Verified"
            ))
        else:
            extracted_fields.append(ExtractedField(
                field_name="customer_name",
                extracted_value="Not Found",
                confidence=0.0,
                status="Flagged",
                warning="Field 'customer_name' could not be found in document text."
            ))
            warnings.append("Customer name could not be automatically extracted.")

        # 2. Policy Number Extraction (Flexible for Indian & International Policy formats)
        pol_match = re.search(r"(?:policy\s*(?:no|num|number|#)?\s*[:|-]?\s*)([A-Z0-9-]{5,35})", raw_text, re.IGNORECASE)
        if pol_match and pol_match.group(1).strip():
            val = pol_match.group(1).strip().split()[0].upper()
            extracted_fields.append(ExtractedField(
                field_name="policy_number",
                extracted_value=val,
                confidence=98.0,
                status="Verified"
            ))
        else:
            extracted_fields.append(ExtractedField(
                field_name="policy_number",
                extracted_value="Not Found",
                confidence=0.0,
                status="Flagged",
                warning="Field 'policy_number' missing from document text."
            ))
            warnings.append("Policy number missing in document text.")

        # 3. Claim Number Extraction
        claim_match = re.search(r"(?:claim\s*(?:no|num|number|#)?\s*[:|-]?\s*)([A-Z0-9-]{5,35})", raw_text, re.IGNORECASE)
        if claim_match and claim_match.group(1).strip():
            val = claim_match.group(1).strip().split()[0].upper()
            extracted_fields.append(ExtractedField(
                field_name="claim_number",
                extracted_value=val,
                confidence=98.0,
                status="Verified"
            ))

        # 3b. Email Extraction
        email_match = re.search(r"(?:email|e-mail)\s*[:|-]?\s*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})", raw_text, re.IGNORECASE)
        if not email_match:
            email_match = re.search(r"\b([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})\b", raw_text)
        if email_match:
            extracted_fields.append(ExtractedField(
                field_name="email",
                extracted_value=email_match.group(1).strip(),
                confidence=96.0,
                status="Verified"
            ))

        # 3c. Phone Extraction
        phone_match = re.search(r"(?:phone|mobile|contact|tel)\s*[:|-]?\s*(\+?[0-9\s-]{8,20})", raw_text, re.IGNORECASE)
        if phone_match:
            extracted_fields.append(ExtractedField(
                field_name="phone",
                extracted_value=phone_match.group(1).strip(),
                confidence=96.0,
                status="Verified"
            ))

        # 4. Vehicle Registration Number Extraction (e.g. HR-98-4544, MH-12-AB-1234)
        veh_match = re.search(r"(?:vehicle\s*(?:no|num|number|reg|#)?\s*[:|-]?\s*)([A-Z0-9-]{4,15})", raw_text, re.IGNORECASE)
        if veh_match and veh_match.group(1).strip():
            val = veh_match.group(1).strip().split()[0].upper()
            extracted_fields.append(ExtractedField(
                field_name="vehicle_number",
                extracted_value=val,
                confidence=98.0,
                status="Verified"
            ))
        else:
            vin_match = re.search(r"\b[A-HJ-NPR-Z0-9]{17}\b", raw_text)
            if vin_match:
                extracted_fields.append(ExtractedField(
                    field_name="vehicle_number",
                    extracted_value=vin_match.group(0).upper(),
                    confidence=96.0,
                    status="Verified"
                ))

        # 5. Engine & Chassis Numbers Extraction
        engine_match = re.search(r"(?:engine\s*(?:no|num|number|#)?\s*[:|-]?\s*)([A-Z0-9]{5,25})", raw_text, re.IGNORECASE)
        if engine_match:
            extracted_fields.append(ExtractedField(
                field_name="engine_number",
                extracted_value=engine_match.group(1).strip().upper(),
                confidence=96.0,
                status="Verified"
            ))

        chassis_match = re.search(r"(?:chassis\s*(?:no|num|number|#)?\s*[:|-]?\s*)([A-Z0-9]{10,25})", raw_text, re.IGNORECASE)
        if chassis_match:
            extracted_fields.append(ExtractedField(
                field_name="chassis_number",
                extracted_value=chassis_match.group(1).strip().upper(),
                confidence=96.0,
                status="Verified"
            ))

        # 6. Incident Date Extraction
        date_match = re.search(r"\b((?:0[1-9]|[12][0-9]|3[01])[-/.](?:0[1-9]|1[0-2])[-/.](?:19|20)[0-9]{2}(?:\s+[0-9]{1,2}:[0-9]{2})?)\b|\b((?:19|20)[0-9]{2}[-/.](?:0[1-9]|1[0-2])[-/.](?:0[1-9]|[12][0-9]|3[01]))\b", raw_text)
        if date_match:
            extracted_fields.append(ExtractedField(
                field_name="incident_date",
                extracted_value=date_match.group(0),
                confidence=94.0,
                status="Verified"
            ))

        # 7. Estimated Cost of Repairs / Claim Amount Extraction
        amount_match = re.search(r"(?:estimated\s*cost\s*of\s*repairs|estimated\s*cost|claim\s*amount|total\s*amount|total\s*estimate|amount)\s*[:|-]?\s*\$?([0-9,]+(?:\.[0-9]{2})?)", raw_text, re.IGNORECASE)
        if amount_match:
            val_str = amount_match.group(1).strip()
            extracted_fields.append(ExtractedField(
                field_name="claim_amount",
                extracted_value=f"${val_str}" if not val_str.startswith("$") else val_str,
                confidence=96.0,
                status="Verified"
            ))

        # 8. Driver License Extraction
        dl_match = re.search(r"(?:driving\s*license\s*(?:no|num|#)?|license\s*no)\s*[:|-]?\s*([A-Z0-9]{8,20})", raw_text, re.IGNORECASE)
        if dl_match:
            extracted_fields.append(ExtractedField(
                field_name="driving_license_no",
                extracted_value=dl_match.group(1).strip().upper(),
                confidence=98.0,
                status="Verified"
            ))

        return extracted_fields, warnings
