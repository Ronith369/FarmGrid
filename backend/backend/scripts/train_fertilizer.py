import sys
from pathlib import Path
import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

FEATURES = [
    "location", "crop", "soil_type", "soil_color",
    "moisture", "water_availability", "previous_crop", "previous_yield"
]
TARGET = "fertilizer"


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/train_fertilizer.py data/fertilizer_training.csv")

    df = pd.read_csv(sys.argv[1])
    missing = [c for c in FEATURES + [TARGET] if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    cat = ["location", "crop", "soil_type", "soil_color", "previous_crop"]
    num = ["moisture", "water_availability", "previous_yield"]

    preprocess = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
        ("num", "passthrough", num),
    ])

    pipe = Pipeline([
        ("preprocess", preprocess),
        ("model", RandomForestClassifier(
            n_estimators=300, random_state=42, class_weight="balanced"
        )),
    ])

    if len(df) < 10 or df[TARGET].nunique() < 2:
        pipe.fit(df[FEATURES], df[TARGET])
        print("Demo dataset is small; fitted on all rows. Training accuracy:", pipe.score(df[FEATURES], df[TARGET]))
    else:
        X_train, X_test, y_train, y_test = train_test_split(
            df[FEATURES], df[TARGET], test_size=0.2, random_state=42, stratify=df[TARGET]
        )
        pipe.fit(X_train, y_train)
        print("Test accuracy:", pipe.score(X_test, y_test))

    out = Path("app/ml/artifacts/fertilizer_pipeline.joblib")
    out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, out)
    print("Saved", out)


if __name__ == "__main__":
    main()
