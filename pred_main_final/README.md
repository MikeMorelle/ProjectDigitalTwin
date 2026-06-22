System:

- CMAPPS Daten werden im Producer mit Rolling Features berechnet
- KafkaProducer generiert im gewählten Sekundeninterval Datenfluss (jede Maschinen_id zum Zeitpunkt t)
- KafkaConsumer empfängt Daten und speichert diese in Postgresql/Timescaledb ab
- UI verbindet sich mit Datenbank, skaliert, predicted und präsentiert mittels Ausgaben

Wie starten?
0. Docker (Desktop) aktiv + Terminal in Pred_main_final offen
1. docker compose down -v                    #sicherstellen, dass keine Konflikte entstehen
2. docker compose up --build                #Projekt starten
3. abwarten und wenn in Konsole api/uvicorn ready ist (Uvicorn running on ...), dann Datensatz in setup auswählen und los geht`s

