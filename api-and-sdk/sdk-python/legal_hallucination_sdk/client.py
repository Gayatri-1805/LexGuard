"""
Python SDK client for legal hallucination detection API.

Usage:
    from legal_hallucination_sdk import HallucinationDetectorClient

    client = HallucinationDetectorClient(base_url="http://localhost:8000/api")
    response = client.check(text="Section 43A requires...", context="Legal analysis")
    print(response["decision"])  # SAFE, FLAGGED, ABSTAIN

    summary = client.get_summary(days=30)
    print(f"Avg trust: {summary['avg_trust_index']}")
"""

import httpx
from typing import Optional, Any, Dict


class DetectorAPIError(Exception):
    """Custom exception for API errors."""

    def __init__(self, status_code: int, detail: str, response_text: str = ""):
        self.status_code = status_code
        self.detail = detail
        self.response_text = response_text
        super().__init__(
            f"API Error {status_code}: {detail}\nResponse: {response_text}"
        )


class HallucinationDetectorClient:
    """
    Client for legal hallucination detection API.

    Attributes:
        base_url: Base URL of the API (e.g., "http://localhost:8000/api")
    """

    def __init__(self, base_url: str):
        """
        Initialize the client.

        Args:
            base_url: Base URL of the API endpoint
        """
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.client.close()

    def check(
        self,
        text: str,
        context: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Check LLM output for hallucinations.

        Args:
            text: LLM-generated text to check
            context: Optional context/prompt that produced the text
            request_id: Optional caller-supplied request identifier

        Returns:
            CheckResponse dict with claims, verdicts, trust_index, decision

        Raises:
            DetectorAPIError: On non-200 response
        """
        payload = {
            "text": text,
            "context": context,
            "request_id": request_id,
        }

        try:
            response = self.client.post(f"{self.base_url}/check", json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise DetectorAPIError(
                status_code=e.response.status_code,
                detail=e.response.get("detail", str(e)),
                response_text=e.response.text,
            )
        except Exception as e:
            raise DetectorAPIError(
                status_code=0,
                detail=f"Request failed: {str(e)}",
            )

    def get_summary(self, days: int = 30) -> Dict[str, Any]:
        """
        Get aggregate analytics summary.

        Args:
            days: Number of days to look back (default: 30)

        Returns:
            Summary dict with total_checks, checks_safe, checks_flagged, avg_trust_index, etc.

        Raises:
            DetectorAPIError: On non-200 response
        """
        try:
            response = self.client.get(
                f"{self.base_url}/analytics/summary",
                params={"days": days},
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise DetectorAPIError(
                status_code=e.response.status_code,
                detail=e.response.get("detail", str(e)),
                response_text=e.response.text,
            )
        except Exception as e:
            raise DetectorAPIError(
                status_code=0,
                detail=f"Request failed: {str(e)}",
            )

    def get_checks(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Get paginated list of recent checks.

        Args:
            limit: Max results per page (default: 50)
            offset: Pagination offset (default: 0)

        Returns:
            Dict with total count and list of checks

        Raises:
            DetectorAPIError: On non-200 response
        """
        try:
            response = self.client.get(
                f"{self.base_url}/analytics/checks",
                params={"limit": limit, "offset": offset},
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise DetectorAPIError(
                status_code=e.response.status_code,
                detail=e.response.get("detail", str(e)),
                response_text=e.response.text,
            )
        except Exception as e:
            raise DetectorAPIError(
                status_code=0,
                detail=f"Request failed: {str(e)}",
            )

    def get_flagged(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Get paginated list of flagged checks (for review).

        Args:
            limit: Max results per page (default: 50)
            offset: Pagination offset (default: 0)

        Returns:
            Dict with total count and list of flagged checks

        Raises:
            DetectorAPIError: On non-200 response
        """
        try:
            response = self.client.get(
                f"{self.base_url}/analytics/flagged",
                params={"limit": limit, "offset": offset},
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise DetectorAPIError(
                status_code=e.response.status_code,
                detail=e.response.get("detail", str(e)),
                response_text=e.response.text,
            )
        except Exception as e:
            raise DetectorAPIError(
                status_code=0,
                detail=f"Request failed: {str(e)}",
            )

    def close(self):
        """Close the HTTP client."""
        self.client.close()
