import pandas as pd
import email
import re
import joblib
from email.policy import default
from email.parser import Parser
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.sparse import hstack, csr_matrix
from tqdm import tqdm
import numpy as np
import warnings
import scipy

# Suppresses warnings for cleaner output
warnings.filterwarnings('ignore')
tqdm.pandas()

def get_domain(email_address):
    """Extracts the domain from an email address string."""
    if not isinstance(email_address, str):
        return None
    match = re.search(r'@([\w.-]+)', email_address)
    if match:
        return match.group(1).lower()
    return None

def get_body_and_subject(raw_email):
    """
    Parses a raw email string and extracts the Subject,
    the plain-text Body, and an is_html flag.
    """
    subject = None
    body = None
    is_html = 0
    
    try:
        #latin-1 encoding
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
            
            # If no plain text, look for HTML
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
            # Not multipart, just get the payload
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
                # Fallback for unknown non-multipart types
                body = msg.get_payload(decode=True)
                if isinstance(body, bytes):
                    body = body.decode('latin-1', errors='ignore')

        # Fallback if body is still not found
        if body is None:
            body = ""
            
    except Exception as e:
        print(f"Warning: Error parsing email - {e}")
        subject = ""
        body = ""

    return subject, body, is_html


#Master Feature Extraction Function

SPAM_KEYWORDS = [
    'free', 'viagra', 'money', 'urgent', 'win', 'winner', 'limited time', 
    'action required', 'account', 'verification', 'congratulations', 'click here',
    'unsubscribe', 'spam', 'mlm', 'leads', 'cheap'
]
SPAM_REGEX = re.compile(r'\b(' + '|'.join(SPAM_KEYWORDS) + r')\b', re.IGNORECASE)
OBFUSCATION_REGEX = re.compile(r'\w\s+\w\s+\w') # e.g., "m o n e y"

def extract_all_features(raw_email):
    """
    Takes a raw email string and extracts all our
    Header and Content features.
    """
    features = {}
    
    try:
        msg = email.message_from_bytes(raw_email.encode('latin-1'), policy=default)
        subject, body, is_html = get_body_and_subject(raw_email)
    except Exception:
        subject, body, is_html = "", "", 0
        msg = email.message_from_string("") # Create empty object
    
    features['subject'] = subject
    features['body'] = body
    received_headers = msg.get_all('Received', [])
    features['hop_count'] = len(received_headers)
    
    from_addr = msg.get('From', '')
    reply_to = msg.get('Reply-To', '')
    features['is_mismatch'] = 1 if (get_domain(from_addr) and get_domain(reply_to) and get_domain(from_addr) != get_domain(reply_to)) else 0
    
    features['has_x_mailer'] = 1 if msg.get('X-Mailer') else 0
    features['has_message_id'] = 1 if msg.get('Message-ID') else 0
    
    features['is_html'] = is_html
    features['link_count'] = body.count('http://') + body.count('https://') + body.count('href=')
    features['keyword_count'] = len(SPAM_REGEX.findall(body))
    features['obfuscation_count'] = len(OBFUSCATION_REGEX.findall(body))
    features['subject_all_caps'] = 1 if (subject and subject.isupper() and len(subject) > 5) else 0

    return pd.Series(features)


#Orchestration Script

def main():
    print("Loading spamassassin_master.csv...")
    try:
        df = pd.read_csv('./dataset/spamassassin_master.csv')
    except FileNotFoundError:
        print("Error: 'spamassassin_master.csv' not found.")
        return
        
    df.dropna(subset=['message'], inplace=True)
    print(f"Loaded {len(df)} emails.")
    
    #Feature Extraction ---
    print("Applying feature extraction to all emails...")
    features_df = df['message'].progress_apply(extract_all_features)
    df = pd.concat([df, features_df], axis=1)
    
    #Vectorize Text Features 
    df['subject'] = df['subject'].fillna('')
    df['body'] = df['body'].fillna('')

    subject_vec = TfidfVectorizer(stop_words='english', max_features=1000, ngram_range=(1,2))
    body_vec = TfidfVectorizer(stop_words='english', max_features=5000)
    
    subject_features = subject_vec.fit_transform(df['subject'])
    body_features = body_vec.fit_transform(df['body'])
    
    #Combine All Features
    heuristic_cols = [
        'hop_count', 'is_mismatch', 'has_x_mailer', 'has_message_id',
        'is_html', 'link_count', 'keyword_count', 'obfuscation_count',
        'subject_all_caps'
    ]
    
    # Convert our numeric features into a sparse matrix
    heuristic_features = csr_matrix(df[heuristic_cols].astype(float).values)
    
    # Combine all sparse matrices horizontally
    # This is our final "X" matrix
    X_final = hstack([subject_features, body_features, heuristic_features])
    
    # Our final "y" target
    y_final = df['label']
    
    print(f"Final feature matrix shape (rows, features): {X_final.shape}")
    print(f"Final target vector shape (rows,): {y_final.shape}")

    #Save All Model-Ready Files
    
    # 1. Save the final X and y files for training
    scipy.sparse.save_npz('X_features.npz', X_final)
    y_final.to_pickle('y_target.pkl')
    
    # 2. Save the "tools" our API will need for inference
    joblib.dump(subject_vec, 'subject_vectorizer.joblib')
    joblib.dump(body_vec, 'body_vectorizer.joblib')
    joblib.dump(heuristic_cols, 'heuristic_columns.joblib')
if __name__ == "__main__":
    main()