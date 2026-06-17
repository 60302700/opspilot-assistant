import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

# Load credentials from .env
load_dotenv()

def test_email_connection():
    sender_email = os.environ.get("SENDER_EMAIL")
    sender_password = os.environ.get("SENDER_PASSWORD")
    
    print(f"Testing with Email: {sender_email}")
    
    if not sender_email or not sender_password:
        print("❌ Error: SENDER_EMAIL or SENDER_PASSWORD are not set in the .env file.")
        return

    try:
        # Using Ethereal Email directly
        sender_email = "grace.kuhlman70@ethereal.email"
        sender_password = "kSKbEAkDuzzQCUY5Ek"
        
        print("Attempting to connect to smtp.ethereal.email:587...")
        server = smtplib.SMTP("smtp.ethereal.email", 587)
        server.ehlo()
        server.starttls()
        
        print("Attempting to login...")
        server.login(sender_email, sender_password)
        print("✅ Login successful! The credentials work perfectly.")
        
        # Optionally send a quick automated test email to yourself
        msg = EmailMessage()
        msg.set_content("This is an automated test to confirm that OpsPilot SMTP functionality is working!")
        msg["Subject"] = "OpsPilot SMTP Test"
        msg["From"] = sender_email
        msg["To"] = sender_email  # Send to yourself
        
        print(f"Sending a self-test email to {sender_email}...")
        server.send_message(msg)
        print("✅ Test email sent successfully!")
        
        server.quit()
        
    except smtplib.SMTPAuthenticationError:
        print("❌ Authentication failed! Check if your password is correct. If you have 2FA enabled, you MUST use an App Password generated from your Microsoft account.")
    except Exception as e:
        print(f"❌ Connection or sending error: {str(e)}")

if __name__ == "__main__":
    test_email_connection()
