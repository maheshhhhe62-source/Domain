# ═══════════════════════════════════════════════════════════════════════════
#  SPIDEY WEB DUMPER — Dockerfile (v2.0 Premium)
#  Python 3.11 + Latest SQLmap from GitHub
# ═══════════════════════════════════════════════════════════════════════════

FROM python:3.11-slim

# ═══ ENV ═══
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

# ═══ SYSTEM DEPS ═══
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    wget \
    build-essential \
    libssl-dev \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# ═══ INSTALL LATEST SQLMAP FROM GITHUB ═══
RUN git clone --depth 1 https://github.com/sqlmapproject/sqlmap.git /opt/sqlmap \
    && chmod +x /opt/sqlmap/sqlmap.py /opt/sqlmap/sqlmapapi.py \
    && ln -sf /opt/sqlmap/sqlmap.py /usr/local/bin/sqlmap \
    && ln -sf /opt/sqlmap/sqlmapapi.py /usr/local/bin/sqlmapapi

# ═══ WORKDIR ═══
WORKDIR /app

# ═══ PYTHON DEPS ═══
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ═══ COPY APP ═══
COPY . .

# ═══ DIRS ═══
RUN mkdir -p /app/data /app/data/outputs /app/web/static

# ═══ EXPOSE ═══
EXPOSE 8080

# ═══ START ═══
CMD ["python", "-m", "uvicorn", "web.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]