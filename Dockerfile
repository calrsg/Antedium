FROM python:3.13-slim

WORKDIR /app

# Install dependencies first so this layer is cached unless requirements change
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run as a non-root user
RUN useradd --create-home --uid 1000 bot \
    && chown -R bot:bot /app
USER bot

CMD ["python", "main.py"]
