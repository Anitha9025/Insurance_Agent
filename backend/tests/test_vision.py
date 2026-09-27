import os
import io
import pytest
from PIL import Image, ImageDraw

from app.services.vision_analysis_service import (
    VisionAnalysisService,
    GeminiVisionProvider,
    ImageAnalysisResult
)
from app.ocr.image_engine import ImageOCREngine

@pytest.fixture
def create_test_image(tmp_path):
    """Helper fixture to generate synthetic test images with distinct colors and shapes."""
    def _generator(filename: str, color: str = "red", text: str = "") -> str:
        img_path = str(tmp_path / filename)
        img = Image.new("RGB", (300, 300), color=color)
        draw = ImageDraw.Draw(img)
        if text:
            draw.text((10, 10), text, fill=(255, 255, 255))
        img.save(img_path)
        return img_path
    return _generator

@pytest.mark.asyncio
async def test_vision_provider_dynamic_response(create_test_image):
    provider = GeminiVisionProvider()

    # Generate 3 distinct synthetic images
    img1 = create_test_image("car_red.jpg", color="red", text="Red Vehicle Collision")
    img2 = create_test_image("tree_fallen.png", color="green", text="Fallen Tree Property Impact")
    img3 = create_test_image("doc_report.jpeg", color="blue", text="Police Report Document")

    res1 = await provider.analyze_image(img1)
    res2 = await provider.analyze_image(img2)
    res3 = await provider.analyze_image(img3)

    assert isinstance(res1, ImageAnalysisResult)
    assert isinstance(res2, ImageAnalysisResult)
    assert isinstance(res3, ImageAnalysisResult)

    # Dynamic verification: Results must reflect the actual uploaded image filename/dimensions
    assert "car_red.jpg" in res1.scene_description or any("car_red.jpg" in o for o in res1.observations)
    assert "tree_fallen.png" in res2.scene_description or any("tree_fallen.png" in o for o in res2.observations)
    assert res3.analysis_type == "document" or "doc_report.jpeg" in res3.scene_description


@pytest.mark.asyncio
async def test_image_scenarios(create_test_image):
    service = VisionAnalysisService()

    scenarios = [
        ("two_car_collision.jpg", "red", "Collision front bumper"),
        ("motorcycle_accident.png", "black", "Motorcycle side damage"),
        ("fallen_tree_car.jpg", "green", "Tree on vehicle roof"),
        ("parked_damaged_car.png", "silver", "Rear bumper dent"),
        ("undamaged_car.jpg", "white", "Clean intact sedan"),
        ("road_scene.png", "gray", "Highway clear lane"),
        ("property_damage.jpg", "brown", "Broken garage door"),
        ("blurry_image.png", "darkgray", "Low clarity capture"),
        ("document_report.jpg", "blue", "Insurance Policy PDF"),
        ("unrelated_landscape.png", "yellow", "Sunset beach landscape")
    ]

    for fname, col, txt in scenarios:
        path = create_test_image(fname, color=col, text=txt)
        res = await service.analyze_single_image(path)
        assert res.scene_description is not None
        assert len(res.observations) > 0
        assert res.confidence >= 0.0


@pytest.mark.asyncio
async def test_multi_image_claim_analysis(create_test_image):
    service = VisionAnalysisService()
    img_a = create_test_image("damage_front.jpg", color="red")
    img_b = create_test_image("damage_rear.jpg", color="blue")

    res = await service.analyze_claim_images("claim-test-999", [img_a, img_b])
    assert res["claim_id"] == "claim-test-999"
    assert len(res["images"]) == 2
    assert res["images"][0]["filename"] == "damage_front.jpg"
    assert res["images"][1]["filename"] == "damage_rear.jpg"


@pytest.mark.asyncio
async def test_image_ocr_engine_integration(create_test_image):
    engine = ImageOCREngine()
    path = create_test_image("accident_scene.png", color="orange")
    res = await engine.extract_text(path)

    assert "SCENE DESCRIPTION:" in res.raw_text
    assert "OBSERVATIONS:" in res.raw_text
    assert "vision_analysis" in res.metadata


def test_analyze_claim_images_api_endpoint(client, create_test_image):
    # Setup Customer, Policy, Claim
    cust = client.post("/api/v1/customers", json={
        "name": "Bruce Wayne", "phone": "555-9000", "email": "bruce@example.com",
        "dob": "1980-02-19", "address": "Gotham", "nationalId": "SSN-XXX-XX-0007", "memberSince": "2019-01-01"
    }).json()

    pol = client.post("/api/v1/policies", json={
        "policyNumber": "POL-BAT-001", "category": "Vehicle", "startDate": "2025-01-01",
        "endDate": "2027-01-01", "coverageLimit": 200000.0, "deductible": 1000.0, "customerId": cust["id"]
    }).json()

    claim = client.post("/api/v1/claims", json={
        "title": "Frontal collision", "description": "Crash into barrier",
        "category": "Vehicle", "incidentDate": "2026-09-01", "incidentTime": "22:00",
        "location": "Downtown", "claimAmount": 15000.0, "customerId": cust["id"], "policyNumber": pol["policyNumber"]
    }).json()

    # Upload 2 Image Documents
    img_a_path = create_test_image("front.jpg", color="red")
    with open(img_a_path, "rb") as f:
        client.post(f"/api/v1/documents/claims/{claim['id']}/documents", files={"file": ("front.jpg", f, "image/jpeg")}, data={"category": "Damage Photo"})

    res_multi = client.post(f"/api/v1/documents/claims/{claim['id']}/analyze-images")
    assert res_multi.status_code == 200
    data = res_multi.json()
    assert data["claimId"] == claim["id"]
    assert len(data["images"]) >= 1
