FROM python:3.9-slim

# Defina o diretório de trabalho
WORKDIR /app

# Copie os arquivos necessários para o diretório de trabalho
COPY . /app

# Instale as dependências
RUN pip install flask fastapi opentelemetry-distro opentelemetry-exporter-otlp

# Configura o OTLP
RUN opentelemetry-bootstrap -a install

ARG OTEL_EXPORTER_OTLP_ENDPOINT
ARG OTEL_SERVICE_NAME
ARG OTEL_EXPORTER_OTLP_INSECURE
ARG OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED
ARG OTEL_TRACES_EXPORTER
ARG OTEL_METRICS_EXPORTER
ARG OTEL_LOGS_EXPORTER

ENV OTEL_EXPORTER_OTLP_ENDPOINT=${OTEL_EXPORTER_OTLP_ENDPOINT}
ENV OTEL_SERVICE_NAME=${OTEL_SERVICE_NAME}
ENV OTEL_EXPORTER_OTLP_INSECURE=${OTEL_EXPORTER_OTLP_INSECURE}
ENV OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=${OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED}
ENV OTEL_TRACES_EXPORTER=${OTEL_TRACES_EXPORTER}
ENV OTEL_METRICS_EXPORTER=${OTEL_METRICS_EXPORTER}
ENV OTEL_LOGS_EXPORTER={OTEL_LOGS_EXPORTER}

# Exponha a porta que a aplicação vai rodar
EXPOSE 8080

# Comando para rodar a aplicação
CMD ["opentelemetry-instrument","--traces_exporter", "otlp,console", "--metrics_exporter", "otlp,console", "--logs_exporter", "otlp,console", "--service_name", "sfz-python", "flask", "run", "-p", "8080"]