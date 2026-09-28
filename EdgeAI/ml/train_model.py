# ml/train_model.py
# Trains and evaluates a Random Forest using StratifiedGroupKFold cross-validation.
# Why: with only 3 runs per class, a single train/test split can accidentally
# leave a whole class out of the test set (this happened - see prior run).
# Cross-validation across multiple folds ensures every run is used as a held-out
# test set at least once, and every class gets a fair, complete evaluation,
# while still respecting the group (run) boundary to prevent leakage.

import pandas as pd
import joblib
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import matplotlib.pyplot as plt
import glob
import os

from features import extract_window_features, WINDOW_SIZE
from config import RAW_DIR, MODEL_PATH, CONFUSION_MATRIX_PATH

DATA_DIR = RAW_DIR
N_SPLITS = 3   # each class has 3 runs, so 3 folds roughly holds out 1 run/class/fold


def build_features_with_groups():
    csv_files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    all_rows = []

    for filepath in csv_files:
        df = pd.read_csv(filepath)
        fault_label = df["fault_label"].iloc[0]
        group_id = os.path.basename(filepath)

        num_windows = len(df) // WINDOW_SIZE
        for i in range(num_windows):
            start = i * WINDOW_SIZE
            end = start + WINDOW_SIZE
            window_df = df.iloc[start:end]

            features = extract_window_features(window_df)
            features["fault_label"] = fault_label
            features["group_id"] = group_id
            all_rows.append(features)

    return pd.DataFrame(all_rows)


def main():
    print("Rebuilding windowed features with run/group tracking...\n")
    df = build_features_with_groups()
    print(f"Total windows: {len(df)}, from {df['group_id'].nunique()} separate runs\n")

    X = df.drop(columns=["fault_label", "group_id"])
    y = df["fault_label"]
    groups = df["group_id"]

    sgkf = StratifiedGroupKFold(n_splits=N_SPLITS, shuffle=True, random_state=42)

    all_y_true = []
    all_y_pred = []
    fold_num = 1

    for train_idx, test_idx in sgkf.split(X, y, groups=groups):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        test_runs = sorted(groups.iloc[test_idx].unique())

        print(f"--- Fold {fold_num} ---")
        print(f"Test runs: {test_runs}")
        print(f"Train: {len(X_train)} windows | Test: {len(X_test)} windows")

        model = RandomForestClassifier(
            n_estimators=200,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        fold_acc = accuracy_score(y_test, y_pred)
        print(f"Fold {fold_num} accuracy: {fold_acc:.2%}\n")

        all_y_true.extend(y_test)
        all_y_pred.extend(y_pred)
        fold_num += 1

    print("=" * 60)
    print("=== OVERALL CROSS-VALIDATED RESULTS (all folds combined) ===")
    print("=" * 60)

    overall_acc = accuracy_score(all_y_true, all_y_pred)
    print(f"\nOverall accuracy across all folds: {overall_acc:.2%}")
    print("(Every run was used as held-out test data exactly once)\n")

    print("=== Classification Report (all classes, all folds combined) ===")
    print(classification_report(all_y_true, all_y_pred))

    print("=== Confusion Matrix (all folds combined) ===")
    labels = sorted(y.unique())
    cm = confusion_matrix(all_y_true, all_y_pred, labels=labels)
    cm_df = pd.DataFrame(cm, index=labels, columns=labels)
    print(cm_df)
    print()

    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_yticklabels(labels)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title("Confusion Matrix (cross-validated, all folds)")
    for i in range(len(labels)):
        for j in range(len(labels)):
            ax.text(j, i, cm[i, j], ha="center", va="center",
                     color="white" if cm[i, j] > cm.max() / 2 else "black")
    plt.colorbar(im)
    plt.tight_layout()
    plt.savefig(CONFUSION_MATRIX_PATH)
    print(f"Saved confusion matrix plot to {CONFUSION_MATRIX_PATH}")

    # Final deployed model: trained on ALL data, now that we trust the
    # cross-validated evaluation above.
    print("\nTraining final model on all data for deployment...")
    final_model = RandomForestClassifier(
        n_estimators=200,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )
    final_model.fit(X, y)

    importances = pd.Series(final_model.feature_importances_, index=X.columns)
    top_features = importances.sort_values(ascending=False).head(15)
    print("\n=== Top 15 Most Important Features (final model) ===")
    print(top_features)

    joblib.dump(final_model, MODEL_PATH)
    print(f"\nFinal model saved to: {MODEL_PATH}")


if __name__ == "__main__":
    main()
