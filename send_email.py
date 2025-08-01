import os
import requests
from dotenv import load_dotenv
import logging

# Configure logging for this module
logger = logging.getLogger(__name__)

load_dotenv()

from flask import render_template

def send_email(subject, text_body, summary_content, podcast_name, episode_title, published_date, recipient_email=None):
    api_key = os.getenv("AHASEND_API_KEY")
    sender_email = os.getenv("SENDER_EMAIL")
    default_recipient_email = os.getenv("RECIPIENT_EMAIL")
    sender_name = "Summacast" # Default sender name

    recipient = recipient_email if recipient_email else default_recipient_email

    if not all([api_key, sender_email, default_recipient_email]):
        logger.error("Error: Missing environment variables. Please check your .env file.")
        return False

    # Render the HTML email template
    html_body = render_template(
        'email_summary_template.html',
        podcast_name=podcast_name,
        episode_title=episode_title,
        published_date=published_date,
        summary_content=summary_content
    )

    email = {
        'from': {
            'name': sender_name,
            'email': sender_email,
        },
        'recipients': [
            {
                'name': 'Podcast Listener', # This could be customized later
                'email': recipient,
            }
        ],
        'content': {
            'subject': subject,
            'text_body': text_body,
            'html_body': html_body,
        },
    }
    headers = {
        'X-Api-Key': api_key,
        'Content-Type': 'application/json'
    }
    
    try:
        r = requests.post('https://api.ahasend.com/v1/email/send', json=email, headers=headers)
        r.raise_for_status()
        logger.info("Email sent successfully!")
        logger.info(r.json())
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending email: {e}")
        if e.response:
            logger.error(f"AhaSend API response: {e.response.text}")
        return False


if __name__ == '__main__':
    send_email(
        "Test Email from Summacast",
        "This is a test email from the summacast-rebuild project.",
        "<p>This is the <b>HTML</b> body of the test email.</p>"
    )