---
name: machine-learning
type: data
priority: 2
token_estimate: 400
compatible_with: [developer, senior_software_engineer]
requires: [python]
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# Machine Learning Engineering Expertise

## Specialist Profile
ML engineering specialist building production models. Expert in feature engineering, model training, and deployment patterns.

## Implementation Guidelines

### Training Pipeline

```python
# src/training/train.py
import mlflow
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score

def train_model(config: TrainingConfig):
    mlflow.set_experiment(config.experiment_name)

    with mlflow.start_run():
        # Log parameters
        mlflow.log_params(config.to_dict())

        # Load and split data
        X, y = load_features(config.feature_table)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # Create pipeline
        pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("classifier", RandomForestClassifier(
                n_estimators=config.n_estimators,
                max_depth=config.max_depth,
                random_state=42,
            )),
        ])

        # Train
        pipeline.fit(X_train, y_train)

        # Evaluate
        y_pred = pipeline.predict(X_test)
        y_proba = pipeline.predict_proba(X_test)[:, 1]

        metrics = {
            "accuracy": accuracy_score(y_test, y_pred),
            "roc_auc": roc_auc_score(y_test, y_proba),
            "f1": f1_score(y_test, y_pred),
        }
        mlflow.log_metrics(metrics)

        # Log model
        mlflow.sklearn.log_model(
            pipeline,
            "model",
            registered_model_name=config.model_name,
        )

        return metrics
```

### Feature Store

```python
# src/features/user_features.py
from feast import Entity, Feature, FeatureView, FileSource
from datetime import timedelta

user = Entity(name="user_id", value_type=ValueType.STRING)

user_features = FeatureView(
    name="user_features",
    entities=["user_id"],
    ttl=timedelta(days=1),
    features=[
        Feature(name="order_count", dtype=ValueType.INT64),
        Feature(name="total_spent", dtype=ValueType.FLOAT),
        Feature(name="days_since_last_order", dtype=ValueType.INT64),
        Feature(name="avg_order_value", dtype=ValueType.FLOAT),
    ],
    batch_source=FileSource(
        path="s3://feature-store/user_features/",
        timestamp_field="event_timestamp",
    ),
)

# Retrieval
def get_training_features(user_ids: list[str], timestamp: datetime):
    return store.get_historical_features(
        entity_df=pd.DataFrame({
            "user_id": user_ids,
            "event_timestamp": [timestamp] * len(user_ids),
        }),
        features=["user_features:order_count", "user_features:total_spent"],
    ).to_df()
```

### Model Serving

```python
# src/serving/predictor.py
import mlflow.pyfunc

class ChurnPredictor:
    def __init__(self, model_uri: str):
        self.model = mlflow.pyfunc.load_model(model_uri)
        self.feature_store = feast.FeatureStore()

    def predict(self, user_id: str) -> dict:
        # Get real-time features
        features = self.feature_store.get_online_features(
            features=["user_features:order_count", "user_features:total_spent"],
            entity_rows=[{"user_id": user_id}],
        ).to_dict()

        # Predict
        df = pd.DataFrame([features])
        proba = self.model.predict(df)[0]

        return {
            "user_id": user_id,
            "churn_probability": float(proba),
            "risk_level": "high" if proba > 0.7 else "medium" if proba > 0.3 else "low",
        }
```

## Patterns to Avoid
- ❌ Training/serving skew
- ❌ Data leakage in features
- ❌ Missing experiment tracking
- ❌ No model versioning

## Verification Checklist
- [ ] Experiment tracking (MLflow)
- [ ] Feature store for consistency
- [ ] Model versioning
- [ ] A/B testing capability
- [ ] Monitoring for drift
