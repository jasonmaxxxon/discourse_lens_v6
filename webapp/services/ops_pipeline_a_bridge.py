import asyncio
import logging
from webapp.services.job_manager import JobManager
from webapp.services import pipeline_runner

logger = logging.getLogger(__name__)


async def run_pipeline_a_with_ops(job_id: str, url: str) -> None:
    """
    Bridge function to run Pipeline A while updating Supabase Ops tables.
    Tracks lifecycle via logs and standard RPC claiming.
    """
    manager = JobManager()
    worker_id = "bridge-pipeline-a"
    item_id: str | None = None
    heartbeat_task: asyncio.Task | None = None
    heartbeat_interval = 4  # seconds
    stop_heartbeat = asyncio.Event()

    logger.info(f"[{job_id}] Bridge Started. Target: {url}")

    try:
        # 1. Claim the item (Standard RPC Protocol)
        claimed_item = await manager.claim_next_item(job_id, worker_id)
        if not claimed_item:
            logger.warning(f"[{job_id}] Claim returned None. Item might be stuck or already claimed.")
            # Inspect current items to detect missing rows early
            items_snapshot, _degraded = await manager.get_job_items(job_id, limit=5)
            logger.info(f"[{job_id}] Items snapshot after failed claim count={len(items_snapshot)}")
            if not items_snapshot:
                logger.error(f"[{job_id}] OPS_ITEM_MISSING url={url} (no job_items found)")
            return

        item_id = claimed_item["id"]
        logger.info(f"[{job_id}] Claimed Item ID: {item_id}")

        # 2. Update Stage: Fetch
        await manager.set_item_stage(item_id, "fetch")
        logger.info(f"[{job_id}] Stage -> Fetch")

        # 3. Run the Actual Pipeline Logic (Legacy Runner)
        logger.info(f"[{job_id}] Executing Legacy Runner...")
        await manager.set_item_stage(item_id, "analyst")
        logger.info(f"[{job_id}] Stage -> Analyst")

        async def heartbeat():
            while not stop_heartbeat.is_set():
                try:
                    await manager.touch_item(item_id, stage="analyst")
                    await manager.set_job_heartbeat(job_id)
                except Exception as hb_err:
                    logger.warning(f"[{job_id}] Heartbeat failed: {hb_err}")
                try:
                    await asyncio.wait_for(stop_heartbeat.wait(), timeout=heartbeat_interval)
                except asyncio.TimeoutError:
                    continue

        heartbeat_task = asyncio.create_task(heartbeat())
        await asyncio.to_thread(pipeline_runner.run_pipeline_a_job, job_id, url)
        logger.info(f"[{job_id}] Legacy Runner Completed.")

        # 4. Success Sequence
        await manager.set_item_stage(item_id, "store")
        logger.info(f"[{job_id}] Stage -> Store")

        await manager.complete_item(item_id, result_post_id=f"pipeline_a:{job_id}")
        logger.info(f"[{job_id}] Item Completed.")

        await manager._rpc(
            "bump_job_counters",
            {"p_job_id": job_id, "p_is_success": True, "p_is_failed": False},
        )

    except Exception as e:
        logger.error(f"[{job_id}] Pipeline A Bridge Failed: {e}")
        if item_id:
            await manager.fail_item(item_id, "analyst", "PIPELINE_ERROR", str(e))
            await manager._rpc(
                "bump_job_counters",
                {"p_job_id": job_id, "p_is_success": False, "p_is_failed": True},
            )

    finally:
        stop_heartbeat.set()
        if heartbeat_task:
            try:
                await heartbeat_task
            except Exception as hb_err:
                logger.warning(f"[{job_id}] Heartbeat task cleanup failed: {hb_err}")
        if item_id:
            job_snapshot = await manager._table_select_single("job_batches", job_id)
            job_snapshot = job_snapshot or {}
            logger.info(
                f"[{job_id}] Finalizing (processed={job_snapshot.get('processed_count')}, "
                f"success={job_snapshot.get('success_count')}, failed={job_snapshot.get('failed_count')}, "
                f"total={job_snapshot.get('total_count')})"
            )
            await manager._rpc("finalize_job_if_done", {"p_job_id": job_id})
            logger.info(f"[{job_id}] Job Finalization Check Done.")
