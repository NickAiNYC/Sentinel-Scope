"""OutreachAgent: Triggers notifications to supervisors for compliance gaps."""
from datetime import datetime
from typing import List, Optional, Protocol

from packages.sentinel.models import ComplianceGap, DecisionProof


class NotificationInterface(Protocol):
    """Protocol for notification service."""
    
    def send_notification(self, recipient: str, subject: str, message: str) -> bool:
        """Send notification to recipient."""
        ...


class MockNotificationService:
    """
    Mock notification service.
    Replace this with actual notification implementation (email, SMS, Slack, etc.).
    """
    
    def send_notification(self, recipient: str, subject: str, message: str) -> bool:
        """
        Mock notification that simulates sending.
        In production, implement actual notification delivery.
        
        Args:
            recipient: Notification recipient (email, phone, user ID, etc.)
            subject: Notification subject/title
            message: Notification message content
            
        Returns:
            True if successful, False otherwise
        """
        # Log the notification (in production, actually send it)
        print(f"[NOTIFICATION] To: {recipient}")
        print(f"[NOTIFICATION] Subject: {subject}")
        print(f"[NOTIFICATION] Message: {message}")
        print("-" * 60)
        return True


class OutreachAgent:
    """
    OutreachAgent triggers notifications to supervisors when compliance gaps are detected.
    """
    
    def __init__(
        self, 
        notification_service: NotificationInterface | None = None,
        supervisor_contact: str = "supervisor@example.com"
    ):
        """
        Initialize OutreachAgent with notification service.
        
        Args:
            notification_service: Service for sending notifications.
                                If None, uses MockNotificationService.
            supervisor_contact: Contact information for supervisor notifications
        """
        self.notification_service = notification_service or MockNotificationService()
        self.supervisor_contact = supervisor_contact
    
    def _format_gap_message(self, gap: ComplianceGap) -> str:
        """
        Format compliance gap into human-readable message.
        
        Args:
            gap: Compliance gap to format
            
        Returns:
            Formatted message string
        """
        message = f"""
COMPLIANCE GAP DETECTED

Severity: {gap.severity}
Gap Type: {gap.gap_type}
Description: {gap.description}

Entity Details:
- Type: {gap.entity.entity_type}
- Name/ID: {gap.entity.name}
- Location: {gap.entity.location}
- Detected At: {gap.detected_at.strftime('%Y-%m-%d %H:%M:%S')}
- Detection Confidence: {gap.entity.confidence:.2%}

Compliance Status:
- Insurance: {gap.compliance_status.insurance_status}
- Certification: {gap.compliance_status.certification_status}
- Notes: {gap.compliance_status.compliance_notes}

IMMEDIATE ACTION REQUIRED
Please review and address this compliance gap immediately.
"""
        return message
    
    def notify_gap(self, gap: ComplianceGap) -> bool:
        """
        Send notification for a single compliance gap.
        
        Args:
            gap: Compliance gap to notify about
            
        Returns:
            True if notification sent successfully
        """
        subject = f"🚨 {gap.severity} Compliance Gap: {gap.gap_type}"
        message = self._format_gap_message(gap)
        
        return self.notification_service.send_notification(
            recipient=self.supervisor_contact,
            subject=subject,
            message=message
        )
    
    def notify_multiple_gaps(self, gaps: list[ComplianceGap]) -> dict:
        """
        Send notifications for multiple compliance gaps.
        
        Args:
            gaps: List of compliance gaps
            
        Returns:
            Dictionary with notification results
        """
        results = {
            'total': len(gaps),
            'successful': 0,
            'failed': 0,
            'details': []
        }
        
        for gap in gaps:
            success = self.notify_gap(gap)
            if success:
                results['successful'] += 1
            else:
                results['failed'] += 1
            
            results['details'].append({
                'gap_id': gap.gap_id,
                'gap_type': gap.gap_type,
                'severity': gap.severity,
                'notification_sent': success
            })
        
        return results
    
    def notify_critical_gaps_only(self, gaps: list[ComplianceGap]) -> dict:
        """
        Send notifications only for critical severity gaps.
        
        Args:
            gaps: List of compliance gaps
            
        Returns:
            Dictionary with notification results
        """
        critical_gaps = [gap for gap in gaps if gap.severity == "Critical"]
        return self.notify_multiple_gaps(critical_gaps)
    
    def create_notification_summary(self, gaps: list[ComplianceGap]) -> str:
        """
        Create a summary notification for multiple gaps.
        
        Args:
            gaps: List of compliance gaps
            
        Returns:
            Summary message string
        """
        if not gaps:
            return "No compliance gaps detected."
        
        # Group by severity
        severity_counts = {}
        for gap in gaps:
            severity_counts[gap.severity] = severity_counts.get(gap.severity, 0) + 1
        
        summary = f"""
COMPLIANCE GAPS SUMMARY

Total Gaps Detected: {len(gaps)}

Breakdown by Severity:
"""
        for severity in ['Critical', 'High', 'Medium', 'Low']:
            count = severity_counts.get(severity, 0)
            if count > 0:
                summary += f"- {severity}: {count}\n"
        
        summary += "\nDetailed Gaps:\n"
        for i, gap in enumerate(gaps, 1):
            summary += f"\n{i}. {gap.gap_type} ({gap.severity})\n"
            summary += f"   Entity: {gap.entity.entity_type} - {gap.entity.name}\n"
            summary += f"   Location: {gap.entity.location}\n"
        
        return summary
    
    def send_summary_notification(self, gaps: list[ComplianceGap]) -> bool:
        """
        Send a single summary notification for all gaps.
        
        Args:
            gaps: List of compliance gaps
            
        Returns:
            True if notification sent successfully
        """
        if not gaps:
            return False
        
        subject = f"🚨 Compliance Alert: {len(gaps)} Gap(s) Detected"
        message = self.create_notification_summary(gaps)
        
        return self.notification_service.send_notification(
            recipient=self.supervisor_contact,
            subject=subject,
            message=message
        )
