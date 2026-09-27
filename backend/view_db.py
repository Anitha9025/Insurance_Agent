import json
import urllib.request

def main():
    url = "http://localhost:8000/api/v1/documents"
    print("=" * 110)
    print("LIVE POSTGRESQL DATABASE RECORDS (CLEAN & DEDUPLICATED)")
    print("=" * 110)

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                
                print("\n--- 1. TABLE: claim_documents ---")
                if not data:
                    print("No documents stored in database yet.")
                    return

                print(f"{'ID':<16} | {'CLAIM_ID':<12} | {'FILE_NAME':<32} | {'TYPE':<6} | {'STATUS':<10} | {'VERIFIED':<10}")
                print("-" * 100)
                
                all_ocr_fields = []
                for d in data:
                    doc_id = d.get("id", "")
                    claim_id = d.get("claimId", d.get("claim_id", ""))
                    file_name = d.get("fileName", d.get("file_name", ""))
                    doc_type = d.get("type", "")
                    status = d.get("ocrStatus", d.get("ocr_status", ""))
                    verified = d.get("verificationStatus", d.get("verification_status", ""))
                    
                    print(f"{doc_id:<16} | {claim_id:<12} | {file_name:<32} | {doc_type:<6} | {status:<10} | {verified:<10}")

                    fields = d.get("ocrFields", d.get("ocr_fields", []))
                    seen_names = set()
                    for f in fields:
                        fn = f.get("fieldName", f.get("field_name", "")).lower().strip()
                        if fn in seen_names:
                            continue
                        seen_names.add(fn)
                        all_ocr_fields.append((doc_id, f))

                print("\n--- 2. TABLE: ocr_fields ---")
                if not all_ocr_fields:
                    print("No OCR fields stored in database yet.")
                else:
                    print(f"{'DOCUMENT_ID':<16} | {'FIELD_NAME':<24} | {'EXTRACTED_VALUE':<35} | {'CONF':<5} | {'STATUS':<8}")
                    print("-" * 100)
                    for doc_id, f in all_ocr_fields:
                        fname = f.get("fieldName", f.get("field_name", ""))
                        val = str(f.get("extractedValue", f.get("extracted_value", ""))).replace("\n", " ")[:34]
                        conf = float(f.get("confidence", 0.0))
                        st = f.get("status", "")
                        print(f"{doc_id:<16} | {fname:<24} | {val:<35} | {conf:<5.1f} | {st:<8}")

                print("\n" + "=" * 110)
            else:
                print(f"HTTP Error: Server returned status {response.status}")
    except Exception as e:
        print(f"Connection Note: {str(e)}")

if __name__ == "__main__":
    main()
