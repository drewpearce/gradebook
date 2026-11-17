# pg_dump must be at least the Neon server's major version (Neon project is on PG 17).
FROM postgres:17-alpine
RUN apk add --no-cache aws-cli curl bash
# Newer aws-cli checksum headers have broken R2 uploads.
ENV AWS_REQUEST_CHECKSUM_CALCULATION=when_required AWS_RESPONSE_CHECKSUM_VALIDATION=when_required
COPY backup.sh /usr/local/bin/backup.sh
ENTRYPOINT []
CMD ["bash", "/usr/local/bin/backup.sh"]
