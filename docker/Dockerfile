FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install Poetry
ENV POETRY_HOME="/opt/poetry"
ENV PATH="$POETRY_HOME/bin:$PATH"
RUN curl -sSL https://install.python-poetry.org | python3 - 

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --with dev --no-interaction --no-ansi --no-root

# Copy application code
COPY . .

# Install project
RUN poetry install --no-interaction --no-ansi

EXPOSE 8000

CMD ["uvicorn", "apps.crl.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

