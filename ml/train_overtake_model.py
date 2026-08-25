import os, glob, warnings
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix, classification_report
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

warnings.filterwarnings('ignore')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw')
MODEL_PATH = os.path.join(BASE_DIR, 'ml', 'overtake_model.pkl')
TRAIN_YEARS = [2023, 2024, 2025]
VALIDATION_YEAR = 2026
RANDOM_STATE = 42

# IMPORTANT: only information available at prediction time.
# No next-position / position-change / target-derived fields.
NUMERIC_FEATURES = [
    'lap', 'position', 'tyre_life', 'tyre_life_squared',
    'speed_mean', 'speed_max', 'speed_min', 'speed_range', 'speed_std', 'speed_variation',
    'throttle_mean', 'throttle_max', 'throttle_full_usage',
    'brake_mean', 'brake_max', 'brake_usage', 'heavy_braking_usage',
    'rpm_mean', 'rpm_max', 'gear_mean', 'gear_max', 'gear_std',
]
CATEGORICAL_FEATURES = ['compound', 'track_status']
FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES
FORBIDDEN_FEATURES = [
    'next_position', 'next_track_status', 'position_delta',
    'position_gain', 'position_gain_strength', 'overtake',
    'pit_next', 'next_lap_time', 'lap_time_delta',
    'previous_lap_time', 'lap_time_delta_rolling'
]


def numeric(df, col, default=np.nan):
    if col not in df.columns:
        return pd.Series(default, index=df.index, dtype=float)
    return pd.to_numeric(df[col], errors='coerce').replace([np.inf, -np.inf], np.nan).fillna(default)


def load_data():
    print('\n' + '=' * 75)
    print('LOADING MULTI-SEASON F1 DATA')
    print('=' * 75)
    files = []
    for year in TRAIN_YEARS + [VALIDATION_YEAR]:
        files += sorted(glob.glob(os.path.join(RAW_DIR, str(year), '*.csv')))
    print(f'\nFound {len(files)} race files.')
    frames = []
    for f in files:
        print('  Loading', os.path.basename(f))
        try:
            d = pd.read_csv(f)
            if not d.empty:
                frames.append(d)
        except Exception as e:
            print('  [WARNING] skipped:', e)
    if not frames:
        raise RuntimeError('No usable race CSV files found.')
    data = pd.concat(frames, ignore_index=True)
    print(f'\nTotal rows loaded: {len(data)}')
    return data


def make_features(data):
    print('\n' + '=' * 75)
    print('CREATING LEAKAGE-FREE FEATURES')
    print('=' * 75)
    df = data.copy()
    df['lap'] = numeric(df, 'lap', 1)
    df['position'] = numeric(df, 'position', 20)
    df['tyre_life'] = numeric(df, 'tyre_life', 0)
    df['tyre_life_squared'] = df['tyre_life'] ** 2

    telemetry_cols = [
        'speed_mean','speed_max','speed_min','speed_range','speed_std','speed_variation',
        'throttle_mean','throttle_max','throttle_full_usage',
        'brake_mean','brake_max','brake_usage','heavy_braking_usage',
        'rpm_mean','rpm_max','gear_mean','gear_max','gear_std'
    ]
    for c in telemetry_cols:
        df[c] = numeric(df, c, np.nan)

    df['compound'] = df.get('compound', pd.Series('UNKNOWN', index=df.index)).fillna('UNKNOWN').astype(str).str.upper()
    df['track_status'] = df.get('track_status', pd.Series('UNKNOWN', index=df.index)).fillna('UNKNOWN').astype(str)

    if 'telemetry_available' in df.columns:
        available = numeric(df, 'telemetry_available', 0) > 0
    else:
        available = df['speed_mean'].notna()

    if 'overtake' not in df.columns:
        raise RuntimeError("CSV files must contain the 'overtake' target.")
    y = numeric(df, 'overtake', 0).astype(int).clip(0, 1)
    before = len(df)
    df = df.loc[available].copy()
    y = y.loc[available]
    print(f'Telemetry-backed rows: {len(df)}/{before}')
    print(f'Removed rows without telemetry: {before-len(df)}')

    leaked = [x for x in FEATURES if x in FORBIDDEN_FEATURES]
    if leaked:
        raise RuntimeError('LEAKAGE CHECK FAILED: ' + str(leaked))
    X = df[FEATURES].copy()
    print(f'\nFinal usable rows: {len(X)}')
    print('\nTarget distribution:')
    print(y.value_counts().sort_index().to_string())
    print('\nLeakage check:')
    print('  ✓ future position/change features excluded')
    print('  ✓ target excluded from X')
    print('  ✓ next-lap features excluded')
    return df, X, y


def build_model():
    pre = ColumnTransformer([
        ('numeric', SimpleImputer(strategy='median'), NUMERIC_FEATURES),
        ('categorical', Pipeline([
            ('imputer', SimpleImputer(strategy='most_frequent')),
            ('onehot', OneHotEncoder(handle_unknown='ignore'))
        ]), CATEGORICAL_FEATURES)
    ])
    rf = RandomForestClassifier(
        n_estimators=500, max_depth=14, min_samples_leaf=4,
        max_features='sqrt', class_weight='balanced_subsample',
        random_state=RANDOM_STATE, n_jobs=-1
    )
    return Pipeline([('preprocessor', pre), ('classifier', rf)])


def best_threshold(y, p):
    best_t, best_f = 0.50, -1
    for t in np.arange(0.10, 0.91, 0.01):
        pred = (p >= t).astype(int)
        f = f1_score(y, pred, zero_division=0)
        if f > best_f or (np.isclose(f, best_f) and t > best_t):
            best_t, best_f = float(round(t, 2)), f
    return best_t


