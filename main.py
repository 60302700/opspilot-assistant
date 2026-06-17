import json
import os
import smtplib
from email.message import EmailMessage
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import chromadb

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyC6k89OPo_46j4yIbzVuGlOQCBWDFa83Xc")
genai.configure(api_key=GEMINI_API_KEY)

# ChromaDB
chroma_client = chromadb.Client()
collection = chroma_client.create_collection(name="business_data")

def load_data():
    docs = []
    ids = []
    # clients
    with open("data/clients.json", "r") as f:
        clients = json.load(f)
        for c in clients:
            docs.append(f"Client: {c['name']}, Industry: {c['industry']}, Status: {c['status']}, Spend: {c['total_spend']}, Contact: {c['contact']}")
            ids.append(f"client_{c['client_id']}")
    # invoices
    with open("data/invoices.json", "r") as f:
        invoices = json.load(f)
        for i in invoices:
            docs.append(f"Invoice {i['invoice_id']} for Client {i['client_id']}, Amount: {i['amount']}, Status: {i['status']}, Date: {i['date']}")
            ids.append(f"invoice_{i['invoice_id']}")
    # tickets
    with open("data/tickets.json", "r") as f:
        tickets = json.load(f)
        for t in tickets:
            docs.append(f"Ticket {t['ticket_id']} for Client {t['client_id']}, Subject: {t['subject']}, Status: {t['status']}, Priority: {t['priority']}")
            ids.append(f"ticket_{t['ticket_id']}")
    # emails
    with open("data/emails.json", "r") as f:
        emails = json.load(f)
        for e in emails:
            docs.append(f"Email {e['email_id']} for Client {e['client_id']}, From: {e['from']}, Subject: {e['subject']}, Body: {e['body']}, Date: {e['date']}")
            ids.append(f"email_{e['email_id']}")
            
    collection.add(
        documents=docs,
        ids=ids
    )

load_data()

# Tools
def search_company_data(query: str) -> str:
    """Useful to search for any company data, clients, invoices, etc. in the RAG system."""
    results = collection.query(query_texts=[query], n_results=5)
    return str(results['documents'])

def get_client(client_name: str) -> str:
    """Get details for a specific client."""
    with open("data/clients.json") as f:
        clients = json.load(f)
    for c in clients:
        if client_name.lower() in c['name'].lower():
            return str(c)
    return "Client not found."

def get_client_invoices(client_name: str) -> str:
    """Get invoices for a given client name."""
    client_str = get_client(client_name)
    if "not found" in client_str: return "Client not found."
    client = eval(client_str)
    cid = client["client_id"]
    with open("data/invoices.json") as f:
        invoices = json.load(f)
    return str([i for i in invoices if i["client_id"] == cid])

def get_client_tickets(client_name: str) -> str:
    """Get support tickets for a given client name."""
    client_str = get_client(client_name)
    if "not found" in client_str: return "Client not found."
    client = eval(client_str)
    cid = client["client_id"]
    with open("data/tickets.json") as f:
        tickets = json.load(f)
    return str([t for t in tickets if t["client_id"] == cid])

def get_client_emails(client_name: str) -> str:
    """Get emails for a given client name."""
    client_str = get_client(client_name)
    if "not found" in client_str: return "Client not found."
    client = eval(client_str)
    cid = client["client_id"]
    with open("data/emails.json") as f:
        emails = json.load(f)
    return str([e for e in emails if e["client_id"] == cid])

def send_email(recipient: str, subject: str, body: str) -> str:
    """Send an email to a recipient using SMTP."""
    sender_email = os.environ.get("SENDER_EMAIL")
    sender_password = os.environ.get("SENDER_PASSWORD")
    
    if not sender_email or not sender_password:
        print(f"Mock email sent to {recipient}: {subject}")
        return f"Warning: SENDER_EMAIL or SENDER_PASSWORD not set in environment. Mock email sent to {recipient}."

    try:
        msg = EmailMessage()
        msg.set_content(body + "\n\n" + recipient)
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = sender_email

        # Using Ethereal Email directly 
        smtp_server = "smtp.ethereal.email"
        smtp_port = 465  # Using SSL port (often works better on Render/Cloud if 587 is blocked)
        
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        return "Email sent successfully via SMTP SSL."
    except Exception as e:
        return f"Error sending email: {str(e)}"

# create the model with tools
tools = [
     search_company_data, 
     get_client, 
     get_client_invoices, 
     get_client_tickets, 
     get_client_emails, 
     send_email
]
agent_model = genai.GenerativeModel("gemini-3.1-flash-lite", tools=tools, system_instruction="""
You are an AI business operations assistant called OpsPilot.
Act like a business operations analyst. 
Always use retrieved data before answering. Do not answer questions not related to business operations.
Never hallucinate business data. Provide structured responses using:
- Summary
- Key Data 
- Insights
- Actions
""")

chat_session = agent_model.start_chat(enable_automatic_function_calling=True)

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    try:
        response = chat_session.send_message(req.message)
        return {"response": response.text}
    except Exception as e:
        return {"error": str(e)}

app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
