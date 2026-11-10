FROM python:3.11-slim-bookworm@sha256:94a8fee35252d06ab75856f15f12c7bae67b10e8a6da93c7fded82b2610926cd
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/browsers
WORKDIR /opt/valvuln
COPY requirements.lock requirements-worker.lock ./
RUN pip install --no-cache-dir -r requirements-worker.lock && python -m playwright install --with-deps chromium && apt-get update && apt-get install -y --no-install-recommends iptables=1.8.9-2 util-linux=2.38.1-5+deb12u3 && rm -rf /var/lib/apt/lists/* && useradd --uid 10001 --create-home valvuln
ENV XDG_CONFIG_HOME=/tmp/valvuln-config XDG_CACHE_HOME=/tmp/valvuln-cache
COPY boundary ./boundary
COPY worker ./worker
COPY containers/lab-network.sh /usr/local/bin/lab-network
RUN chmod 755 /usr/local/bin/lab-network && mkdir -p /handoff/inbox /handoff/outbox && chown -R 10001:10001 /handoff
ENTRYPOINT ["/usr/local/bin/lab-network", "worker"]
CMD ["python", "-m", "worker.service"]
