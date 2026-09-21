"""Evaluation service — dataset management and evaluation runner."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.db.models import (
    EvaluationDataset, EvaluationResult, EvaluationRun, NlpSettings
)
from app.nlp.pipeline import run_pipeline
from app.nlp.score_fusion import FusionWeights

logger = get_logger(__name__)


async def _get_fusion_weights(db: AsyncSession) -> FusionWeights:
    result = await db.execute(select(NlpSettings))
    rows = result.scalars().all()
    w = {r.name: r.value for r in rows}
    return FusionWeights(
        tfidf=w.get("alpha_tfidf", settings.SCORE_WEIGHT_TFIDF),
        word_order=w.get("beta_word_order", settings.SCORE_WEIGHT_WORD_ORDER),
        intent=w.get("gamma_intent", settings.SCORE_WEIGHT_INTENT),
        keyword=w.get("delta_keyword", settings.SCORE_WEIGHT_KEYWORD),
    )


async def list_datasets(db: AsyncSession) -> List[EvaluationDataset]:
    result = await db.execute(
        select(EvaluationDataset).order_by(EvaluationDataset.created_at.desc())
    )
    return result.scalars().all()


async def create_dataset(
    db: AsyncSession, name: str, description: Optional[str], cases: List[dict], created_by: str
) -> EvaluationDataset:
    ds = EvaluationDataset(
        id=uuid.uuid4(),
        name=name,
        description=description,
        cases=cases,
        created_by=uuid.UUID(created_by),
    )
    db.add(ds)
    await db.flush()
    return ds


async def run_evaluation(
    db: AsyncSession,
    dataset_id: str,
    mode: str,  # "baseline" | "enhanced"
    run_by: str,
) -> EvaluationRun:
    """
    Run evaluation on all cases in the dataset.
    Computes actual metrics — no fabricated values.
    """
    ds_result = await db.execute(
        select(EvaluationDataset).where(EvaluationDataset.id == uuid.UUID(dataset_id))
    )
    dataset = ds_result.scalars().first()
    if not dataset:
        raise ValueError("Dataset not found")

    baseline_mode = mode == "baseline"
    weights = await _get_fusion_weights(db)

    # Create run record
    run = EvaluationRun(
        id=uuid.uuid4(),
        dataset_id=dataset.id,
        mode=mode,
        weights_snapshot={
            "alpha_tfidf": weights.tfidf,
            "beta_word_order": weights.word_order,
            "gamma_intent": weights.intent,
            "delta_keyword": weights.keyword,
        } if not baseline_mode else {"alpha_tfidf": 1.0, "beta_word_order": 0.0, "gamma_intent": 0.0, "delta_keyword": 0.0},
        run_at=datetime.now(timezone.utc),
        run_by=uuid.UUID(run_by),
        total_cases=len(dataset.cases),
    )
    db.add(run)
    await db.flush()

    # Evaluate each case
    intent_correct_count = 0
    retrieval_correct_count = 0
    unknown_count = 0
    total_time = 0
    results_with_expected_intent = 0
    results_with_expected_kb = 0

    for i, case in enumerate(dataset.cases):
        query = case.get("query", "")
        expected_intent = case.get("expected_intent")
        expected_category = case.get("expected_category")

        nlp_result = run_pipeline(
            query=query,
            weights=weights,
            baseline_mode=baseline_mode,
        )

        predicted_intent = nlp_result["intent"]
        predicted_kb_id = nlp_result.get("kb_entry_id")
        query_type = nlp_result["query_type"]
        processing_time = nlp_result["processing_time_ms"]
        total_time += processing_time

        # Intent accuracy
        intent_correct = None
        if expected_intent:
            results_with_expected_intent += 1
            if expected_intent == "unknown":
                intent_correct = query_type in ("UNKNOWN_INSTITUTIONAL", "OUT_OF_DOMAIN")
            else:
                intent_correct = (predicted_intent == expected_intent)
            if intent_correct:
                intent_correct_count += 1

        # Retrieval success — check by category if no specific entry ID
        retrieval_correct = None
        if expected_category and expected_category != "unknown":
            results_with_expected_kb += 1
            # Check top candidates from debug
            top_candidates = nlp_result.get("debug", {}).get("top_candidates", [])
            if top_candidates and top_candidates[0].get("category") == expected_category:
                retrieval_correct = True
                retrieval_correct_count += 1
            else:
                retrieval_correct = False

        if query_type in ("UNKNOWN_INSTITUTIONAL", "OUT_OF_DOMAIN"):
            unknown_count += 1

        result_row = EvaluationResult(
            id=uuid.uuid4(),
            run_id=run.id,
            case_index=i,
            query=query,
            expected_intent=expected_intent,
            expected_kb_entry_id=expected_category,
            predicted_intent=predicted_intent,
            predicted_kb_entry_id=predicted_kb_id,
            intent_correct=intent_correct,
            retrieval_correct=retrieval_correct,
            final_score=nlp_result["final_score"],
            query_type=query_type,
            processing_time_ms=processing_time,
            debug_json=nlp_result.get("debug"),
        )
        db.add(result_row)

    # Compute aggregate metrics
    total = len(dataset.cases)
    run.intent_accuracy = (
        round(intent_correct_count / results_with_expected_intent, 4)
        if results_with_expected_intent > 0 else None
    )
    run.retrieval_success_rate = (
        round(retrieval_correct_count / results_with_expected_kb, 4)
        if results_with_expected_kb > 0 else None
    )
    run.unknown_rate = round(unknown_count / total, 4) if total > 0 else 0.0
    run.avg_processing_time_ms = round(total_time / total, 2) if total > 0 else 0.0

    await db.flush()
    return run


async def get_runs(db: AsyncSession) -> List[EvaluationRun]:
    result = await db.execute(
        select(EvaluationRun).order_by(EvaluationRun.run_at.desc())
    )
    return result.scalars().all()


async def get_run_with_results(
    db: AsyncSession, run_id: str
) -> Optional[EvaluationRun]:
    result = await db.execute(
        select(EvaluationRun).where(EvaluationRun.id == uuid.UUID(run_id))
    )
    run = result.scalars().first()
    if run:
        res_result = await db.execute(
            select(EvaluationResult)
            .where(EvaluationResult.run_id == run.id)
            .order_by(EvaluationResult.case_index)
        )
        run.results = res_result.scalars().all()
    return run
