import os
import pandas as pd
from tqdm import tqdm

BASE_DIR = './dataset/' 

# 0 = ham (not spam), 1 = spam
DATA_DIRS = {
    'easy_ham': 0,
    'hard_ham': 0,
    'spam_2': 1
}

def load_emails_from_folder(folder_path, label):
    """Reads all files in a folder and returns a list of dictionaries."""
    print(f"Processing folder: {folder_path}...")
    emails = []    
    # Get all filenames in the directory
    try:
        filenames = os.listdir(folder_path)
    except FileNotFoundError:
        print(f"Error: Folder not found at {folder_path}")
        return []
    
    # Using tqdm for a progress bar
    for filename in tqdm(filenames):
        # Skipping hidden files like .DS_Store
        if filename.startswith('.'):
            continue
            
        file_path = os.path.join(folder_path, filename)
        try:
            with open(file_path, 'rb') as f:
                content = f.read().decode('latin-1')
                emails.append({
                    'message': content,
                    'label': label
                })
        except Exception as e:
            print(f"Warning: Could not read file {filename}. Error: {e}")
    return emails

def main():
    print("Step 1: Building Master SpamAssassin Dataset")
    all_emails = []
    for folder_name, label in DATA_DIRS.items():
        folder_path = os.path.join(BASE_DIR, folder_name)
        all_emails.extend(load_emails_from_folder(folder_path, label))
        
    if not all_emails:
        print("No emails were loaded. Exiting.")
        return

    print("Converting to DataFrame...")
    df = pd.DataFrame(all_emails)
    
    # Shuffling the dataset to mix spam and ham
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    output_filename = 'spamassassin_master.csv'
    print(f"\nSaving to '{output_filename}'...")
    df.to_csv(output_filename, index=False, encoding='utf-8')
    
    print("\n--- Success! ---")
    print(f"Created '{output_filename}' with {len(df)} total emails.")
    print("\nLabel Distribution:")
    print(df['label'].value_counts())
    
    print("\nDataFrame Head:")
    print(df.head())

if __name__ == "__main__":
    main()