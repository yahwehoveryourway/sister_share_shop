import os
from flask import current_app, render_template_string
from flask_mail import Message
from app import mail

def send_thank_you_email(donation):
    """Send automated thank you email to donor"""
    try:
        subject = f"Thank you for your donation: {donation.title}"
        body = f"""
        Dear {donation.donor.username},

        Thank you so much for your generous donation of "{donation.title}" to Sister Share Shop!

        Your kindness makes a real difference in our community. Your donated item has been matched with someone who truly needs it.

        Item Details:
        - Title: {donation.title}
        - Category: {donation.category.name}
        - Donated on: {donation.donated_at.strftime('%B %d, %Y') if donation.donated_at else 'Recently'}

        We are grateful for your support and generosity. Together, we're building a stronger, more caring community.

        With heartfelt appreciation,
        The Sister Share Shop Team

        ---
        This is an automated message. Please do not reply to this email.
        """

        msg = Message(
            subject=subject,
            recipients=[donation.donor.email],
            body=body
        )
        
        mail.send(msg)
        current_app.logger.info(f"Thank you email sent to {donation.donor.email} for donation {donation.id}")
        return True
        
    except Exception as e:
        current_app.logger.error(f"Failed to send thank you email: {str(e)}")
        return False

def send_match_notification(donation, request, match):
    """Send notification emails when items are matched"""
    try:
        # Email to donor
        donor_subject = f"Your donation has been matched: {donation.title}"
        donor_body = f"""
        Dear {donation.donor.username},

        Great news! Your donation of "{donation.title}" has been matched with someone who needs it.

        This means your generous gift is now making a direct impact in someone's life. Thank you for being part of the Sister Share Shop community!

        Donation Details:
        - Item: {donation.title}
        - Category: {donation.category.name}
        - Matched on: {match.created_at.strftime('%B %d, %Y')}

        Your kindness is truly appreciated.

        Best regards,
        The Sister Share Shop Team
        """

        donor_msg = Message(
            subject=donor_subject,
            recipients=[donation.donor.email],
            body=donor_body
        )

        # Email to requester
        requester_subject = f"Your request has been fulfilled: {request.title}"
        requester_body = f"""
        Dear {request.requester.username},

        Wonderful news! We found a match for your request: "{request.title}"

        A generous community member has donated an item that matches your needs. You can expect to hear from our team soon about pickup or delivery arrangements.

        Request Details:
        - Item: {request.title}
        - Category: {request.category.name}
        - Matched on: {match.created_at.strftime('%B %d, %Y')}

        Thank you for being part of the Sister Share Shop community!

        Best regards,
        The Sister Share Shop Team
        """

        requester_msg = Message(
            subject=requester_subject,
            recipients=[request.requester.email],
            body=requester_body
        )

        mail.send(donor_msg)
        mail.send(requester_msg)
        
        current_app.logger.info(f"Match notification emails sent for match {match.id}")
        return True
        
    except Exception as e:
        current_app.logger.error(f"Failed to send match notification emails: {str(e)}")
        return False

def send_admin_notification(subject, message, admin_emails=None):
    """Send notification to admin users"""
    try:
        if not admin_emails:
            from models import User
            admin_users = User.query.filter_by(is_admin=True).all()
            admin_emails = [user.email for user in admin_users]
        
        if not admin_emails:
            current_app.logger.warning("No admin emails found for notification")
            return False

        msg = Message(
            subject=f"Sister Share Shop Admin: {subject}",
            recipients=admin_emails,
            body=message
        )
        
        mail.send(msg)
        current_app.logger.info(f"Admin notification sent: {subject}")
        return True
        
    except Exception as e:
        current_app.logger.error(f"Failed to send admin notification: {str(e)}")
        return False
