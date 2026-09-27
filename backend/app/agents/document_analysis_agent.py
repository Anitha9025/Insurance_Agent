import re
from difflib import SequenceMatcher
from typing import List, Dict, Any, Optional, Tuple
from app.agents.state import DocumentAnalysisResult, DocumentItemAnalysis
from app.core.logging import logger

def _spell_check_similarity(s1: Optional[str], s2: Optional[str]) -> float:
    """Calculates string similarity ratio for spell check and typo detection (0.0 to 1.0)."""
    if not s1 or not s2:
        return 1.0
    c1 = s1.strip().lower()
    c2 = s2.strip().lower()
    if c1 == c2:
        return 1.0
    return SequenceMatcher(None, c1, c2).ratio()

def _are_dates_equal(d1: Optional[str], d2: Optional[str]) -> bool:
    """Helper to intelligently parse and compare dates in various formats ('20 September 2026', '20-09-2026', '2026-09-20')."""
    if not d1 or not d2:
        return True
    s1 = d1.strip()
    s2 = d2.strip()
    if s1 == s2 or s1.lower() == s2.lower():
        return True

    def parse_date(s: str) -> Optional[Tuple[int, int, int]]:
        s_clean = s.strip()
        # YYYY-MM-DD or YYYY/MM/DD
        m = re.search(r"(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})", s_clean)
        if m:
            return (int(m.group(1)), int(m.group(2)), int(m.group(3)))
        # DD-MM-YYYY or DD/MM/YYYY
        m = re.search(r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})", s_clean)
        if m:
            return (int(m.group(3)), int(m.group(2)), int(m.group(1)))

        # Month names: "20 September 2026", "20 Sep 2026", "September 20, 2026"
        months = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]
        short_months = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
        s_lower = s_clean.lower()
        for idx, (m_full, m_short) in enumerate(zip(months, short_months), 1):
            if m_full in s_lower or m_short in s_lower:
                nums = [int(n) for n in re.findall(r"\d+", s_clean)]
                years = [n for n in nums if n > 1900]
                days = [n for n in nums if 1 <= n <= 31 and n not in years]
                if years and days:
                    return (years[0], idx, days[0])
        return None

    p1 = parse_date(s1)
    p2 = parse_date(s2)
    if p1 and p2:
        return p1 == p2
    return False

