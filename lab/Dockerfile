FROM python:3.11-slim-bookworm@sha256:94a8fee35252d06ab75856f15f12c7bae67b10e8a6da93c7fded82b2610926cd
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /opt/valvuln
COPY requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock && apt-get update && apt-get install -y --no-install-recommends iptables=1.8.9-2 util-linux=2.38.1-5+deb12u3 && rm -rf /var/lib/apt/lists/* && useradd --uid 10001 --create-home valvuln
COPY lab ./lab
COPY boundary ./boundary
COPY containers/lab-network.sh /usr/local/bin/lab-network
RUN chmod 755 /usr/local/bin/lab-network && mkdir /data && chown 10001:10001 /data
ENTRYPOINT ["/usr/local/bin/lab-network", "lab"]
CMD ["uvicorn", "lab.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8001", "--workers", "1", "--no-access-log"]
