from typing import Optional, Tuple


class AnalysisClient:
    def __init__(self, base_url: Optional[str] = None) -> None:
        self.base_url = base_url or "http://ml-service.local"  # placeholder

    async def analyze_header(self, header_text: str) -> dict:
        # TODO: integrate real HTTP call to model service
        # Return a mocked response for now
        return {"is_phishing": False, "confidence": 0.5, "source": "stub"}

    async def analyze_file(self, eml_bytes: bytes) -> dict:
        # TODO: integrate real HTTP call to model service
        return {"is_phishing": True, "confidence": 0.8, "source": "stub"}

