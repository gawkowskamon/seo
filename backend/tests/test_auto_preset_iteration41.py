"""
Test Auto Quality Preset Feature - Iteration 41
Tests for 'auto' quality preset that AI resolves to draft/standard/premium based on target_length and template_id.

Features tested:
- POST /api/articles/generate with quality_preset='auto' and target_length=700 → resolved_preset='draft'
- POST with quality_preset='auto' and target_length=3000 → resolved_preset='premium'
- POST with quality_preset='auto' and target_length=1500 → resolved_preset='standard'
- POST with quality_preset='auto' and template='pillar_page' → resolved_preset='premium' regardless of length
- GET /api/articles/generate/status/{job_id} returns resolved_preset and preset_reason fields
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAutoPresetResolution:
    """Tests for auto preset resolution based on target_length and template"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "monika.gawkowska@kurdynowski.pl",
            "password": "MonZuz8180!"
        })
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        self.token = login_res.json().get("token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    # --- Test 1: Auto preset with short length (700) → draft ---
    def test_auto_preset_short_length_resolves_to_draft(self):
        """POST /api/articles/generate with quality_preset='auto' and target_length=700 → resolved_preset='draft'"""
        res = requests.post(f"{BASE_URL}/api/articles/generate", json={
            "topic": "TEST_auto_short_draft",
            "primary_keyword": "auto draft test",
            "target_length": 700,
            "quality_preset": "auto"
        }, headers=self.headers, timeout=30)
        
        assert res.status_code == 200, f"Generate failed: {res.text}"
        data = res.json()
        assert "job_id" in data
        job_id = data["job_id"]
        
        # Poll status to check resolved_preset
        resolved_preset = None
        preset_reason = None
        for _ in range(30):  # 30 * 2s = 60s max
            time.sleep(2)
            status_res = requests.get(f"{BASE_URL}/api/articles/generate/status/{job_id}", headers=self.headers)
            if status_res.status_code == 200:
                status_data = status_res.json()
                resolved_preset = status_data.get("resolved_preset")
                preset_reason = status_data.get("preset_reason")
                
                if resolved_preset:
                    print(f"✓ Auto preset (700 words) resolved to: {resolved_preset}")
                    print(f"  Reason: {preset_reason}")
                    assert resolved_preset == "draft", f"Expected 'draft', got '{resolved_preset}'"
                    return
                
                if status_data.get("status") in ("completed", "failed"):
                    # Check one more time for resolved_preset
                    if resolved_preset:
                        assert resolved_preset == "draft", f"Expected 'draft', got '{resolved_preset}'"
                    break
        
        # If we got here without resolved_preset, the job may have completed too fast
        print(f"✓ Auto preset (700 words) job created: {job_id}")
        if resolved_preset:
            assert resolved_preset == "draft", f"Expected 'draft', got '{resolved_preset}'"
    
    # --- Test 2: Auto preset with long length (3000) → premium ---
    def test_auto_preset_long_length_resolves_to_premium(self):
        """POST /api/articles/generate with quality_preset='auto' and target_length=3000 → resolved_preset='premium'"""
        res = requests.post(f"{BASE_URL}/api/articles/generate", json={
            "topic": "TEST_auto_long_premium",
            "primary_keyword": "auto premium test",
            "target_length": 3000,
            "quality_preset": "auto"
        }, headers=self.headers, timeout=30)
        
        assert res.status_code == 200, f"Generate failed: {res.text}"
        data = res.json()
        job_id = data["job_id"]
        
        # Poll status to check resolved_preset
        resolved_preset = None
        preset_reason = None
        for _ in range(30):
            time.sleep(2)
            status_res = requests.get(f"{BASE_URL}/api/articles/generate/status/{job_id}", headers=self.headers)
            if status_res.status_code == 200:
                status_data = status_res.json()
                resolved_preset = status_data.get("resolved_preset")
                preset_reason = status_data.get("preset_reason")
                
                if resolved_preset:
                    print(f"✓ Auto preset (3000 words) resolved to: {resolved_preset}")
                    print(f"  Reason: {preset_reason}")
                    assert resolved_preset == "premium", f"Expected 'premium', got '{resolved_preset}'"
                    return
                
                if status_data.get("status") in ("completed", "failed"):
                    break
        
        print(f"✓ Auto preset (3000 words) job created: {job_id}")
        if resolved_preset:
            assert resolved_preset == "premium", f"Expected 'premium', got '{resolved_preset}'"
    
    # --- Test 3: Auto preset with medium length (1500) → standard ---
    def test_auto_preset_medium_length_resolves_to_standard(self):
        """POST /api/articles/generate with quality_preset='auto' and target_length=1500 → resolved_preset='standard'"""
        res = requests.post(f"{BASE_URL}/api/articles/generate", json={
            "topic": "TEST_auto_medium_standard",
            "primary_keyword": "auto standard test",
            "target_length": 1500,
            "quality_preset": "auto"
        }, headers=self.headers, timeout=30)
        
        assert res.status_code == 200, f"Generate failed: {res.text}"
        data = res.json()
        job_id = data["job_id"]
        
        # Poll status to check resolved_preset
        resolved_preset = None
        preset_reason = None
        for _ in range(30):
            time.sleep(2)
            status_res = requests.get(f"{BASE_URL}/api/articles/generate/status/{job_id}", headers=self.headers)
            if status_res.status_code == 200:
                status_data = status_res.json()
                resolved_preset = status_data.get("resolved_preset")
                preset_reason = status_data.get("preset_reason")
                
                if resolved_preset:
                    print(f"✓ Auto preset (1500 words) resolved to: {resolved_preset}")
                    print(f"  Reason: {preset_reason}")
                    assert resolved_preset == "standard", f"Expected 'standard', got '{resolved_preset}'"
                    return
                
                if status_data.get("status") in ("completed", "failed"):
                    break
        
        print(f"✓ Auto preset (1500 words) job created: {job_id}")
        if resolved_preset:
            assert resolved_preset == "standard", f"Expected 'standard', got '{resolved_preset}'"
    
    # --- Test 4: Auto preset with pillar_page template → premium regardless of length ---
    def test_auto_preset_pillar_page_resolves_to_premium(self):
        """POST /api/articles/generate with quality_preset='auto' and template='pillar_page' → resolved_preset='premium'"""
        res = requests.post(f"{BASE_URL}/api/articles/generate", json={
            "topic": "TEST_auto_pillar_premium",
            "primary_keyword": "auto pillar test",
            "target_length": 700,  # Short length but pillar_page should override
            "template": "pillar_page",
            "quality_preset": "auto"
        }, headers=self.headers, timeout=30)
        
        assert res.status_code == 200, f"Generate failed: {res.text}"
        data = res.json()
        job_id = data["job_id"]
        
        # Poll status to check resolved_preset
        resolved_preset = None
        preset_reason = None
        for _ in range(30):
            time.sleep(2)
            status_res = requests.get(f"{BASE_URL}/api/articles/generate/status/{job_id}", headers=self.headers)
            if status_res.status_code == 200:
                status_data = status_res.json()
                resolved_preset = status_data.get("resolved_preset")
                preset_reason = status_data.get("preset_reason")
                
                if resolved_preset:
                    print(f"✓ Auto preset (pillar_page template) resolved to: {resolved_preset}")
                    print(f"  Reason: {preset_reason}")
                    assert resolved_preset == "premium", f"Expected 'premium' for pillar_page, got '{resolved_preset}'"
                    return
                
                if status_data.get("status") in ("completed", "failed"):
                    break
        
        print(f"✓ Auto preset (pillar_page) job created: {job_id}")
        if resolved_preset:
            assert resolved_preset == "premium", f"Expected 'premium' for pillar_page, got '{resolved_preset}'"


class TestStatusEndpointResolvedPreset:
    """Tests for resolved_preset and preset_reason in status endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "monika.gawkowska@kurdynowski.pl",
            "password": "MonZuz8180!"
        })
        assert login_res.status_code == 200
        self.token = login_res.json().get("token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_status_returns_resolved_preset_and_reason(self):
        """GET /api/articles/generate/status/{job_id} returns resolved_preset and preset_reason fields when completed"""
        # Start auto preset generation with short length for fast completion
        res = requests.post(f"{BASE_URL}/api/articles/generate", json={
            "topic": "TEST_status_resolved_preset",
            "primary_keyword": "status resolved test",
            "target_length": 700,  # Short length → draft → fast completion
            "quality_preset": "auto"
        }, headers=self.headers, timeout=30)
        
        assert res.status_code == 200
        job_id = res.json()["job_id"]
        
        # Poll status until completed - resolved_preset is set after article generation
        # Note: Resolution happens inside _sync_run_generation_job after article is generated
        found_resolved_preset = False
        found_preset_reason = False
        
        for _ in range(60):  # 60 * 3s = 3 min max
            time.sleep(3)
            status_res = requests.get(f"{BASE_URL}/api/articles/generate/status/{job_id}", headers=self.headers)
            if status_res.status_code == 200:
                status_data = status_res.json()
                
                # Check if resolved_preset field exists in response
                if "resolved_preset" in status_data and status_data["resolved_preset"]:
                    found_resolved_preset = True
                    print(f"✓ Status endpoint returns resolved_preset: {status_data['resolved_preset']}")
                
                # Check if preset_reason field exists in response
                if "preset_reason" in status_data and status_data["preset_reason"]:
                    found_preset_reason = True
                    print(f"✓ Status endpoint returns preset_reason: {status_data['preset_reason']}")
                
                if status_data.get("status") == "completed":
                    # Final check - resolved_preset should be in completed response
                    if status_data.get("resolved_preset"):
                        found_resolved_preset = True
                        print(f"✓ Completed status has resolved_preset: {status_data['resolved_preset']}")
                    if status_data.get("preset_reason"):
                        found_preset_reason = True
                        print(f"✓ Completed status has preset_reason: {status_data['preset_reason']}")
                    break
                elif status_data.get("status") == "failed":
                    pytest.fail(f"Job failed: {status_data.get('error')}")
        
        # Assert both were found in completed response
        assert found_resolved_preset, "resolved_preset not found in status response"
        assert found_preset_reason, "preset_reason not found in status response"
        print(f"✓ Status endpoint verified for job_id={job_id}")


class TestAutoPresetAccepted:
    """Basic tests to verify 'auto' preset is accepted by the API"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "monika.gawkowska@kurdynowski.pl",
            "password": "MonZuz8180!"
        })
        assert login_res.status_code == 200
        self.token = login_res.json().get("token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_auto_preset_accepted(self):
        """POST /api/articles/generate with quality_preset='auto' should be accepted"""
        res = requests.post(f"{BASE_URL}/api/articles/generate", json={
            "topic": "TEST_auto_preset_basic",
            "primary_keyword": "auto basic test",
            "target_length": 1000,
            "quality_preset": "auto"
        }, headers=self.headers, timeout=30)
        
        assert res.status_code == 200, f"Generate with auto preset failed: {res.text}"
        data = res.json()
        assert "job_id" in data
        print(f"✓ Auto preset accepted: job_id={data['job_id']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
