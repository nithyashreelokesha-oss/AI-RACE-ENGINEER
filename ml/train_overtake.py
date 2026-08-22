import os
import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
    accuracy_score
)


# ============================================================
# FILE PATHS
# ============================================================

ML_FOLDER = os.path.dirname(
    os.path.abspath(__file__)
)

DATASET_FILE = os.path.join(
    ML_FOLDER,
    "overtake_dataset.csv"
)

MODEL_FILE = os.path.join(
    ML_FOLDER,
    "overtake_model.pkl"
)


# ============================================================
# FEATURES
# ============================================================

FEATURES = [

    "lap",
    "sector",
    "position",

    "battery",

    "gap_ahead",
    "gap_behind",

    "tyre_advantage",
    "pace_advantage",

    "overtake_opportunity",
    "future_opportunity",

    "threat_level",

    "sector_type",
    "sector_energy_demand",
    "sector_overtaking_base",
    "sector_braking_importance",
    "sector_traction_importance",

    "deployment_mode",
    "recommendation"
]


TARGET = "overtake_success"


# ============================================================
# LOAD DATASET
# ============================================================

print()
print("=" * 70)
print("AI OVERTAKE MODEL TRAINING")
print("=" * 70)

df = pd.read_csv(
    DATASET_FILE
)

print()
print(f"Dataset rows: {len(df)}")


# ============================================================
# CHECK DATASET
# ============================================================

missing_columns = [
    column
    for column in FEATURES + [TARGET]
    if column not in df.columns
]

if missing_columns:

    print()
    print("ERROR: Missing columns:")
    print(missing_columns)
    raise ValueError(
        "Dataset does not contain all required columns."
    )


# Remove rows with missing target

df = df.dropna(
    subset=[TARGET]
)


# ============================================================
# CLASS DISTRIBUTION
# ============================================================

successful = int(
    df[TARGET].sum()
)

failed = int(
    len(df) - successful
)

print()
print("=" * 70)
print("CLASS DISTRIBUTION")
print("=" * 70)

print(
    f"Successful overtakes : {successful}"
)

print(
    f"Non-overtakes        : {failed}"
)

print(
    f"Success rate         : "
    f"{successful / len(df) * 100:.2f}%"
)


# ============================================================
# FEATURES / TARGET
# ============================================================

X = df[FEATURES]

y = df[TARGET]


# ============================================================
# CATEGORICAL FEATURES
# ============================================================

categorical_features = [

    "sector_type",
    "deployment_mode",
    "recommendation"
]


numeric_features = [

    feature
    for feature in FEATURES
    if feature not in categorical_features
]


# ============================================================
# PREPROCESSOR
# ============================================================

preprocessor = ColumnTransformer(

    transformers=[

        (
            "categorical",

            OneHotEncoder(
                handle_unknown="ignore"
            ),

            categorical_features
        ),

        (
            "numeric",

            "passthrough",

            numeric_features
        )
    ]
)


# ============================================================
# RANDOM FOREST
# ============================================================

model = RandomForestClassifier(

    # More trees = more stable predictions
    n_estimators=500,

    # Prevent extremely complex trees
    max_depth=10,

    # Smaller leaf allows the model to learn
    # meaningful race-state differences
    min_samples_leaf=2,

    # Standard RF feature selection
    max_features="sqrt",

    # Important because overtakes are usually
    # less frequent than non-overtakes
    class_weight="balanced",

    random_state=42,

    n_jobs=-1
)


# ============================================================
# PIPELINE
# ============================================================

pipeline = Pipeline(

    steps=[

        (
            "preprocessor",
            preprocessor
        ),

        (
            "model",
            model
        )
    ]
)


# ============================================================
# TRAIN / TEST SPLIT
# ============================================================

X_train, X_test, y_train, y_test = (
    train_test_split(

        X,
        y,

        test_size=0.20,

        random_state=42,

        stratify=y
    )
)


print()
print("=" * 70)
print("TRAIN / TEST SPLIT")
print("=" * 70)

print(
    f"Training samples : {len(X_train)}"
)

print(
    f"Testing samples  : {len(X_test)}"
)


# ============================================================
# TRAIN
# ============================================================

print()
print("=" * 70)
print("TRAINING RANDOM FOREST")
print("=" * 70)

pipeline.fit(
    X_train,
    y_train
)

print()
print("Training complete.")


# ============================================================
# PREDICTIONS
# ============================================================

predictions = pipeline.predict(
    X_test
)

probabilities = pipeline.predict_proba(
    X_test
)[:, 1]


# ============================================================
# EVALUATION
# ============================================================

print()
print("=" * 70)
print("MODEL EVALUATION")
print("=" * 70)


# ------------------------------------------------------------
# Accuracy
# ------------------------------------------------------------

accuracy = accuracy_score(
    y_test,
    predictions
)

print()
print(
    f"Accuracy: {accuracy:.4f}"
)


# ------------------------------------------------------------
# Classification report
# ------------------------------------------------------------

print()
print("Classification Report:")

print(
    classification_report(
        y_test,
        predictions,
        zero_division=0
    )
)


# ------------------------------------------------------------
# Confusion matrix
# ------------------------------------------------------------

print()
print("Confusion Matrix:")

print(
    confusion_matrix(
        y_test,
        predictions
    )
)


# ------------------------------------------------------------
# ROC-AUC
# ------------------------------------------------------------

try:

    auc = roc_auc_score(
        y_test,
        probabilities
    )

    print()
    print(
        f"ROC-AUC: {auc:.4f}"
    )

except ValueError:

    print()
    print(
        "ROC-AUC could not be calculated."
    )


# ============================================================
# PROBABILITY RANGE
# ============================================================

print()
print("=" * 70)
print("PREDICTION PROBABILITY CHECK")
print("=" * 70)

print(
    f"Minimum probability : "
    f"{probabilities.min() * 100:.2f}%"
)

print(
    f"Maximum probability : "
    f"{probabilities.max() * 100:.2f}%"
)

print(
    f"Average probability : "
    f"{probabilities.mean() * 100:.2f}%"
)


# ============================================================
# SAMPLE PREDICTIONS
# ============================================================

print()
print("=" * 70)
print("SAMPLE ML PREDICTIONS")
print("=" * 70)

sample_count = min(
    10,
    len(X_test)
)

sample_results = pd.DataFrame({

    "Actual":
        y_test.iloc[:sample_count].values,

    "Predicted":
        predictions[:sample_count],

    "Probability":
        [
            round(
                value * 100,
                2
            )
            for value in probabilities[:sample_count]
        ]
})

print(
    sample_results.to_string(
        index=False
    )
)


# ============================================================
# SAVE MODEL
# ============================================================

joblib.dump(
    pipeline,
    MODEL_FILE
)


print()
print("=" * 70)
print("MODEL SAVED")
print("=" * 70)

print(
    f"Model path:"
)

print(
    MODEL_FILE
)

print()
print("You can now run the Streamlit application.")
print()