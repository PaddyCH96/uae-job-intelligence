"""Skill demand forecasting model.

Trains a simple model to predict future skill demand
based on historical job posting data.
"""

import json
import os
import pickle
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split


def get_training_data(db_session):
    """Extract training data from database."""
    query = """
    SELECT 
        skill AS skill_name,
        COUNT(*) AS total_demand,
        COUNT(CASE WHEN posted_date >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) AS demand_30d,
        COUNT(CASE WHEN posted_date >= CURRENT_DATE - INTERVAL '90 days' THEN 1 END) AS demand_90d,
        COUNT(DISTINCT company_id) AS unique_companies
    FROM analytics.fact_job_posting,
         jsonb_array_elements_text(extracted_skills) AS skill
    WHERE extracted_skills IS NOT NULL
      AND is_active = TRUE
    GROUP BY skill
    HAVING COUNT(*) >= 2
    """
    return pd.read_sql(query, db_session.bind)


def train_skill_demand_model(db_session=None):
    """Train the skill demand forecasting model."""
    print("Training skill demand forecasting model...")
    
    # Get training data
    if db_session is None:
        from src.database import get_db_context
        with get_db_context() as db:
            df = get_training_data(db)
    else:
        df = get_training_data(db_session)
    
    if len(df) < 3:
        print(f"Insufficient training data: {len(df)} samples (need at least 3)")
        print("Creating baseline model with available data...")
    
    # Prepare features
    X = df[['total_demand', 'demand_30d', 'demand_90d', 'unique_companies']].values
    y = df['total_demand'].values
    
    # For small datasets, use all data for training
    if len(X) < 10:
        X_train, X_test, y_train, y_test = X, X, y, y
    else:
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train model
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    
    print(f"Model Performance:")
    print(f"  R² Score: {r2:.4f}")
    print(f"  MAE: {mae:.2f}")
    print(f"  RMSE: {rmse:.2f}")
    
    # Save model
    model_dir = Path("models")
    model_dir.mkdir(exist_ok=True)
    
    model_data = {
        'model': model,
        'features': ['total_demand', 'demand_30d', 'demand_90d', 'unique_companies'],
        'trained_at': datetime.now().isoformat(),
        'metrics': {'r2': r2, 'mae': mae, 'rmse': rmse},
        'training_samples': len(df)
    }
    
    model_path = model_dir / "skill_forecast_v1.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump(model_data, f)
    
    print(f"Model saved to {model_path}")
    
    # Save metrics to JSON
    metrics_path = model_dir / "skill_forecast_metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(model_data['metrics'], f, indent=2)
    
    return model_data


if __name__ == "__main__":
    train_skill_demand_model()