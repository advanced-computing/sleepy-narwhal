# 📊 Quant Analysis on NYC Daily Inmates in Custody

## 👥 Group Member: Jing Bu & Jinen Wang

**Sleepy-Narwhal**



## 🔍 Project Overview

This project analyzes **New York City’s Daily Inmates in Custody dataset** to uncover patterns in:

* Security classification disparities (MIN / MED / MAX)
* Demographic differences (race, age)
* The relationship between **mental health observation** and **infractions**

We combine **data validation, statistical analysis, and interactive visualization** to provide insights into correctional system dynamics.

---

## 🎯 Motivation

Mass incarceration and correctional systems are deeply tied to issues of:

* Social inequality
* Mental health
* Institutional bias

This project aims to use **data-driven methods** to better understand these dynamics and provide a foundation for further research and policy discussions.

---

## 🧱 Project Structure

```
sleepy-narwhal/
│
├── data_utils.py          # Data loading & preprocessing
├── data_validation.py     # Pandera-based validation
├── schemas.py             # Data schema definitions
├── streamlit_app.py       # Interactive dashboard
├── main.ipynb             # Main analysis notebook
├── tests/                 # Unit tests
├── requirements.txt
└── readme.md
```

---

## ⚙️ Tech Stack

* Python (pandas, numpy)
* Pandera (data validation)
* Streamlit (interactive app)
* Plotly (visualizations)
* Pytest (testing)

---

## 📊 Data Source

* NYC Open Data – Daily Inmates in Custody
* (Optional) Hate Crimes dataset for extended analysis

> Note: Data is assumed to follow specific formats (see validation assumptions below).

---

### 🔄 Data Ingestion Strategy

#### Data Source 1: NYC Daily Inmates in Custody

* **Loading method**: Batch loading (via CSV / API pull)
* **Reason**:
  The dataset is updated periodically (daily snapshots), and does not require real-time ingestion.
  Batch processing ensures reproducibility for analysis and consistency across experiments.

#### Data Source 2: Hate Crimes Dataset (Optional Extension)

* **Loading method**: Batch loading
* **Reason**:
  This dataset is used for exploratory or extended analysis and does not require real-time updates.
  It can be integrated as a static dataset for cross-domain insights.

#### (Future Extension) Data Source 3: Real-time Correctional Events

* **Loading method**: Streaming ingestion (e.g., API / message queue)
* **Reason**:
  If extended to a real-time dashboard, streaming data would enable live monitoring of inmate status, incidents, or facility-level changes.

---

## ✅ Data Validation Assumptions

We enforce schema validation using **Pandera**:

### Inmate Dataset

* `custody_level`: must be one of `MIN`, `MED`, `MAX`
* `race`: string (nullable allowed)

### Hate Crimes Dataset

* `complaint_year_number`: integer > 2019
* `bias_motive_description`: string (nullable allowed)

We use:

```
ignore_unknown_columns=True
```

to ensure robustness to API changes.

---

## 🚀 How to Run

### 1. Install dependencies

```
pip install -r requirements.txt
```

### 2. Run analysis notebook

Open:

```
main.ipynb
```

### 3. Launch Streamlit app

```
streamlit run streamlit_app.py
```

---

## 📈 Features

* Data cleaning & validation pipeline
* Descriptive statistics for inmate demographics
* Interactive visualizations:

  * Custody level distribution by race & age
  * Mental health vs infractions analysis
* Streamlit dashboard for exploration

---

## 🧪 Testing

Run tests with:

```
pytest
```

---

## 🤝 Contributing

We welcome contributions!

### You can help by:

* Improving data validation rules
* Adding new visualizations
* Extending datasets (e.g., time trends, policy changes)
* Refactoring code for better modularity
* Enhancing the Streamlit UI

### Steps:

1. Fork the repo
2. Create a new branch
3. Make changes
4. Submit a Pull Request

---

## 🗺️ Roadmap

* [ ] Add time-series analysis (trends over time)
* [ ] Integrate more NYC datasets
* [ ] Improve dashboard UX
* [ ] Add regression / causal analysis
* [ ] Deploy Streamlit app online

---

## ⚠️ Disclaimer

This project is for **educational and exploratory purposes only**.
Interpretations should not be taken as definitive policy conclusions.

---

## 📬 Contact

Maintained by:

* Jing Bu
* Gina Wang

---

⭐ If you find this project useful, feel free to star the repo!
