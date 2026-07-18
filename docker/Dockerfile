# docker/Dockerfile — full image with R/SingleR (Member 4, Task 8)
FROM python:3.11-slim

# system deps + R
RUN apt-get update && apt-get install -y --no-install-recommends \
    r-base r-base-dev build-essential \
    libcurl4-openssl-dev libssl-dev libxml2-dev libfontconfig1-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python deps first (layer caching)
COPY requirements/ requirements/
RUN pip install --no-cache-dir \
    -r requirements/base.txt \
    -r requirements/app.txt \
    -r requirements/agents.txt

# R deps (SingleR + celldex) — slow layer, cached unless requirements change
RUN R -e "install.packages('BiocManager', repos='https://cloud.r-project.org'); \
          BiocManager::install(c('SingleR','celldex'), update=FALSE, ask=FALSE)"

COPY . .
ENV PYTHONPATH=/app
ENV R_HOME=/usr/lib/R
EXPOSE 8000 8501

CMD ["python", "-m", "src.api.main"]