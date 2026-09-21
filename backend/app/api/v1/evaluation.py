"""Evaluation routes — /api/v1/evaluation"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.db.session import get_db
from app.schemas.evaluation import (
    EvalDatasetCreate, EvalDatasetOut, EvalRunOut, RunEvalRequest
)
from app.services import evaluation_service

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


@router.get("/datasets", response_model=list[EvalDatasetOut])
async def list_datasets(db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    datasets = await evaluation_service.list_datasets(db)
    return [
        EvalDatasetOut(
            id=str(d.id),
            name=d.name,
            description=d.description,
            case_count=len(d.cases),
            created_at=d.created_at,
        )
        for d in datasets
    ]


@router.post("/datasets", response_model=EvalDatasetOut, status_code=201)
async def create_dataset(
    body: EvalDatasetCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    ds = await evaluation_service.create_dataset(
        db, body.name, body.description, [c.model_dump() for c in body.cases], str(current_user.id)
    )
    return EvalDatasetOut(
        id=str(ds.id), name=ds.name, description=ds.description,
        case_count=len(ds.cases), created_at=ds.created_at
    )


@router.post("/datasets/{dataset_id}/run", response_model=EvalRunOut, status_code=201)
async def run_evaluation(
    dataset_id: str,
    body: RunEvalRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    if body.mode not in ("baseline", "enhanced"):
        raise HTTPException(status_code=400, detail="mode must be 'baseline' or 'enhanced'")
    try:
        run = await evaluation_service.run_evaluation(db, dataset_id, body.mode, str(current_user.id))
        return EvalRunOut(
            id=str(run.id), dataset_id=str(run.dataset_id), mode=run.mode,
            weights_snapshot=run.weights_snapshot,
            intent_accuracy=run.intent_accuracy,
            retrieval_success_rate=run.retrieval_success_rate,
            unknown_rate=run.unknown_rate,
            avg_processing_time_ms=run.avg_processing_time_ms,
            total_cases=run.total_cases,
            run_at=run.run_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/runs", response_model=list[EvalRunOut])
async def list_runs(db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    runs = await evaluation_service.get_runs(db)
    return [
        EvalRunOut(
            id=str(r.id), dataset_id=str(r.dataset_id), mode=r.mode,
            weights_snapshot=r.weights_snapshot,
            intent_accuracy=r.intent_accuracy,
            retrieval_success_rate=r.retrieval_success_rate,
            unknown_rate=r.unknown_rate,
            avg_processing_time_ms=r.avg_processing_time_ms,
            total_cases=r.total_cases,
            run_at=r.run_at,
        )
        for r in runs
    ]


@router.get("/runs/{run_id}", response_model=EvalRunOut)
async def get_run(run_id: str, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    run = await evaluation_service.get_run_with_results(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    from app.schemas.evaluation import EvalResultItem
    return EvalRunOut(
        id=str(run.id), dataset_id=str(run.dataset_id), mode=run.mode,
        weights_snapshot=run.weights_snapshot,
        intent_accuracy=run.intent_accuracy,
        retrieval_success_rate=run.retrieval_success_rate,
        unknown_rate=run.unknown_rate,
        avg_processing_time_ms=run.avg_processing_time_ms,
        total_cases=run.total_cases,
        run_at=run.run_at,
        results=[
            EvalResultItem(
                case_index=r.case_index, query=r.query,
                expected_intent=r.expected_intent, predicted_intent=r.predicted_intent,
                intent_correct=r.intent_correct, retrieval_correct=r.retrieval_correct,
                final_score=r.final_score, query_type=r.query_type,
                processing_time_ms=r.processing_time_ms,
            )
            for r in (run.results or [])
        ],
    )
