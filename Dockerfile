# Stage 1: install dependencies
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

# Install system dependencies needed for common python packages
RUN apt-get update \
 && apt-get install -y --no-install-recommends gcc build-essential libpq-dev curl \
 && rm -rf /var/lib/apt/lists/*

# Copy requirements (or pyproject/poetry if you use that)
COPY requirements.txt /app/requirements.txt

# Install into site-packages under /usr/local (no virtualenv)
RUN pip install --upgrade pip setuptools wheel \
 && pip wheel --no-cache-dir --wheel-dir /wheels -r /app/requirements.txt

# Stage 2: final image
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Minimal runtime deps (curl useful for healthchecks)
RUN apt-get update \
 && apt-get install -y --no-install-recommends libpq5 curl \
 && rm -rf /var/lib/apt/lists/*

# Copy wheels and install
COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/*

# Copy app code
COPY . /app

# Create directory for static files
RUN mkdir -p /vol/static /vol/media

# Expose port (Gunicorn will bind to 8000)
EXPOSE 8000

# copy entrypoint and give execute permission
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# run as non-root for safety
RUN groupadd -r app && useradd -r -g app app && chown -R app:app /app /vol
USER app

ENTRYPOINT ["/app/entrypoint.sh"]
# CMD is handled inside entrypoint (gunicorn exec)