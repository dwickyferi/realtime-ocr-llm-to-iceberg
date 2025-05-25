# Real-time OCR Pipeline with MinIO, RisingWave, and Apache Iceberg

This project implements a real-time OCR (Optical Character Recognition) data pipeline that processes receipt images stored in MinIO, extracts information using LLMs (Large Language Models), and persists the data in Apache Iceberg format for analytical workloads using RisingWave as the stream processing engine.

## Architecture

```mermaid
graph LR
    A[MinIO] -->|Webhook| B[Flask API]
    B -->|Extract Text| C[Groq LLM]
    C -->|Structured Data| D[PostgreSQL]
    D -->|CDC| E[RisingWave]
    E -->|Materialized Views| F[Apache Iceberg]
    F -->|Query| G[Trino]
```

## Features

- Real-time receipt image processing using MinIO event notifications
- Text extraction and structured data generation using Groq LLM
- Change Data Capture (CDC) from PostgreSQL using RisingWave
- Stream processing and real-time analytics with RisingWave
- Data lake storage using Apache Iceberg
- SQL query capabilities using Trino

## Prerequisites

- Docker and Docker Compose
- Python 3.8+
- MinIO credentials
- Groq API key

## Components

1. **MinIO**: Object storage for receipt images
2. **Flask Webhook**: Receives MinIO events and triggers processing
3. **PostgreSQL**: Stores structured receipt data
4. **RisingWave**: Stream processing engine for CDC and analytics
5. **Apache Iceberg**: Table format for data lake storage
6. **Trino**: SQL query engine for data analysis

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/yourusername/realtime-ocr-llm-to-iceberg.git
cd realtime-ocr-llm-to-iceberg
```

2. Set up environment variables:
```bash
export GROQ_API_KEY=your_groq_api_key
```

3. Start the services:
```bash
./restart.sh
```

4. Initialize the database schema:
```bash
psql -h localhost -p 8432 -U postgres -d postgres -f sql/rw.sql
```

5. The system is now ready to process receipt images. Upload images to MinIO to trigger the pipeline.

## Project Structure

- `src/webhook.py`: Flask application for MinIO webhook and LLM processing
- `sql/rw.sql`: RisingWave materialized views and sink configurations
- `trino/`: Trino configuration files
- `docker-compose.yml`: Service definitions for all components

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