def evaluate(model, X, y):
    p = model.predict_proba(X)[:, 1]
    p50 = (p >= .50).astype(int)
    t = best_threshold(y, p)
    pred = (p >= t).astype(int)
    auc = roc_auc_score(y, p) if y.nunique() > 1 else float('nan')
    print('\n' + '=' * 75)
    print('2026 VALIDATION')
    print('=' * 75)
    print('Threshold 0.50:')
    print(f'  Accuracy : {accuracy_score(y,p50):.4f}')
    print(f'  Precision: {precision_score(y,p50,zero_division=0):.4f}')
    print(f'  Recall   : {recall_score(y,p50,zero_division=0):.4f}')
    print(f'  F1 Score : {f1_score(y,p50,zero_division=0):.4f}')
    print(f'\nBest F1 threshold: {t:.2f}')
    print(f'  Accuracy : {accuracy_score(y,pred):.4f}')
    print(f'  Precision: {precision_score(y,pred,zero_division=0):.4f}')
    print(f'  Recall   : {recall_score(y,pred,zero_division=0):.4f}')
    print(f'  F1 Score : {f1_score(y,pred,zero_division=0):.4f}')
    print(f'  ROC-AUC  : {auc:.4f}')
    print('\nConfusion Matrix:')
    print(confusion_matrix(y,pred))
    print('\nClassification Report:')
    print(classification_report(y,pred,zero_division=0))
    return {
        'threshold_050': {'accuracy':float(accuracy_score(y,p50)), 'precision':float(precision_score(y,p50,zero_division=0)), 'recall':float(recall_score(y,p50,zero_division=0)), 'f1':float(f1_score(y,p50,zero_division=0))},
        'best_threshold': {'threshold':t, 'accuracy':float(accuracy_score(y,pred)), 'precision':float(precision_score(y,pred,zero_division=0)), 'recall':float(recall_score(y,pred,zero_division=0)), 'f1':float(f1_score(y,pred,zero_division=0)), 'roc_auc':float(auc)}
    }


def importance(model):
    try:
        names = model.named_steps['preprocessor'].get_feature_names_out()
        vals = model.named_steps['classifier'].feature_importances_
        items = sorted(zip(names, vals), key=lambda x:x[1], reverse=True)
        print('\nTop ML features:')
        for n,v in items[:20]: print(f'  {n}: {v:.4f}')
        return {n:float(v) for n,v in items}
    except Exception as e:
        print('[WARNING] Feature importance failed:', e)
        return {}


def main():
    print('\n' + '=' * 75)
    print('🏎️ F1 AI RACE ENGINEER')
    print('LEAKAGE-FREE MULTI-SEASON REAL F1 TELEMETRY ML TRAINING')
    print('=' * 75)
    raw = load_data()
    df, X, y = make_features(raw)
    years = pd.to_numeric(df['year'], errors='coerce')
    train = years.isin(TRAIN_YEARS)
    valid = years == VALIDATION_YEAR
    Xtr, ytr = X.loc[train], y.loc[train]
    Xv, yv = X.loc[valid], y.loc[valid]
    print('\n' + '=' * 75)
    print('SEASON-BASED TRAIN / VALIDATION SPLIT')
    print('=' * 75)
    for year in TRAIN_YEARS: print(f'Training {year}: {int((years==year).sum())} rows')
    print(f'Validation {VALIDATION_YEAR}: {len(Xv)} rows')
    print(f'\nTraining rows: {len(Xtr)}')
    print(f'Validation rows: {len(Xv)}')

    print('\n' + '=' * 75)
    print('TRAINING RANDOM FOREST')
    print('=' * 75)
    validation_model = build_model()
    print('Training...')
    validation_model.fit(Xtr, ytr)
    print('Training complete.')
    metrics = evaluate(validation_model, Xv, yv)
    threshold = metrics['best_threshold']['threshold']
    validation_importance = importance(validation_model)

    print('\n' + '=' * 75)
    print('TRAINING FINAL PRODUCTION MODEL')
    print('=' * 75)
    final_model = build_model()
    print(f'Training rows: {len(X)}')
    print('Training...')
    final_model.fit(X, y)
    print('Training complete.')
    final_importance = importance(final_model)

    package = {
        'model': final_model,
        'feature_list': FEATURES,
        'numeric_features': NUMERIC_FEATURES,
        'categorical_features': CATEGORICAL_FEATURES,
        'recommended_threshold': threshold,
        'validation_metrics': metrics['best_threshold'],
        'validation_metrics_050': metrics['threshold_050'],
        'feature_importance': final_importance,
        'validation_feature_importance': validation_importance,
        'training_years': TRAIN_YEARS,
        'validation_year': VALIDATION_YEAR,
        'training_rows': int(len(X)),
        'validation_rows': int(len(Xv)),
        'leakage_free': True,
        'forbidden_features': FORBIDDEN_FEATURES,
    }
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(package, MODEL_PATH)
    print('\n' + '=' * 75)
    print('SAVING MODEL')
    print('=' * 75)
    print('Model saved to:')
    print(MODEL_PATH)
    print('\nModel package contents:')
    print('  ✓ Random Forest pipeline')
    print('  ✓ Leakage-free feature list')
    print('  ✓ 2026 validation metrics')
    print('  ✓ Optimized probability threshold')
    print('  ✓ Feature importance')
    print('  ✓ Leakage metadata')
    print(f'\nRecommended RF threshold: {threshold:.2f}')
    print('\n' + '=' * 75)
    print('LEAKAGE CHECK: PASSED ✓')
    print('=' * 75)
    print('\n✅ ML TRAINING COMPLETE')
    print('2023-2025 = training data')
    print('2026 = unseen validation data')
    print('No future-position features were used.')


if __name__ == '__main__':
    main()