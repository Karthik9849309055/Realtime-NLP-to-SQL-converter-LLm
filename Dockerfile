FROM python:3.11

WORKDIR /app

# System deps needed for sentence-transformers / torch
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip FIRST (important)
RUN pip install --upgrade pip

COPY requirements.txt .

# Install python deps
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]
