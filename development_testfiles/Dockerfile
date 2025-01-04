FROM postgres:latest

# Set environment variables
ENV POSTGRES_PASSWORD=123456

# Kopiere die testDatabase.sql ins Image
COPY testDatabase.sql /docker-entrypoint-initdb.d/

# Generate certs
RUN mkdir -p /var/lib/postgresql/certs && \
    cd /var/lib/postgresql/certs && \
    openssl genpkey -algorithm RSA -out server.key -pkeyopt rsa_keygen_bits:2048 && \
    openssl req -new -key server.key -out server.csr -subj "/CN=localhost" && \
    openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt && \
    # Set permissions
    chown -R postgres:postgres /var/lib/postgresql/certs && \
    chmod 600 /var/lib/postgresql/certs/* && \
    rm /var/lib/postgresql/certs/server.csr && \
    echo "ssl = on" >> /usr/share/postgresql/postgresql.conf.sample && \
    echo "ssl_cert_file = '/var/lib/postgresql/certs/server.crt'" >> /usr/share/postgresql/postgresql.conf.sample && \
    echo "ssl_key_file = '/var/lib/postgresql/certs/server.key'" >> /usr/share/postgresql/postgresql.conf.sample

EXPOSE 5432

# Start postgresql with ssl
CMD ["postgres"]
