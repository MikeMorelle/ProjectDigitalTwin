Systemanforderungen:

- CMAPPS train_FD001 Machinendaten werden im Producer per Zyklus sequenziert
- KafkaProducer generiert sekündlich Datenfluss (jede Maschinen_id zum Zeitpunkt t) 
- KafkaConsumer empfängt Daten, führt feature engineering aus und LSTM + IsoForest
- Anomaliedaten werden in Postgresql/Timescaledb gespeichert
- UI verbindet sich mit Datenbank und präsentiert Ergebnisse

Setup:
0. Docker geöffnet und im Ordner im Terminal des IDE's
1. docker compose down -v   (nur wenn Programm schon einmal lief... bei jedem Reset neu eingeben, damit db entleert wird)
2. docker compose up --build 
