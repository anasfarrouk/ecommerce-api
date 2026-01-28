FROM python:3.14-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Add a user
RUN useradd -m -r admin

# Create application directory
RUN mkdir /ecommerce-api 
RUN chown -R admin /ecommerce-api

WORKDIR /ecommerce-api

# Copy the application code
COPY --chown=admin:admin . .

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_NO_DEV=1

# Sync the project into a new environment
RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev gcc
RUN rm -rf /var/lib/apt/lists/*
RUN uv sync --locked

# Change to non-root user
USER admin

# Expose the application port
EXPOSE 8000

# Command to run migrations and start the Gunicorn server
CMD ["./entrypoint.sh"]
