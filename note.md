```bash
PYTHONPATH=src python src/run/run_dbbert.py demo_docs/postgres100 64000000000 200000000000 8 pg tpch dbbert dbbert "sudo service postgresql restart" ./tpchdata/queries.sql --recover_cmd="sudo rm /var/lib/postgresql/12/main/postgresql.auto.conf"
```

text_source_path = demo_docs/postgres100
memory=64000000000 (bytes)
disk=200000000000 (bytes)
cores=8
dbms=pg
db_name=tpch
db_user=dbbert
db_pwd=dbbert
restart_cmd = "sudo service postgresql restart"
query_path=./tpchdata/queries.sql
recover_cmd="sudo rm /var/lib/postgresql/12/main/postgresql.auto.conf"
