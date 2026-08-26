"""Model versioning and management for MLOps tracking."""

from __future__ import annotations

import json
import pickle
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from uuid import uuid4

from src.utils.logger import logger


class ModelVersionManager:
    """Manages model versions, metadata, and lifecycle."""

    def __init__(self, models_dir: str = "models"):
        """Initialize model version manager.
        
        Args:
            models_dir: Directory to store model artifacts
        """
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)
        self.metadata_file = self.models_dir / "metadata.json"
        self.metadata: Dict[str, Any] = self._load_metadata()

    def _load_metadata(self) -> Dict[str, Any]:
        """Load model metadata from disk."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"failed_to_load_metadata: {str(e)}")
        return {"models": {}, "active": {}}

    def _save_metadata(self) -> None:
        """Save model metadata to disk."""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"failed_to_save_metadata: {str(e)}")

    def register_model(
        self,
        model_name: str,
        model_type: str,
        model_path: str,
        metrics: Dict[str, float],
        hyperparameters: Dict[str, Any],
        training_data_size: int,
        features: List[str]
    ) -> str:
        """Register a new model version.
        
        Args:
            model_name: Name of the model
            model_type: Type (e.g., 'sklearn', 'torch', 'xgboost')
            model_path: Path to saved model file
            metrics: Performance metrics (accuracy, R², MAE, etc.)
            hyperparameters: Model hyperparameters
            training_data_size: Number of training samples
            features: List of feature names
            
        Returns:
            Version ID (UUID)
        """
        version_id = str(uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        model_version = {
            "version_id": version_id,
            "model_name": model_name,
            "model_type": model_type,
            "model_path": model_path,
            "created_at": timestamp,
            "metrics": metrics,
            "hyperparameters": hyperparameters,
            "training_data_size": training_data_size,
            "features": features,
            "status": "inactive"
        }
        
        # Store version metadata
        if model_name not in self.metadata["models"]:
            self.metadata["models"][model_name] = []
        
        self.metadata["models"][model_name].append(model_version)
        self._save_metadata()
        
        logger.info(
            "model_registered",
            model_name=model_name,
            version_id=version_id,
            metrics=metrics
        )
        
        return version_id

    def activate_model(self, model_name: str, version_id: str) -> bool:
        """Activate a specific model version.
        
        Args:
            model_name: Name of the model
            version_id: Version ID to activate
            
        Returns:
            True if successful, False otherwise
        """
        if model_name not in self.metadata["models"]:
            logger.warning(f"model_not_found: {model_name}")
            return False
        
        # Find version
        versions = self.metadata["models"][model_name]
        version = next((v for v in versions if v["version_id"] == version_id), None)
        
        if not version:
            logger.warning(f"version_not_found: {version_id}")
            return False
        
        # Deactivate previous version
        for v in versions:
            v["status"] = "inactive"
        
        # Activate new version
        version["status"] = "active"
        version["activated_at"] = datetime.utcnow().isoformat()
        
        self.metadata["active"][model_name] = version_id
        self._save_metadata()
        
        logger.info(
            "model_activated",
            model_name=model_name,
            version_id=version_id
        )
        
        return True

    def get_active_model(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get active model version.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Model version metadata or None
        """
        version_id = self.metadata["active"].get(model_name)
        if not version_id:
            return None
        
        versions = self.metadata["models"].get(model_name, [])
        return next((v for v in versions if v["version_id"] == version_id), None)

    def get_model_versions(self, model_name: str) -> List[Dict[str, Any]]:
        """Get all versions of a model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            List of model versions
        """
        return self.metadata["models"].get(model_name, [])

    def compare_versions(
        self,
        model_name: str,
        version_ids: List[str]
    ) -> Dict[str, Any]:
        """Compare multiple model versions.
        
        Args:
            model_name: Name of the model
            version_ids: Version IDs to compare
            
        Returns:
            Comparison data
        """
        versions = self.metadata["models"].get(model_name, [])
        selected = [v for v in versions if v["version_id"] in version_ids]
        
        return {
            "model_name": model_name,
            "versions": selected,
            "best_by_metric": self._find_best_versions(selected)
        }

    def _find_best_versions(self, versions: List[Dict]) -> Dict[str, str]:
        """Find best version by each metric."""
        if not versions:
            return {}
        
        best = {}
        # Get all metrics from first version
        metrics = list(versions[0].get("metrics", {}).keys())
        
        for metric in metrics:
            best_version = max(
                versions,
                key=lambda v: v.get("metrics", {}).get(metric, 0)
            )
            best[metric] = best_version["version_id"]
        
        return best

    def deprecate_version(self, model_name: str, version_id: str) -> bool:
        """Deprecate a model version.
        
        Args:
            model_name: Name of the model
            version_id: Version ID to deprecate
            
        Returns:
            True if successful, False otherwise
        """
        versions = self.metadata["models"].get(model_name, [])
        version = next((v for v in versions if v["version_id"] == version_id), None)
        
        if not version:
            return False
        
        version["status"] = "deprecated"
        version["deprecated_at"] = datetime.utcnow().isoformat()
        self._save_metadata()
        
        logger.info(
            "model_deprecated",
            model_name=model_name,
            version_id=version_id
        )
        
        return True

    def get_health_report(self) -> Dict[str, Any]:
        """Get health report of all models."""
        report = {
            "total_models": len(self.metadata["models"]),
            "total_versions": sum(
                len(versions)
                for versions in self.metadata["models"].values()
            ),
            "active_models": len(self.metadata["active"]),
            "models": {}
        }
        
        for model_name, versions in self.metadata["models"].items():
            active = self.metadata["active"].get(model_name)
            report["models"][model_name] = {
                "total_versions": len(versions),
                "active_version": active,
                "latest_metrics": versions[-1].get("metrics") if versions else {}
            }
        
        return report
