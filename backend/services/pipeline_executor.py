import asyncio
import json
from datetime import datetime
from sqlmodel import Session, select
from models.pipeline import Pipeline, PipelineRun
from models.task import Task, Repo
from services.agent_library import get_agent
from database import engine


async def execute_pipeline(pipeline_id: str, repo_id: str, workspace_id: str, api_key_id: str):
    with Session(engine) as session:
        pipeline = session.get(Pipeline, pipeline_id)
        if not pipeline:
            return

        config = json.loads(pipeline.config)
        steps = config.get("steps", [])

        run = PipelineRun(
            pipeline_id=pipeline_id,
            steps_total=len(steps),
            status="running",
        )
        session.add(run)
        session.commit()
        session.refresh(run)

        completed: set = set()

        for i, step in enumerate(steps):
            step_id = step.get("id", step.get("agent", step.get("task", str(i))))
            deps = step.get("depends_on", [])
            on_failure = step.get("on_failure", "stop")

            for dep in deps:
                if dep not in completed:
                    await asyncio.sleep(0.1)

            try:
                agent_name = step.get("agent")
                task_desc = step.get("task")

                if agent_name:
                    agent = get_agent(agent_name)
                    if agent:
                        task_desc = agent.full_description

                if task_desc:
                    repo = session.get(Repo, repo_id)
                    if repo:
                        from agent.orchestrator import run_task
                        from api.ws import get_or_create_queue, pump_queue_to_ws
                        task = Task(
                            workspace_id=workspace_id,
                            repo_id=repo_id,
                            description=task_desc,
                        )
                        session.add(task)
                        session.commit()
                        session.refresh(task)
                        queue = get_or_create_queue(task.id)
                        asyncio.create_task(run_task(task, repo, queue, api_key_id=api_key_id))
                        asyncio.create_task(pump_queue_to_ws(task.id))

                completed.add(step_id)
                run.steps_completed += 1
                session.add(run)
                session.commit()

            except Exception as e:
                if on_failure == "stop":
                    run.status = "failed"
                    run.error = str(e)
                    run.completed_at = datetime.utcnow()
                    session.add(run)
                    session.commit()
                    return
                completed.add(step_id)

        run.status = "success"
        run.completed_at = datetime.utcnow()
        session.add(run)

        pipeline.last_run_at = run.completed_at
        pipeline.last_run_status = "success"
        session.add(pipeline)
        session.commit()
