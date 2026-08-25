"""Salary prediction model.

Trains a Ridge regression model to predict salary based on
job features like skills, experience level, and technologies.
"""

import json
import os
import pickle
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


def get_salary_training_data(db_session):
    """Extract salary training data from database."""
    query = """
    SELECT 
        COALESCE(jsonb_array_length(extracted_skills), 0) AS skill_count,
        COALESCE(jsonb_array_length(extracted_technologies), 0) AS tech_count,
        experience_level_id,
        (salary_min + salary_max) / 2 AS salary_midpoint
    FROM analytics.fact_job_posting
    WHERE salary_min IS NOT NULL 
      AND salary_max IS NOT NULL
      AND is_active = TRUE
    """
    return pd.read_sql(query, db_session.bind)


def train_salary_model(db_session=None):
    """Train the salary prediction model."""
    print("Training salary prediction model...")
    
    # Get training data
    if db_session is None:
        from src.database import get_db_context
        with get_db_context() as db:
            df = get_salary_training_data(db)
    else:
        df = get_salary_training_data(db_session)
    
    if len(df) == 0:
        print("No salary training data available")
        return None
    
    # Prepare features
    X = df[['skill_count', 'tech_count', 'experience_level_id']].fillna(0).values
    y = df['salary_midpoint'].values
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train model
    model = Ridge(alpha=1.0)
    model.fit(X_train_scaled, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test_scaled)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    
    print(f"Model Performance:")
    print(f"  R² Score: {r2:.4f}")
    print(f"  MAE: {mae:.2f} AED")
    print(f"  RMSE: {rmse:.2f} AED")
    
    # Save model
    model_dir = Path("models")
    model_dir.mkdir(exist_ok=True)
    
    model_data = {
        'model': model,
        'scaler': scaler,
        'features': ['skill_count', 'tech_count', 'experience_level_id'],
        'trained_at': datetime.now().isoformat(),
        'metrics': {'r2': r2, 'mae': mae, 'rmse': rmse},
        'training_samples': len(df)
    }
    
    model_path = model_dir / "salary_predictor_v1.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump(model_data, f)
    
    print(f"Model saved to {model_path}")
    
    # Save metrics to JSON
    metrics_path = model_dir / "salary_predictor_metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(model_data['metrics'], f, indent=2)
    
    return model_data


if __name__ == "__main__":
    train_salary_model()