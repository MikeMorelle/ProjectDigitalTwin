Systemanforderungen:

- CMAPPS train_FD001 Daten werden im Producer mit Rolling Features berechnet
- KafkaProducer generiert sekündlich Datenfluss (jede Maschinen_id zum Zeitpunkt t) aus CMAPPS train_FD001
- KafkaConsumer empfängt Daten, führt Anomalie-Detektor aus (später RUL und explainability)
- Anomaliedaten werden in Postgresql/Timescaledb gespeichert
- UI verbindet sich mit Datenbank und präsentiert mittels autorefreshing streamlit OK oder Warnungen
