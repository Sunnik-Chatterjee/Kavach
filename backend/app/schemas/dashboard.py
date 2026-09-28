"""Pydantic response schemas for dashboard endpoints."""

from pydantic import BaseModel, ConfigDict, RootModel

from app.schemas.prediction import PredictionRead


class DashboardSummary(BaseModel):
    """Aggregate prediction metrics and the newest prediction."""

    total_predictions: int
    healthy_count: int
    fault_count: int
    average_confidence: float
    latest_prediction: PredictionRead | None

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "total_predictions": 523,
                    "healthy_count": 498,
                    "fault_count": 25,
                    "average_confidence": 0.94,
                    "latest_prediction": {
                        "id": "3f9a2d7e-8b1c-4a6f-9c2d-1e5b7a3f8c10",
                        "fault_label": "healthy",
                        "confidence": 0.97,
                        "probabilities_json": {"healthy": 0.97, "fault": 0.03},
                        "prediction_timestamp": "2026-09-29T10:30:00Z",
                        "created_at": "2026-09-29T10:30:01Z",
                    },
                }
            ]
        }
    )


class FaultDistribution(RootModel[dict[str, int]]):
    """Prediction counts keyed by fault label."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"healthy": 82, "bearing_fault_near": 10, "bearing_fault_far": 5}]
        }
    )