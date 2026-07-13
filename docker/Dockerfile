FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# build-essential: compiles igraph/leidenalg for scanpy's leiden backend
# r-base: required for rpy2 (Member 3's SingleR/ScType bridge)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    r-base \
    libxml2-dev \
    libcurl4-openssl-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
COPY requirements/ requirements/
RUN pip install -r requirements.txt

COPY scripts/install_r_deps.R scripts/install_r_deps.R
RUN Rscript scripts/install_r_deps.R

COPY . .

CMD ["python", "-m", "scripts.download_data"]
