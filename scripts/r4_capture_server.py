"""Reuse disposable UI setup with a plain, clearly labelled mock response for review captures."""
from app.agent.text_triage import MockTriageTransport
from scripts import r2_ui_qa_server


class PresentationMock(MockTriageTransport):
    def __init__(self):
        self.calls = 0

    async def dispatch(self, call_id, prompt):
        self.calls += 1
        return await super().dispatch(call_id, prompt)


if __name__ == "__main__":
    r2_ui_qa_server.QATransport = PresentationMock
    r2_ui_qa_server.main()
