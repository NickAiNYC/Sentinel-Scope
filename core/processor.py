"""
SentinelScope Batch Processor v2.7 (Enhanced - Dec 2025)
Forensic Vision Engine using DeepSeek-V3 for parallel site imagery analysis.

Enhancements:
- Progress tracking with Streamlit integration
- Exponential backoff retry logic
- Response caching for identical images
- Detailed error classification
- Token usage tracking
- Graceful degradation on partial failures
"""

import base64
import concurrent.futures
import hashlib
import json
import time
from collections.abc import Callable
from typing import Any

import streamlit as st
from openai import OpenAI
from pydantic import ValidationError

from core.gap_detector import ComplianceGapEngine

# Internal SentinelScope Imports
from core.models import CaptureClassification, GapAnalysisResponse


class SentinelBatchProcessor:
    """
    Forensic Vision Engine: Uses DeepSeek-V3 to analyze site imagery in parallel.

    Features:
    - Parallel processing with ThreadPoolExecutor
    - Automatic retry with exponential backoff
    - Image hash-based caching
    - Progress tracking for Streamlit UI
    - Token usage monitoring
    - Graceful error handling
    """

    # DeepSeek pricing (as of Dec 2025)
    DEEPSEEK_VISION_COST_PER_1K_TOKENS = 0.00027

    def __init__(
        self,
        engine: ComplianceGapEngine,
        api_key: str,
        max_workers: int = 5,
        max_retries: int = 3,
        enable_cache: bool = True,
    ):
        """
        Initialize the batch processor.

        Args:
            engine: ComplianceGapEngine instance for gap detection
            api_key: DeepSeek API key
            max_workers: Maximum parallel threads (default: 5)
            max_retries: Maximum retry attempts per image (default: 3)
            enable_cache: Enable image hash-based caching (default: True)
        """
        self.engine = engine
        self.max_workers = max_workers
        self.max_retries = max_retries
        self.enable_cache = enable_cache

        self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

        self.system_prompt = """
ACT AS: A Senior NYC DOB Forensic Inspector with 15+ years experience.

TASK: Conduct a visual milestone audit using NYC BC 2022/2025 guidelines.

INSTRUCTIONS:
1. Identify the primary construction milestone visible in the image
2. Determine the floor level (if visible) or estimate based on context
3. Assess the zone/location within the building
4. Rate your confidence (0.0-1.0) in the classification
5. Evaluate compliance relevance (0-10 scale)
6. Provide brief but specific evidence notes

Output strictly in valid JSON format matching the provided schema.
Be precise but concise. Focus on regulatory-relevant details.
"""

        # Tracking metrics
        self.total_tokens_used = 0
        self.total_api_cost = 0.0
        self.image_cache = {} if enable_cache else None
        self.processing_errors = []

    def _get_image_hash(self, image_data: bytes) -> str:
        """
        Generate SHA-256 hash of image for caching.

        Args:
            image_data: Raw image bytes

        Returns:
            Hex digest of image hash
        """
        return hashlib.sha256(image_data).hexdigest()

    def _prepare_base64(self, file_source: Any) -> tuple[str, str | None]:
        """
        Handles encoding for local paths and Streamlit UploadedFile objects.

        Args:
            file_source: File path string or Streamlit UploadedFile

        Returns:
            Tuple of (base64_encoded_string, image_hash)
        """
        try:
            # Handle Streamlit UploadedFile
            if hasattr(file_source, "read"):
                file_source.seek(0)
                data = file_source.read()
                image_hash = self._get_image_hash(data) if self.enable_cache else None
                return base64.b64encode(data).decode("utf-8"), image_hash

            # Handle file path
            with open(file_source, "rb") as image_file:
                data = image_file.read()
                image_hash = self._get_image_hash(data) if self.enable_cache else None
                return base64.b64encode(data).decode("utf-8"), image_hash

        except Exception as e:
            raise OSError(f"Forensic Encoding Error: {str(e)}") from e

    def _process_single_image(
        self, file_source: str | Any, progress_callback: Callable | None = None
    ) -> CaptureClassification:
        """
        Sends image to DeepSeek-V3 with strict schema enforcement and retry logic.

        Args:
            file_source: File path or UploadedFile object
            progress_callback: Optional callback for progress updates

        Returns:
            CaptureClassification object with analysis results
        """
        # Prepare image
        try:
            base64_image, image_hash = self._prepare_base64(file_source)
        except OSError as e:
            return CaptureClassification(
                milestone="Encoding Error",
                floor="ERR",
                zone="Pre-Processing_Failed",
                confidence=0.0,
                compliance_relevance=0,
                evidence_notes=str(e)[:200],
            )

        # Check cache
        if self.enable_cache and image_hash and image_hash in self.image_cache:
            if progress_callback:
                progress_callback("cache_hit")
            return self.image_cache[image_hash]

        # Retry loop with exponential backoff
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model="deepseek-chat",
                    response_format={"type": "json_object"},
                    temperature=0.1,
                    max_tokens=1000,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": (
                                        f"Audit this capture. Respond strictly "
                                        f"using this Pydantic schema: "
                                        f"{CaptureClassification.model_json_schema()}"
                                    ),
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_image}"
                                    },
                                },
                            ],
                        },
                    ],
                )

                # Track token usage
                if hasattr(response, "usage"):
                    tokens = response.usage.total_tokens
                    self.total_tokens_used += tokens
                    self.total_api_cost += (
                        tokens * self.DEEPSEEK_VISION_COST_PER_1K_TOKENS / 1000
                    )

                # Parse response
                raw_json = response.choices[0].message.content
                parsed_data = json.loads(raw_json)

                # Validate with Pydantic
                result = CaptureClassification.model_validate(parsed_data)

                # Cache result
                if self.enable_cache and image_hash:
                    self.image_cache[image_hash] = result

                if progress_callback:
                    progress_callback("success")

                return result

            except json.JSONDecodeError as je:
                error_msg = (
                    f"Invalid JSON from DeepSeek "
                    f"(attempt {attempt + 1}/{self.max_retries})"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(2**attempt)  # Exponential backoff
                    continue
                else:
                    self.processing_errors.append(error_msg)
                    return CaptureClassification(
                        milestone="JSON Parse Error",
                        floor="ERR",
                        zone="DeepSeek_Response_Invalid",
                        confidence=0.0,
                        compliance_relevance=0,
                        evidence_notes=f"{error_msg}: {str(je)[:150]}",
                    )

            except ValidationError as ve:
                error_msg = "NYC DOB Schema Mismatch"
                self.processing_errors.append(error_msg)
                return CaptureClassification(
                    milestone="Validation Error",
                    floor="ERR",
                    zone="Forensic_Failure",
                    confidence=0.0,
                    compliance_relevance=0,
                    evidence_notes=f"{error_msg}: {str(ve)[:200]}",
                )

            except Exception as e:
                error_str = str(e).lower()

                # Handle rate limiting
                if "rate_limit" in error_str or "429" in error_str:
                    if attempt < self.max_retries - 1:
                        wait_time = (2**attempt) * 2  # Longer wait for rate limits
                        if progress_callback:
                            progress_callback(f"rate_limit_wait_{wait_time}")
                        time.sleep(wait_time)
                        continue
                    else:
                        self.processing_errors.append("Rate limit exceeded")
                        return CaptureClassification(
                            milestone="Rate Limit Error",
                            floor="ERR",
                            zone="API_Throttled",
                            confidence=0.0,
                            compliance_relevance=0,
                            evidence_notes=(
                                "DeepSeek rate limit exceeded. "
                                "Try again later."
                            ),
                        )

                # Handle authentication errors
                elif "api_key" in error_str or "401" in error_str:
                    self.processing_errors.append("Authentication failed")
                    return CaptureClassification(
                        milestone="Auth Error",
                        floor="ERR",
                        zone="API_Key_Invalid",
                        confidence=0.0,
                        compliance_relevance=0,
                        evidence_notes="Invalid DeepSeek API key. Check credentials.",
                    )

                # Generic retry for transient errors
                elif attempt < self.max_retries - 1:
                    time.sleep(2**attempt)
                    continue

                # Final failure
                else:
                    self.processing_errors.append(f"API error: {str(e)[:100]}")
                    return CaptureClassification(
                        milestone="System Error",
                        floor="ERR",
                        zone="Audit_Failed",
                        confidence=0.0,
                        compliance_relevance=0,
                        evidence_notes=f"API connection failed: {str(e)[:200]}",
                    )

        # Should never reach here, but safeguard
        return CaptureClassification(
            milestone="Unknown Error",
            floor="ERR",
            zone="Processing_Failed",
            confidence=0.0,
            compliance_relevance=0,
            evidence_notes="Unexpected processing failure after all retries",
        )

    def run_audit(
        self, file_sources: list[Any], show_progress: bool = True
    ) -> list[CaptureClassification]:
        """
        Processes site captures in parallel using a ThreadPool.

        Args:
            file_sources: List of file paths or UploadedFile objects
            show_progress: Whether to show Streamlit progress bar

        Returns:
            List of CaptureClassification objects
        """
        # Reset error tracking
        self.processing_errors = []

        total_images = len(file_sources)
        processed_count = 0
        cache_hits = 0

        # Progress tracking
        if show_progress:
            progress_bar = st.progress(0)
            status_text = st.empty()

        def update_progress(status: str):
            nonlocal processed_count, cache_hits

            if status == "cache_hit":
                cache_hits += 1
            elif status == "success":
                processed_count += 1

            if show_progress:
                progress = (processed_count + cache_hits) / total_images
                progress_bar.progress(progress)
                status_text.text(
                    f"Processing: {processed_count + cache_hits}/{total_images} "
                    f"({'cached: ' + str(cache_hits) if cache_hits > 0 else ''})"
                )

        # Process in parallel
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as executor:
            futures = {
                executor.submit(
                    self._process_single_image, source, update_progress
                ): source
                for source in file_sources
            }

            results = []
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    # Handle unexpected executor errors
                    st.error(f"Unexpected error in parallel processing: {str(e)}")
                    results.append(
                        CaptureClassification(
                            milestone="Executor Error",
                            floor="ERR",
                            zone="Thread_Pool_Failed",
                            confidence=0.0,
                            compliance_relevance=0,
                            evidence_notes=f"Thread pool error: {str(e)[:200]}",
                        )
                    )

        # Cleanup progress display
        if show_progress:
            progress_bar.progress(1.0)
            status_text.text(f"✅ Completed: {total_images} images processed")

        # Show errors if any
        if self.processing_errors and show_progress:
            with st.expander("⚠️ Processing Errors", expanded=False):
                for error in self.processing_errors:
                    st.warning(error)

        return results

    def finalize_gap_analysis(
        self,
        findings: list[CaptureClassification],
        api_key: str | None = None,
        use_batch_processing: bool = False,
    ) -> GapAnalysisResponse:
        """
        Finalizes the remediation roadmap using the gap detection engine.

        Args:
            findings: List of classified milestones
            api_key: Optional DeepSeek API key for AI remediation
            use_batch_processing: Whether to use batch processing for gaps

        Returns:
            GapAnalysisResponse with compliance analysis
        """
        return self.engine.detect_gaps(
            findings=findings,
            api_key=api_key,
            use_batch_processing=use_batch_processing,
        )

    def get_usage_summary(self) -> dict:
        """
        Get summary of API usage and costs for the current session.

        Returns:
            Dictionary with tokens used, cost, and cache stats
        """
        return {
            "total_tokens": self.total_tokens_used,
            "total_cost_usd": round(self.total_api_cost, 4),
            "model": "deepseek-chat",
            "cache_size": len(self.image_cache) if self.enable_cache else 0,
            "cache_enabled": self.enable_cache,
            "errors_count": len(self.processing_errors),
        }

    def clear_cache(self):
        """Clear the image processing cache."""
        if self.enable_cache:
            self.image_cache.clear()

    def reset_usage_tracking(self):
        """Reset token and cost tracking counters."""
        self.total_tokens_used = 0
        self.total_api_cost = 0.0
        self.processing_errors = []
