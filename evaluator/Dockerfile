FROM python:3.11-slim-bookworm@sha256:94a8fee35252d06ab75856f15f12c7bae67b10e8a6da93c7fded82b2610926cd
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /opt/valvuln
COPY requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock && useradd --uid 10001 --create-home valvuln
COPY requirements-worker.lock pyproject.toml ./
COPY app ./app
COPY boundary ./boundary
# Operator image only. Never copied into app/worker/lab images or mounted to the model.
COPY evaluator ./evaluator
USER 10001:10001
ENTRYPOINT ["python", "-m", "evaluator.text_benchmark"]
