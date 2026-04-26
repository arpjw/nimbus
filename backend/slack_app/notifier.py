from slack_app.slack_app import SlackApp


class SlackNotifier:
    def __init__(self):
        self._app = SlackApp()

    async def on_task_start(self, channel: str, task_id: str, task_desc: str) -> str:
        text = f":rocket: *Nimbus task started*\n`{task_desc[:200]}`\nTask ID: `{task_id}`"
        return await self._app.post_message(channel, text)

    async def on_phase_update(self, channel: str, thread_ts: str, phase: str, detail: str) -> None:
        text = f":gear: *{phase.replace('_', ' ').title()}* -- {detail}"
        await self._app.post_thread_reply(channel, thread_ts, text)

    async def on_task_complete(
        self,
        channel: str,
        thread_ts: str,
        pr_url: str,
        verdict: str,
        duration: float,
    ) -> None:
        mins = int(duration // 60)
        secs = int(duration % 60)
        text = (
            f":white_check_mark: *Task complete* in {mins}m {secs}s\n"
            f"PR: {pr_url}\n"
            f"Verdict: *{verdict}*"
        )
        await self._app.post_thread_reply(channel, thread_ts, text)

    async def on_task_failed(self, channel: str, thread_ts: str, error: str) -> None:
        text = f":x: *Task failed*\n```{error[:500]}```"
        await self._app.post_thread_reply(channel, thread_ts, text)
