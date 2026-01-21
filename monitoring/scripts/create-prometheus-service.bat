@echo off
REM Script batch pour creer le service Prometheus avec la bonne syntaxe

sc.exe delete Prometheus

sc.exe create Prometheus binPath= "\"C:\Prometheus\prometheus.exe\" --config.file=\"C:\Prometheus\prometheus.yml\" --storage.tsdb.path=\"C:\Prometheus\data\" --storage.tsdb.retention.time=30d --web.listen-address=0.0.0.0:9090" start= auto DisplayName= "Prometheus Server"

sc.exe description Prometheus "Prometheus monitoring system and time series database"

echo Service cree. Demarrage...
net start Prometheus

pause











