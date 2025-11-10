import pandas as pd
import joblib
from scipy.sparse import load_npz
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, confusion_matrix, classification_report
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

#Load Feature-Engineered Data
try:
    X_final = load_npz('X_features.npz')
    y_final = pd.read_pickle('y_target.pkl')
except FileNotFoundError:
    print("Error: 'X_features.npz' or 'y_target.pkl' not found.")
    print("Please run create_features.py script first.")
    exit()

print(f"Data loaded. Feature matrix shape: {X_final.shape}")

# Split Data
X_train, X_test, y_train, y_test = train_test_split(
    X_final, 
    y_final, 
    test_size=0.2, 
    random_state=42,
    stratify=y_final
)

print(f"Training samples: {X_train.shape[0]}, Testing samples: {X_test.shape[0]}")

model = LogisticRegression(solver='liblinear', random_state=42)
model.fit(X_train, y_train)
# Evaluate the Model
print("Model Evaluation")
y_pred = model.predict(X_test)

# Calculate key metrics
accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred)
recall = recall_score(y_test, y_pred)

print("\n--- Key Metrics ---")
print(f"  Accuracy: {accuracy * 100:.2f}%")
print(f"  Precision: {precision * 100:.2f}%")
print(f"  Recall: {recall * 100:.2f}%")

#Classification Report
print(classification_report(y_test, y_pred, target_names=['Ham (0)', 'Spam (1)']))

model_filename = 'phishing_model.joblib'
joblib.dump(model, model_filename)
print(f"saved model as '{model_filename}'")