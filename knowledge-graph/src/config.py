"""
Knowledge graph configuration.

Loads Neo4j connection settings, embedding parameters,
and graph update policies from environment variables.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class GraphConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "vayu_graph_secret"
    neo4j_database: str = "vayu"

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    kafka_brokers: str = "localhost:9092"
    kafka_consumer_group: str = "vayu-knowledge-graph"
    kafka_satellite_topic: str = "raw.satellite"
    kafka_sensor_topic: str = "raw.sensor"
    kafka_weather_topic: str = "raw.weather"
    kafka_traffic_topic: str = "raw.traffic"
    kafka_citizen_topic: str = "raw.citizen"

    graph_embedding_dim: int = 128
    graph_node2vec_walks: int = 10
    graph_node2vec_length: int = 80

    @property
    def kafka_broker_list(self) -> list[str]:
        return [b.strip() for b in self.kafka_brokers.split(",")]


graph_config = GraphConfig()
