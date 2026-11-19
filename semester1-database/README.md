# Neo-Sousse 2030 — Databases module

First part of the project: modelling the smart city's data and building a first analytics dashboard.

- `schema.sql`: tables for owners, sensors, measurements, technicians, interventions, citizens, vehicles and trips
- `seed.sql`: sample data for Sousse
- `dashboard_app.py`: Streamlit dashboard (city overview, air quality, sensors, maintenance, citizens, mobility)
- Report and ER diagram: [`../docs/`](../docs/)

```bash
psql -U postgres -d smart_city -f schema.sql
psql -U postgres -d smart_city -f seed.sql
pip install -r requirements.txt
DB_PASS=your_password streamlit run dashboard_app.py
```
