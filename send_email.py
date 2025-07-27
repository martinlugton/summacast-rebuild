import os
import requests
from dotenv import load_dotenv

load_dotenv()

def send_email(subject, text_body, html_body):
    api_key = os.getenv("AHASEND_API_KEY")
    sender_email = os.getenv("SENDER_EMAIL")
    recipient_email = os.getenv("RECIPIENT_EMAIL")
    sender_name = "Summacast" # Default sender name

    if not all([api_key, sender_email, recipient_email]):
        print("Error: Missing environment variables. Please check your .env file.")
        return

    email = {
        'from': {
            'name': sender_name,
            'email': sender_email,
        },
        'recipients': [
            {
                'name': 'Podcast Listener', # This could be customized later
                'email': recipient_email,
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
        print("Email sent successfully!")
        print(r.json())
    except requests.exceptions.RequestException as e:
        print(f"Error sending email: {e}")
        if e.response:
            print(e.response.text)


if __name__ == '__main__':
    send_email(
        "Test Email from Summacast",
        "This is a test email from the summacast-rebuild project.",
        "<p>This is the <b>HTML</b> body of the test email.</p>"
    )