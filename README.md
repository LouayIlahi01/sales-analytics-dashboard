# Sales Analytics Dashboard

Interactive sales dashboard built with **Python, Dash, Plotly and Pandas**.

Uses a synthetic dataset for demonstration.

![Dashboard screenshot](assets/screenshot.png)

## Features
- Revenue headline with month-over-month change, plus Orders, Profit and Customers columns, each with a monthly bar sparkline and a dashed average line (hover a bar for its value)
- Auto-generated key insights (top category, margin, best month)
- Sales vs profit trend with the best month pinned
- Weekday-by-month activity heatmap
- Top 5 products with category tags
- Dark purple theme: pill filters for category and region, segmented control for quarter

## Performance choices
- Data loaded once with `functools.lru_cache`
- A single callback updates all components, so filters trigger one pass over the data
- Filtering and aggregation are done with vectorised Pandas operations

## Run locally
Requires **Python 3.9+**

```bash
git clone https://github.com/Louaylahi01/sales-analytics-dashboard.git
cd sales-analytics-dashboard
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Optional: Regenerate the synthetic dataset (a pre-generated CSV is already included)
python generate_data.py      

python app.py                # open http://127.0.0.1:8050
