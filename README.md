# MuscleTone Fitness - Streamlit Edition

A gym membership management app with a modern web UI using Streamlit. Uses the same SQLite database as the original Tkinter app so you can switch between them.

## Features
- Dashboard with key statistics (Total, Active, Expiring)
- Members table with search and CSV export
- Add / Edit / Delete members
- Uses local SQLite database: `~/MuscleToneFitness/gym_data.db`

## Setup
```bash
# From the project folder
pip install -r requirements.txt
```

## Run (Streamlit)
```bash
streamlit run streamlit_app.py
```
Then open the URL shown in the terminal (usually http://localhost:8501).

## Optional: Populate sample data
```bash
python sample_data.py
```

## Original desktop app (optional)
The previous Tkinter version still exists as `maingym.py`.
```bash
python maingym.py
```

## Notes
- All data is stored locally at `~/MuscleToneFitness/gym_data.db`.
- Streamlit app and Tkinter app share the same database schema.
