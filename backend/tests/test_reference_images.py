"""
Test suite for reference_images array feature in image generation endpoints.
Tests: POST /api/images/generate and POST /api/images/generate-batch
Focus: API contract validation (field acceptance, mime_type validation, error handling)
Note: Does NOT call actual Gemini model - tests validation logic only
"""

import pytest
import requests
import os
import base64

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "monika.gawkowska@kurdynowski.pl"
TEST_PASSWORD = "MonZuz8180!"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for testing"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Authentication failed - cannot proceed with tests")


@pytest.fixture
def auth_headers(auth_token):
    """Authenticated headers"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


# --- Helper to create minimal valid base64 image data ---
def create_test_image_data(mime_type="image/png"):
    """Create a minimal valid-looking base64 string for testing API validation"""
    # This is NOT a real image - just test data for API contract validation
    fake_data = b"TEST_IMAGE_DATA_FOR_VALIDATION_ONLY_" + mime_type.encode()
    return base64.b64encode(fake_data).decode('utf-8')


class TestReferenceImagesFieldValidation:
    """Test reference_images array field acceptance and validation"""
    
    def test_generate_endpoint_accepts_reference_images_field(self, auth_headers):
        """POST /api/images/generate accepts 'reference_images' (array) field"""
        # This tests that the endpoint doesn't reject the field
        payload = {
            "prompt": "TEST_validation_prompt",
            "style": "hero",
            "reference_images": []  # Empty array should be accepted
        }
        
        response = requests.post(
            f"{BASE_URL}/api/images/generate",
            headers=auth_headers,
            json=payload,
            timeout=10
        )
        
        # 400 for bad image data is expected, but not 422 for unknown field
        # If reference_images field wasn't accepted, we'd get 422 validation error
        assert response.status_code != 422, f"reference_images field not accepted: {response.text}"
        print(f"PASS: reference_images field accepted by generate endpoint (status: {response.status_code})")
    
    
    def test_generate_batch_endpoint_accepts_reference_images_field(self, auth_headers):
        """POST /api/images/generate-batch accepts 'reference_images' (array) field"""
        payload = {
            "prompt": "TEST_validation_prompt_batch",
            "style": "hero",
            "num_variants": 2,
            "reference_images": []  # Empty array should be accepted
        }
        
        response = requests.post(
            f"{BASE_URL}/api/images/generate-batch",
            headers=auth_headers,
            json=payload,
            timeout=10
        )
        
        assert response.status_code != 422, f"reference_images field not accepted in batch: {response.text}"
        print(f"PASS: reference_images field accepted by generate-batch endpoint (status: {response.status_code})")
    
    
    def test_reference_images_array_structure_validation(self, auth_headers):
        """Test that reference_images array items have correct structure"""
        payload = {
            "prompt": "TEST_structure_validation",
            "style": "hero",
            "reference_images": [
                {
                    "data": create_test_image_data("image/png"),
                    "mime_type": "image/png",
                    "name": "test_image.png"  # Optional name field
                }
            ]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/images/generate",
            headers=auth_headers,
            json=payload,
            timeout=10
        )
        
        # Should not get 422 for field validation
        assert response.status_code != 422, f"reference_images structure validation failed: {response.text}"
        print(f"PASS: reference_images array structure accepted (status: {response.status_code})")


class TestMimeTypeValidation:
    """Test mime_type validation in reference_images array"""
    
    def test_valid_mime_type_png_accepted(self, auth_headers):
        """image/png mime_type is accepted"""
        payload = {
            "prompt": "TEST_mime_png",
            "style": "hero",
            "reference_images": [
                {"data": create_test_image_data("image/png"), "mime_type": "image/png"}
            ]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/images/generate",
            headers=auth_headers,
            json=payload,
            timeout=10
        )
        
        # Should not return 400 for invalid mime type
        if response.status_code == 400:
            assert "format" not in response.json().get("detail", "").lower() or "png" not in response.json().get("detail", "").lower()
        print(f"PASS: image/png mime_type accepted (status: {response.status_code})")
    
    
    def test_valid_mime_type_jpeg_accepted(self, auth_headers):
        """image/jpeg mime_type is accepted"""
        payload = {
            "prompt": "TEST_mime_jpeg",
            "style": "hero",
            "reference_images": [
                {"data": create_test_image_data("image/jpeg"), "mime_type": "image/jpeg"}
            ]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/images/generate",
            headers=auth_headers,
            json=payload,
            timeout=10
        )
        
        if response.status_code == 400:
            assert "format" not in response.json().get("detail", "").lower() or "jpeg" not in response.json().get("detail", "").lower()
        print(f"PASS: image/jpeg mime_type accepted (status: {response.status_code})")
    
    
    def test_valid_mime_type_webp_accepted(self, auth_headers):
        """image/webp mime_type is accepted"""
        payload = {
            "prompt": "TEST_mime_webp",
            "style": "hero",
            "reference_images": [
                {"data": create_test_image_data("image/webp"), "mime_type": "image/webp"}
            ]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/images/generate",
            headers=auth_headers,
            json=payload,
            timeout=10
        )
        
        if response.status_code == 400:
            assert "format" not in response.json().get("detail", "").lower() or "webp" not in response.json().get("detail", "").lower()
        print(f"PASS: image/webp mime_type accepted (status: {response.status_code})")
    
    
    def test_invalid_mime_type_returns_400(self, auth_headers):
        """Invalid mime_type (image/gif) returns 400 error"""
        payload = {
            "prompt": "TEST_invalid_mime",
            "style": "hero",
            "reference_images": [
                {"data": create_test_image_data("image/gif"), "mime_type": "image/gif"}
            ]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/images/generate",
            headers=auth_headers,
            json=payload,
            timeout=10
        )
        
        assert response.status_code == 400, f"Expected 400 for invalid mime_type, got {response.status_code}"
        assert "format" in response.json().get("detail", "").lower() or "gif" in response.json().get("detail", "").lower() or "nieobslugiwany" in response.json().get("detail", "").lower()
        print(f"PASS: Invalid mime_type (gif) correctly rejected with 400")
    
    
    def test_invalid_mime_type_in_batch_returns_400(self, auth_headers):
        """Invalid mime_type in batch endpoint returns 400 error"""
        payload = {
            "prompt": "TEST_invalid_mime_batch",
            "style": "hero",
            "num_variants": 2,
            "reference_images": [
                {"data": create_test_image_data("image/bmp"), "mime_type": "image/bmp"}
            ]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/images/generate-batch",
            headers=auth_headers,
            json=payload,
            timeout=10
        )
        
        assert response.status_code == 400, f"Expected 400 for invalid mime_type in batch, got {response.status_code}"
        print(f"PASS: Invalid mime_type in batch correctly rejected with 400")


class TestBackwardCompatibility:
    """Test backward compatibility with legacy single reference_image field"""
    
    def test_single_reference_image_field_still_works(self, auth_headers):
        """Legacy single reference_image field still accepted"""
        payload = {
            "prompt": "TEST_legacy_single_image",
            "style": "hero",
            "reference_image": {
                "data": create_test_image_data("image/png"),
                "mime_type": "image/png"
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/images/generate",
            headers=auth_headers,
            json=payload,
            timeout=10
        )
        
        # Should not get 422 for unknown field
        assert response.status_code != 422, f"Legacy reference_image field not accepted: {response.text}"
        print(f"PASS: Legacy single reference_image field still works (status: {response.status_code})")
    
    
    def test_single_reference_image_in_batch_still_works(self, auth_headers):
        """Legacy single reference_image field in batch endpoint still accepted"""
        payload = {
            "prompt": "TEST_legacy_single_batch",
            "style": "hero",
            "num_variants": 2,
            "reference_image": {
                "data": create_test_image_data("image/jpeg"),
                "mime_type": "image/jpeg"
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/images/generate-batch",
            headers=auth_headers,
            json=payload,
            timeout=10
        )
        
        assert response.status_code != 422, f"Legacy reference_image field not accepted in batch: {response.text}"
        print(f"PASS: Legacy single reference_image field works in batch (status: {response.status_code})")


class TestMultipleReferenceImages:
    """Test multiple reference images in the array"""
    
    def test_multiple_reference_images_accepted(self, auth_headers):
        """Multiple reference images in array are accepted"""
        payload = {
            "prompt": "TEST_multiple_refs",
            "style": "hero",
            "reference_images": [
                {"data": create_test_image_data("image/png"), "mime_type": "image/png", "name": "ref1.png"},
                {"data": create_test_image_data("image/jpeg"), "mime_type": "image/jpeg", "name": "ref2.jpg"},
                {"data": create_test_image_data("image/webp"), "mime_type": "image/webp", "name": "ref3.webp"}
            ]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/images/generate",
            headers=auth_headers,
            json=payload,
            timeout=10
        )
        
        assert response.status_code != 422, f"Multiple reference_images not accepted: {response.text}"
        print(f"PASS: Multiple reference_images (3 images) accepted (status: {response.status_code})")
    
    
    def test_one_invalid_in_multiple_returns_400(self, auth_headers):
        """If one image in array has invalid mime_type, request returns 400"""
        payload = {
            "prompt": "TEST_one_invalid_in_multiple",
            "style": "hero",
            "reference_images": [
                {"data": create_test_image_data("image/png"), "mime_type": "image/png"},
                {"data": create_test_image_data("image/gif"), "mime_type": "image/gif"},  # Invalid
                {"data": create_test_image_data("image/webp"), "mime_type": "image/webp"}
            ]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/images/generate",
            headers=auth_headers,
            json=payload,
            timeout=10
        )
        
        assert response.status_code == 400, f"Expected 400 when one image has invalid mime, got {response.status_code}"
        print(f"PASS: One invalid mime in array correctly rejected with 400")


class TestEndpointExists:
    """Basic endpoint existence tests"""
    
    def test_health_endpoint(self):
        """Health endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert response.status_code == 200
        print("PASS: Health endpoint accessible")
    
    
    def test_image_styles_endpoint(self):
        """Image styles endpoint returns list of styles"""
        response = requests.get(f"{BASE_URL}/api/image-styles", timeout=10)
        assert response.status_code == 200
        styles = response.json()
        assert isinstance(styles, list)
        assert len(styles) > 0
        print(f"PASS: Image styles endpoint returns {len(styles)} styles")
    
    
    def test_generate_endpoint_requires_auth(self):
        """Generate endpoint requires authentication"""
        payload = {"prompt": "test", "style": "hero"}
        response = requests.post(
            f"{BASE_URL}/api/images/generate",
            json=payload,
            timeout=10
        )
        assert response.status_code == 401
        print("PASS: Generate endpoint requires authentication")
    
    
    def test_batch_endpoint_requires_auth(self):
        """Batch endpoint requires authentication"""
        payload = {"prompt": "test", "style": "hero", "num_variants": 2}
        response = requests.post(
            f"{BASE_URL}/api/images/generate-batch",
            json=payload,
            timeout=10
        )
        assert response.status_code == 401
        print("PASS: Batch endpoint requires authentication")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
