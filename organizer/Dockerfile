# Run the organizer 24/7 on any server or cloud host that runs Docker.
#
#   docker build -t organizer .
#   docker run -d --name organizer --restart unless-stopped \
#     -p 8765:8765 -v organizer-data:/data --env-file .env \
#     -e ORGANIZER_WEB_TOKEN=<long random text> organizer
#
# Then open http://<server>:8765/?token=<that text> once.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    ORGANIZER_HOME=/data \
    ORGANIZER_WEB_HOST=0.0.0.0 \
    ORGANIZER_WEB_PORT=8765

RUN useradd --create-home --uid 1000 organizer && mkdir /data && chown organizer /data
WORKDIR /app
COPY organizer ./organizer
USER organizer
VOLUME ["/data"]
EXPOSE 8765
HEALTHCHECK --interval=60s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/health', timeout=4)"
CMD ["python", "-m", "organizer", "run"]