class DocumentAnalysisAgent:
    """Agent responsible for aggregating and analyzing all uploaded claim documents.
    Reuses existing Phase 4 Cloud Multimodal Vision and Hybrid OCR outputs without duplicating model calls.
    Performs cross-document mismatch validation against registered claim/customer/policy metadata and policy documents.
    """

    @staticmethod
    def analyze(
        documents_data: List[Dict[str, Any]],
        claim_data: Optional[Dict[str, Any]] = None,
        customer_data: Optional[Dict[str, Any]] = None,
        policy_data: Optional[Dict[str, Any]] = None
    ) -> DocumentAnalysisResult:
        logger.info(f"DocumentAnalysisAgent starting analysis across {len(documents_data)} documents...")

        item_analyses: List[DocumentItemAnalysis] = []
        aggregated_evidence: List[str] = []
        aggregated_uncertainties: List[str] = []
        has_flagged = False

        # Context attributes for cross-document validation
        reg_customer_name = (customer_data.get("name") if customer_data else None) or (claim_data.get("customer_name") if claim_data else None)
        reg_customer_email = (customer_data.get("email") if customer_data else None) or (claim_data.get("customer_email") if claim_data else None)
        reg_customer_phone = (customer_data.get("phone") if customer_data else None) or (claim_data.get("customer_phone") if claim_data else None)
        reg_policy_num = (policy_data.get("policy_number") if policy_data else None) or (claim_data.get("policy_number") if claim_data else None)
        reg_incident_date = claim_data.get("incident_date") if claim_data else None
        reg_vehicle_no = (policy_data.get("vehicle_number") if policy_data else None) or (claim_data.get("vehicle_number") if claim_data else None)
        reg_chassis_no = (policy_data.get("chassis_number") if policy_data else None) or (claim_data.get("chassis_number") if claim_data else None)

        # Policy document extracted fields
        pol_doc_fields = (policy_data.get("document_extracted_fields") if policy_data else None) or (policy_data.get("specific_details") if policy_data else None) or {}

        # ── Policy Document Field-by-Field Spell Check & Cross Validation ──
        if pol_doc_fields:
            pol_cust_name = pol_doc_fields.get("customer_name")
            pol_cust_email = pol_doc_fields.get("customer_email")
            pol_cust_phone = pol_doc_fields.get("customer_phone")
            pol_veh_no = pol_doc_fields.get("registration_number")
            pol_chassis_no = pol_doc_fields.get("chassis_number")

            # 1. Customer Name Comparison & Spell Check
            if reg_customer_name and pol_cust_name:
                sim = _spell_check_similarity(reg_customer_name, pol_cust_name)
                parts_reg = set(reg_customer_name.lower().split())
                parts_pol = set(pol_cust_name.lower().split())

                if sim >= 0.95 or parts_reg == parts_pol:
                    aggregated_evidence.append(f"Policy Document Field Match: Customer Name ('{reg_customer_name}') verified against policy document.")
                elif sim >= 0.70 or bool(parts_reg.intersection(parts_pol)):
                    has_flagged = True
                    aggregated_uncertainties.append(
                        f"Name Spell Check Warning [Policy Document]: Registered customer name ('{reg_customer_name}') has spelling variation compared to policy document name ('{pol_cust_name}')."
                    )
                else:
                    has_flagged = True
                    aggregated_uncertainties.append(
                        f"Customer Name Mismatch [Policy Document]: Registered customer name ('{reg_customer_name}') does not match policy document holder name ('{pol_cust_name}')."
                    )

            # 2. Email Comparison
            if reg_customer_email and pol_cust_email:
                if reg_customer_email.strip().lower() == pol_cust_email.strip().lower():
                    aggregated_evidence.append(f"Policy Document Field Match: Email ('{reg_customer_email}') verified against policy document.")
                else:
                    has_flagged = True
                    aggregated_uncertainties.append(
                        f"Email Mismatch [Policy Document]: Registered email ('{reg_customer_email}') differs from policy document email ('{pol_cust_email}')."
                    )

            # 3. Phone Comparison
            if reg_customer_phone and pol_cust_phone:
                clean_reg = re.sub(r"\D", "", reg_customer_phone)
                clean_pol = re.sub(r"\D", "", pol_cust_phone)
                if clean_reg and clean_pol and (clean_reg == clean_pol or clean_reg[-10:] == clean_pol[-10:]):
                    aggregated_evidence.append(f"Policy Document Field Match: Phone ('{reg_customer_phone}') verified against policy document.")
                else:
                    has_flagged = True
                    aggregated_uncertainties.append(
                        f"Phone Mismatch [Policy Document]: Registered phone ('{reg_customer_phone}') differs from policy document phone ('{pol_cust_phone}')."
                    )

            # 4. Vehicle Registration Number Comparison & Spell Check
            if pol_veh_no:
                target_veh = reg_vehicle_no
                if not target_veh and documents_data:
                    for d in documents_data:
                        for f in d.get("ocr_fields") or d.get("ocrFields") or []:
                            if isinstance(f, dict):
                                fn = (f.get("field_name") or f.get("fieldName") or "").lower()
                                if "vehicle" in fn or "registration" in fn or "plate" in fn:
                                    target_veh = f.get("extracted_value") or f.get("extractedValue")
                                    break

                if target_veh:
                    clean_target = target_veh.replace("-", "").replace(" ", "").upper()
                    clean_pol = pol_veh_no.replace("-", "").replace(" ", "").upper()
                    sim = _spell_check_similarity(clean_target, clean_pol)
                    if clean_target == clean_pol:
                        aggregated_evidence.append(f"Policy Document Field Match: Vehicle Registration Number ('{target_veh}') verified against policy document.")
                    elif sim >= 0.75:
                        has_flagged = True
                        aggregated_uncertainties.append(
                            f"Vehicle Registration Spell Check Warning [Policy Document]: Vehicle registration ('{target_veh}') has character variation compared to policy document registration ('{pol_veh_no}')."
                        )
                    else:
                        has_flagged = True
                        aggregated_uncertainties.append(
                            f"Vehicle Registration Mismatch [Policy Document]: Vehicle registration ('{target_veh}') differs from policy document vehicle registration ('{pol_veh_no}')."
                        )

            # 5. Chassis / VIN Number Comparison & Spell Check
            if pol_chassis_no:
                target_chassis = reg_chassis_no
                if not target_chassis and documents_data:
                    for d in documents_data:
                        for f in d.get("ocr_fields") or d.get("ocrFields") or []:
                            if isinstance(f, dict):
                                fn = (f.get("field_name") or f.get("fieldName") or "").lower()
                                if "chassis" in fn or "vin" in fn:
                                    target_chassis = f.get("extracted_value") or f.get("extractedValue")
                                    break

                if target_chassis:
                    clean_target = target_chassis.replace("-", "").replace(" ", "").upper()
                    clean_pol = pol_chassis_no.replace("-", "").replace(" ", "").upper()
                    sim = _spell_check_similarity(clean_target, clean_pol)
                    if clean_target == clean_pol:
                        aggregated_evidence.append(f"Policy Document Field Match: Chassis Number ('{target_chassis}') verified against policy document.")
                    elif sim >= 0.75:
                        has_flagged = True
                        aggregated_uncertainties.append(
                            f"Chassis Number Spell Check Warning [Policy Document]: Chassis number ('{target_chassis}') has character variation compared to policy document chassis number ('{pol_chassis_no}')."
                        )
                    else:
                        has_flagged = True
                        aggregated_uncertainties.append(
                            f"Chassis Number Mismatch [Policy Document]: Chassis number ('{target_chassis}') differs from policy document chassis number ('{pol_chassis_no}')."
                        )

        for doc in documents_data:
            doc_id = doc.get("id") or doc.get("document_id") or "unknown"
            filename = doc.get("file_name") or doc.get("fileName") or "unknown"
            doc_type = doc.get("category") or doc.get("type") or "Unknown Document"
            ocr_status = doc.get("ocr_status") or doc.get("ocrStatus") or "Pending"
            verif_status = doc.get("verification_status") or doc.get("verificationStatus") or "Pending"
            ocr_fields = doc.get("ocr_fields") or doc.get("ocrFields") or []

            if verif_status == "Flagged":
                has_flagged = True
                aggregated_uncertainties.append(f"Document '{filename}' ({doc_id}) marked for human review.")

            vision_meta = doc.get("vision_analysis") or doc.get("visionAnalysis")

            # Extract visual evidence if Phase 4 Vision Analysis is present
            if isinstance(vision_meta, dict):
                scene_desc = vision_meta.get("scene_description") or vision_meta.get("sceneDescription")
                if scene_desc:
                    aggregated_evidence.append(f"Visual Scene [{filename}]: {scene_desc}")
                
                objs = vision_meta.get("objects_detected") or vision_meta.get("objectsDetected") or []
                if objs:
                    aggregated_evidence.append(f"Visually Detected Objects [{filename}]: {', '.join(objs)}")

                vehicles = vision_meta.get("vehicles") or []
                for v in vehicles:
                    if isinstance(v, dict):
                        v_type = v.get("vehicle_type") or v.get("vehicleType") or "vehicle"
                        v_color = v.get("color") or ""
                        v_damage = v.get("visible_damage") or v.get("visibleDamage") or []
                        d_str = ", ".join(v_damage) if isinstance(v_damage, list) else str(v_damage)
                        aggregated_evidence.append(f"Vehicle Analysis [{filename}]: {v_color} {v_type} - Damage: {d_str}")

                unknowns = vision_meta.get("unknowns") or []
                for u in unknowns:
                    aggregated_uncertainties.append(f"Visual Uncertainty [{filename}]: {u}")

            # Extract textual OCR evidence and perform Cross-Document Field Validation
            if isinstance(ocr_fields, list) and len(ocr_fields) > 0:
                extracted_pairs = []
                for f in ocr_fields:
                    if isinstance(f, dict):
                        k = (f.get("field_name") or f.get("fieldName") or "").strip()
                        v = (f.get("extracted_value") or f.get("extractedValue") or "").strip()
                        if not k or not v or v.lower() in ["not found", "unknown", "n/a"]:
                            continue

                        extracted_pairs.append(f"{k}: {v}")
                        k_lower = k.lower()
                        k_norm = re.sub(r"[_\s]+", " ", k_lower).strip()

                        # 1. Customer Name Cross-Validation
                        if any(x in k_norm for x in ["customer name", "applicant name", "policyholder name", "insured name", "policyholder"]):
                            if reg_customer_name and v.lower() != reg_customer_name.lower():
                                parts_v = set(v.lower().split())
                                parts_reg = set(reg_customer_name.lower().split())
                                if not parts_v.intersection(parts_reg):
                                    has_flagged = True
                                    aggregated_uncertainties.append(
                                        f"Customer Name Mismatch [{filename}]: Extracted customer_name ('{v}') does not match registered customer ('{reg_customer_name}')."
                                    )

                        # 2. Email Cross-Validation
                        elif "email" in k_norm:
                            if reg_customer_email and v.lower().strip() != reg_customer_email.lower().strip():
                                has_flagged = True
                                aggregated_uncertainties.append(
                                    f"Email Mismatch [{filename}]: Extracted email ('{v}') differs from registered email ('{reg_customer_email}')."
                                )

                        # 3. Phone Cross-Validation
                        elif any(x in k_norm for x in ["phone", "mobile", "contact", "tel"]):
                            clean_v = re.sub(r"\D", "", v)
                            clean_reg = re.sub(r"\D", "", reg_customer_phone) if reg_customer_phone else ""
                            if clean_reg and clean_v != clean_reg:
                                has_flagged = True
                                aggregated_uncertainties.append(
                                    f"Phone Mismatch [{filename}]: Extracted phone ('{v}') differs from registered phone ('{reg_customer_phone}')."
                                )

                        # 4. Policy Number Cross-Validation
                        elif "policy" in k_norm and any(x in k_norm for x in ["number", "no", "num", "policy"]):
                            clean_v = v.replace("-", "").replace(" ", "").lower()
                            clean_reg = reg_policy_num.replace("-", "").replace(" ", "").lower() if reg_policy_num else ""
                            if clean_reg and clean_v != clean_reg:
                                has_flagged = True
                                aggregated_uncertainties.append(
                                    f"Policy Number Mismatch [{filename}]: Extracted policy_number ('{v}') differs from registered policy ('{reg_policy_num}')."
                                )

                        # 5. Vehicle Registration Number Cross-Validation
                        elif any(x in k_norm for x in ["vehicle", "registration", "plate", "reg"]):
                            clean_v = v.replace("-", "").replace(" ", "").upper()
                            clean_reg = reg_vehicle_no.replace("-", "").replace(" ", "").upper() if reg_vehicle_no else ""
                            if clean_reg and clean_v != clean_reg:
                                has_flagged = True
                                aggregated_uncertainties.append(
                                    f"Vehicle Registration Mismatch [{filename}]: Extracted vehicle registration ('{v}') differs from registered vehicle number ('{reg_vehicle_no}')."
                                )

                        # 6. Chassis Number / VIN Cross-Validation
                        elif any(x in k_norm for x in ["chassis", "vin"]):
                            clean_v = v.replace("-", "").replace(" ", "").upper()
                            clean_reg = reg_chassis_no.replace("-", "").replace(" ", "").upper() if reg_chassis_no else ""
                            if clean_reg and clean_v != clean_reg:
                                has_flagged = True
                                aggregated_uncertainties.append(
                                    f"Chassis Number Mismatch [{filename}]: Extracted chassis number ('{v}') differs from registered chassis number ('{reg_chassis_no}')."
                                )

                        # 7. Incident Date Cross-Validation (Intelligent Date Comparison)
                        elif "incident" in k_norm or "date of loss" in k_norm or "accident date" in k_norm:
                            if reg_incident_date and not _are_dates_equal(v, reg_incident_date):
                                has_flagged = True
                                aggregated_uncertainties.append(
                                    f"Incident Date Mismatch [{filename}]: Extracted incident_date ('{v}') differs from registered claim incident date ('{reg_incident_date}')."
                                )

                if extracted_pairs:
                    aggregated_evidence.append(f"Extracted OCR Fields [{filename}]: {'; '.join(extracted_pairs[:4])}")

            item_analyses.append(DocumentItemAnalysis(
                document_id=doc_id,
                filename=filename,
                document_type=doc_type,
                ocr_status=ocr_status,
                verification_status=verif_status,
                extracted_fields_count=len(ocr_fields) if isinstance(ocr_fields, list) else 0,
                vision_analysis=vision_meta
            ))

        logger.info(
            f"DocumentAnalysisAgent completed: analyzed={len(item_analyses)}, "
            f"evidence_count={len(aggregated_evidence)}, flagged={has_flagged}"
        )

        return DocumentAnalysisResult(
            documents_analyzed=len(item_analyses),
            documents=item_analyses,
            evidence=aggregated_evidence,
            uncertainties=aggregated_uncertainties,
            has_flagged_documents=has_flagged
        )
