# Instagram Profile Scraper — Apify Actor
# Uses apify/actor-python-playwright so Chromium + Playwright are pre-installed

FROM apify/actor-python-playwright:3.11

# Set working directory
WORKDIR /usr/src/app

# Copy & install Python dependencies first (layer-cache friendly)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Ensure Playwright Chromium is present
RUN playwright install chromium

# Copy project sources
COPY src/         ./src/
COPY *.py         ./
COPY config/      ./config/
COPY .actor/      ./.actor/

# Surface logs immediately
ENV PYTHONUNBUFFERED=1

CMD ["python", "src/main.py"]
