# Dockerfile

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy your code
COPY . /app

# Install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose the FastAPI port
EXPOSE 8000

# Run your app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
