import httpx
from config import settings

_BASE_URL = "https://api.linear.app/graphql"


class LinearApp:
    def __init__(self) -> None:
        self._api_key: str = settings.linear_api_key

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    async def post_comment(self, issue_id: str, body: str) -> dict:
        mutation = """
        mutation CommentCreate($issueId: String!, $body: String!) {
            commentCreate(input: {issueId: $issueId, body: $body}) {
                success
                comment { id }
            }
        }
        """
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                _BASE_URL,
                headers=self._headers(),
                json={"query": mutation, "variables": {"issueId": issue_id, "body": body}},
            )
            resp.raise_for_status()
            return resp.json()

    async def get_issue(self, issue_id: str) -> dict:
        query = """
        query Issue($id: String!) {
            issue(id: $id) {
                id
                title
                description
                team { id }
            }
        }
        """
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                _BASE_URL,
                headers=self._headers(),
                json={"query": query, "variables": {"id": issue_id}},
            )
            resp.raise_for_status()
            return resp.json().get("data", {}).get("issue", {})
