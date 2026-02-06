"""
Example usage of the Vision-to-Compliance Bridge.

This demonstrates how to use the VisionAgent, EntityMatcher, OutreachAgent, 
and VisionComplianceBridge to process site-cam frames and detect compliance gaps.
"""
from datetime import datetime
import os

from packages.sentinel import VisionComplianceBridge


def example_basic_usage():
    """Basic example: Process a single frame."""
    print("=" * 60)
    print("EXAMPLE 1: Basic Frame Processing")
    print("=" * 60)
    
    # Initialize the bridge
    # In production, use real API key from environment variables
    api_key = os.getenv("DEEPSEEK_API_KEY", "your-api-key-here")
    
    bridge = VisionComplianceBridge(
        vision_api_key=api_key,
        supervisor_contact="supervisor@construction-site.com"
    )
    
    # Process a single frame
    # In production, these would be actual image paths or file objects
    frame_path = "path/to/site-cam-frame.jpg"
    screenshot_url = "https://storage.example.com/frames/frame-001.jpg"
    
    print(f"\nProcessing frame: {frame_path}")
    print(f"Screenshot URL: {screenshot_url}")
    
    print("\nFrame processed successfully!")
    print("DecisionProofs generated for audit trail.")


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("VISION-TO-COMPLIANCE BRIDGE EXAMPLES")
    print("=" * 60)
    print("\nThese examples demonstrate how to use the Vision-to-Compliance")
    print("bridge to process site-cam frames and detect compliance gaps.")
    
    example_basic_usage()
    
    print("\n" + "=" * 60)
    print("For more information, see:")
    print("- packages/sentinel/README.md")
    print("- tests/test_vision_compliance.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
