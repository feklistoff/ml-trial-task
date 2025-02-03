FROM python:3.11-slim

# Install system dependencies (e.g. for Pillow, torchvision, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container.
COPY ./poetry.lock ./pyproject.toml ./README.rst ./src /app/
WORKDIR /app

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install Poetry and project dependencies
RUN pip install --upgrade pip && pip install poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

COPY . /app

# Set the default command to run service
CMD ["python", "src/ml_trial_task/console.py", "service", "-vv", "config.toml"]
