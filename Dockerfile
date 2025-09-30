FROM python:3.9-slim

# Defina o diretório de trabalho
WORKDIR /app

# Copie os arquivos necessários para o diretório de trabalho
COPY . /app

# Instale as dependências
RUN pip install -r requirements.txt

# Configura o OTLP
RUN opentelemetry-bootstrap -a install

# Exponha a porta que a aplicação vai rodar
EXPOSE 5000

# Comando para rodar a aplicação
CMD ["opentelemetry-instrument", "python", "app.py"]