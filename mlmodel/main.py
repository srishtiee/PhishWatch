import uvicorn
import joblib
import re
import email
import pandas as pd
import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel
from email.policy import default
from bs4 import BeautifulSoup # For parsing HTML
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.sparse import hstack, csr_matrix
import warnings

THRESHOLD = 0.75 #THRESHOLD FOR CLASSIFYING AS PHISHING

# Initialize FastAPI App
app = FastAPI(title="Phishing Detection API", version="1.0")
warnings.filterwarnings('ignore')

#Loading All Model Tools on Startup
try:
    print("Loading model and feature tools...")
    model = joblib.load('phishing_model.joblib')
    subject_vec = joblib.load('subject_vectorizer.joblib')
    body_vec = joblib.load('body_vectorizer.joblib')
    heuristic_cols = joblib.load('heuristic_columns.joblib')
    print("All tools loaded successfully.")
except FileNotFoundError:
    print("ERROR: Model or tool files not found.")
    print("Make sure all .joblib files are in the same directory.")
    model = None

#Feature Engineering Pipeline
def get_domain(email_address):
    if not isinstance(email_address, str):
        return None
    match = re.search(r'@([\w.-]+)', email_address)
    if match:
        return match.group(1).lower()
    return None

def get_body_and_subject(raw_email):
    subject = None
    body = None
    is_html = 0
    try:
        msg = email.message_from_bytes(raw_email.encode('latin-1'), policy=default)
        subject = str(msg.get('Subject', ''))
        
        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                cdispo = str(part.get('Content-Disposition'))
                if ctype == 'text/plain' and 'attachment' not in cdispo:
                    charset = part.get_content_charset() or 'latin-1'
                    body = part.get_payload(decode=True).decode(charset, errors='ignore')
                    break
            if body is None:
                for part in msg.walk():
                    ctype = part.get_content_type()
                    cdispo = str(part.get('Content-Disposition'))
                    if ctype == 'text/html' and 'attachment' not in cdispo:
                        is_html = 1
                        charset = part.get_content_charset() or 'latin-1'
                        html_body = part.get_payload(decode=True).decode(charset, errors='ignore')
                        soup = BeautifulSoup(html_body, 'html.parser')
                        body = soup.get_text()
                        break
        else:
            ctype = msg.get_content_type()
            if ctype == 'text/html':
                is_html = 1
                charset = msg.get_content_charset() or 'latin-1'
                html_body = msg.get_payload(decode=True).decode(charset, errors='ignore')
                soup = BeautifulSoup(html_body, 'html.parser')
                body = soup.get_text()
            elif ctype == 'text/plain':
                charset = msg.get_content_charset() or 'latin-1'
                body = msg.get_payload(decode=True).decode(charset, errors='ignore')
            else:
                body = msg.get_payload(decode=True)
                if isinstance(body, bytes):
                    body = body.decode('latin-1', errors='ignore')
        if body is None:
            body = ""
    except Exception:
        subject, body = "", ""
    return subject, body, is_html

SPAM_KEYWORDS = [
    'free', 'viagra', 'money', 'urgent', 'win', 'winner', 'limited time', 
    'action required', 'account', 'verification', 'congratulations', 'click here',
    'unsubscribe', 'spam', 'mlm', 'leads', 'cheap'
]
SPAM_REGEX = re.compile(r'\b(' + '|'.join(SPAM_KEYWORDS) + r')\b', re.IGNORECASE)
OBFUSCATION_REGEX = re.compile(r'\w\s+\w\s+\w')

def extract_all_features(raw_email):
    """
    This is the "inference" pipeline.
    It takes ONE raw email string and returns a DataFrame row of features.
    """
    features = {}
    try:
        msg = email.message_from_bytes(raw_email.encode('latin-1'), policy=default)
        subject, body, is_html = get_body_and_subject(raw_email)
    except Exception:
        subject, body, is_html = "", "", 0
        msg = email.message_from_string("")
    
    features['subject'] = subject
    features['body'] = body
    
    #Header Heuristics
    received_headers = msg.get_all('Received', [])
    features['hop_count'] = len(received_headers)
    from_addr = msg.get('From', '')
    reply_to = msg.get('Reply-To', '')
    features['is_mismatch'] = 1 if (get_domain(from_addr) and get_domain(reply_to) and get_domain(from_addr) != get_domain(reply_to)) else 0
    features['has_x_mailer'] = 1 if msg.get('X-Mailer') else 0
    features['has_message_id'] = 1 if msg.get('Message-ID') else 0
    
    #Content Heuristics
    features['is_html'] = is_html
    features['link_count'] = body.count('http://') + body.count('https://') + body.count('href=')
    features['keyword_count'] = len(SPAM_REGEX.findall(body))
    features['obfuscation_count'] = len(OBFUSCATION_REGEX.findall(body))
    features['subject_all_caps'] = 1 if (subject and subject.isupper() and len(subject) > 5) else 0
    return pd.DataFrame([features])


class EmailInput(BaseModel):
    raw_email: str

class PredictionOutput(BaseModel):
    is_phishing: bool
    phishing_probability: float

#End Point
@app.post("/predict", response_model=PredictionOutput)
async def predict_phishing(email_input: EmailInput):
    """
    The main prediction endpoint.
    Takes a raw email string and returns a phishing probability.
    """
    if not model:
        return {"error": "Model not loaded. Please check server logs."}

    # 1. Get raw email from the request
    raw_email_text = email_input.raw_email
    
    # 2. Process the single email using our feature pipeline
    features_df = extract_all_features(raw_email_text)
    
    # 3. Vectorize the text parts
    subject_features = subject_vec.transform(features_df['subject'])
    body_features = body_vec.transform(features_df['body'])
    
    # 4. Get the heuristic parts
    # Ensure columns are in the *exact* same order as training
    heuristic_features = csr_matrix(features_df[heuristic_cols].astype(float).values)
    
    # 5. Combine all features into one vector
    X_new = hstack([subject_features, body_features, heuristic_features])
    
    # 6. Get probability prediction
    # model.predict_proba() returns: [[prob_ham, prob_spam]]
    probability = model.predict_proba(X_new)[0][1] # Get prob_spam
    
    # 7. Get boolean prediction
    is_phish = bool(probability > THRESHOLD) # Use a 70% threshold
    
    # 8. Return the result
    return PredictionOutput(
        is_phishing=is_phish,
        phishing_probability=float(probability)
    )

# --- 6. Run the API Server ---
if __name__ == "__main__":
    # This makes the script runnable with `python main.py`
    # For development, use: uvicorn main:app --reload
    uvicorn.run(app, host="0.0.0.0", port=8000)