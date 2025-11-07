import pandas as pd
import joblib
from scipy.sparse import load_npz
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, confusion_matrix, classification_report
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

print("--- Step 3: Model Training ---")

# --- 1. Load Feature-Engineered Data ---
print("Loading 'X_features.npz' and 'y_target.pkl'...")
try:
    X_final = load_npz('X_features.npz')
    y_final = pd.read_pickle('y_target.pkl')
except FileNotFoundError:
    print("Error: 'X_features.npz' or 'y_target.pkl' not found.")
    print("Please run the Step 2 (create_features.py) script first.")
    exit()

print(f"Data loaded. Feature matrix shape: {X_final.shape}")

# --- 2. Split Data into Training and Testing Sets ---
print("Splitting data into training and testing sets (80/20 split)...")
# We'll use 80% of the data to train the model,
# and 20% to test how well it learned.
X_train, X_test, y_train, y_test = train_test_split(
    X_final, 
    y_final, 
    test_size=0.2, 
    random_state=42, # For reproducible results
    stratify=y_final  # Ensures train/test have same % of spam/ham
)

print(f"Training samples: {X_train.shape[0]}, Testing samples: {X_test.shape[0]}")

# --- 3. Choose and Train the Model ---
print("Training Logistic Regression model...")

# Why LogisticRegression? 
# 1. It's very fast.
# 2. It works great with sparse, high-dimensional text data.
# 3. It directly outputs the probabilities (e.g., "92% sure this is spam")
#    that your API contract requires.
model = LogisticRegression(solver='liblinear', random_state=42)

# This is the "learning" step!
model.fit(X_train, y_train)

print("Model training complete.")

# --- 4. Evaluate the Model ---
print("\n--- Model Evaluation ---")
print("Evaluating model performance on the (unseen) test set...")

# Get predictions on the 20% of data it's never seen before
y_pred = model.predict(X_test)

# Calculate key metrics
accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred)
recall = recall_score(y_test, y_pred)

print("\n--- Key Metrics ---")
print(f"  Accuracy: {accuracy * 100:.2f}%")
print(f"             (How many emails (spam or ham) did we classify correctly?)\n")

print(f"  Precision: {precision * 100:.2f}%")
print(f"             (Of all emails we flagged as SPAM, what % were *actually* spam?)\n")

print(f"  Recall: {recall * 100:.2f}%")
print(f"             (Of all *actual* SPAM emails, what % did we successfully *catch*?)\n")


# A high Precision is critical: It means you have few "False Positives."
# A "False Positive" is when you mark a legitimate email (from your boss)
# as spam. This is the worst-case scenario. We want precision to be high!

print("--- Detailed Classification Report ---")
# This report gives you all the metrics in one place
print(classification_report(y_test, y_pred, target_names=['Ham (0)', 'Spam (1)']))


# --- 5. Save the Trained Model ---
print("--- Saving the Model ---")
# This is the final, most important file.
# It contains the trained "brain" of your entire project.
model_filename = 'phishing_model.joblib'
joblib.dump(model, model_filename)

print(f"Successfully trained and saved model as '{model_filename}'")
print("\n--- All Steps Complete! ---")