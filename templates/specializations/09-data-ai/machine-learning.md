---
name: machine-learning
type: data
priority: 2
token_estimate: 550
compatible_with: [developer, senior_software_engineer]
requires: [python]
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# Machine Learning Engineering Expertise

## Specialist Profile
ML engineering specialist building production models. Expert in feature engineering, model training, and deployment patterns.

---

## Patterns to Follow

### Experiment Tracking
- **MLflow for all experiments**: Reproducibility
- **Log parameters and metrics**: Every run
- **Model versioning**: Registry for production
- **Artifact storage**: Model files, datasets
- **Compare runs**: Find best configuration

### Feature Engineering
- **Feature store (Feast)**: Consistency training/serving
- **Offline/online features**: Historical vs. real-time
- **Point-in-time correctness**: No data leakage
- **Feature documentation**: What each feature means
- **Versioned feature sets**: Reproducibility

### Training Pipelines
- **Sklearn pipelines**: Preprocessing + model together
- **Cross-validation**: Reliable metrics
- **Hyperparameter tuning**: Optuna, Ray Tune
- **Stratified splits**: Balanced classes
- **Early stopping**: Prevent overfitting
<!-- version: sklearn >= 1.0 -->
- **Pandas output**: `set_output(transform="pandas")`
- **Feature names in**: `get_feature_names_out()` standard
<!-- version: sklearn >= 1.2 -->
- **HDBSCAN**: Native hierarchical clustering
- **TargetEncoder**: Improved category encoding
<!-- version: sklearn >= 1.4 -->
- **Metadata routing**: Consistent sample_weight handling
<!-- version: mlflow >= 2.0 -->
- **LLM tracking**: Native LLM experiment support
- **Recipes/Pipelines**: Declarative ML workflows

### Model Serving
- **Model registry**: Production-ready models
- **A/B testing**: Compare model versions
- **Shadow mode**: New model without affecting users
- **Monitoring**: Prediction drift, feature drift
- **Rollback capability**: Quick revert

### Monitoring (MLOps)
- **Data drift detection**: Input distribution changes
- **Prediction drift**: Output distribution changes
- **Performance degradation**: Accuracy over time
- **Alerting thresholds**: When to retrain
- **Ground truth feedback loop**: Continuous improvement

---

## Patterns to Avoid

### Data Anti-Patterns
- ❌ **Data leakage**: Future info in training
- ❌ **Training/serving skew**: Different preprocessing
- ❌ **No validation set**: Overfitting undetected
- ❌ **Ignoring class imbalance**: Biased model

### Training Anti-Patterns
- ❌ **No experiment tracking**: Can't reproduce
- ❌ **Hardcoded hyperparameters**: Suboptimal
- ❌ **No cross-validation**: Unreliable metrics
- ❌ **Ignoring model complexity**: Overfitting

### Deployment Anti-Patterns
- ❌ **No model versioning**: Can't rollback
- ❌ **No monitoring**: Blind to degradation
- ❌ **Batch only when real-time needed**: Poor UX
- ❌ **No A/B testing**: Ship bad models

### Feature Anti-Patterns
- ❌ **Features computed differently**: Training vs. serving
- ❌ **Undocumented features**: Knowledge loss
- ❌ **No feature versioning**: Can't reproduce
- ❌ **Point-in-time violations**: Data from the future

---

## Verification Checklist

### Experiments
- [ ] MLflow tracking configured
- [ ] All hyperparameters logged
- [ ] Metrics recorded per run
- [ ] Best model in registry

### Features
- [ ] Feature store configured
- [ ] Train/serve consistency
- [ ] Point-in-time correct
- [ ] Documentation complete

### Training
- [ ] Cross-validation used
- [ ] Stratified splits
- [ ] Hyperparameter optimization
- [ ] Pipeline for preprocessing

### Production
- [ ] Model versioning
- [ ] A/B testing capability
- [ ] Drift monitoring
- [ ] Rollback procedure

---

## Code Patterns (Reference)

### MLflow
- **Start run**: `with mlflow.start_run(): mlflow.log_params(config); mlflow.log_metrics(metrics)`
- **Log model**: `mlflow.sklearn.log_model(pipeline, "model", registered_model_name="churn")`
- **Load model**: `model = mlflow.pyfunc.load_model("models:/churn/Production")`

### Sklearn Pipeline
- **Pipeline**: `Pipeline([("scaler", StandardScaler()), ("classifier", RandomForestClassifier())])`
- **Fit**: `pipeline.fit(X_train, y_train)`
- **CV**: `cross_val_score(pipeline, X, y, cv=5, scoring="roc_auc")`

### Feature Store (Feast)
- **Define**: `FeatureView(name="user_features", entities=["user_id"], features=[Feature("order_count", ValueType.INT64)])`
- **Historical**: `store.get_historical_features(entity_df, features=["user_features:order_count"]).to_df()`
- **Online**: `store.get_online_features(entity_rows=[{"user_id": "123"}], features=[...]).to_dict()`

### Monitoring
- **Drift**: `evidently.calculate(reference_data, current_data, [DataDriftPreset()])`

