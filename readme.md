# Project Name: Quant Analysis on NYC's Daily Inmates in Custody
## Group Name: 
Sleep-Narwhal
## Project Description: 

Analyzed NYC inmate custody data to explore demographic disparities in security classification and the relationship between mental health observation and infractions using interactive visualizations.

## Assumptions made for Data Validation:

For the Inmates dataset, we are assuming that:

The custody_level column will consistently use the specific acronyms "MIN", "MED", and "MAX". If the API provider changes this to full words (e.g., "Minimum"), our mappings will fail, so we validate against this specific list.

The race column will be formatted as strings. Null values are acceptable and expected.

For the Hate Crimes dataset, we are assuming that:

The complaint_year_number must be a valid integer larger than 2019. We use coerce=True because the API might return years as string types instead of numeric types.

The bias_motive_description column should consistently be of string type, allowing for empty/null values when the motive is unknown.

By using ignore_unknown_columns=True, we assume that adding new columns to the API won't break our application, as we only validate the columns we actively use for our visualizations.

## Setup & Usage
*Setup*

Ensure Python 3 is installed.
Install required Python packages:
Download or clone the project repository and confirm that main.ipynb is located in the project root directory.

*Usage*

Open the notebook:
<a target="_blank" href="https://colab.research.google.com/github/advanced-computing/sleepy-narwhal/blob/main/main.ipynb">
  <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/>
</a>

Run the notebook cells sequentially from top to bottom.
The notebook will:
1. Load and clean the NYC Daily Inmates in Custody dataset
2. Generate descriptive statistics for inmate demographics
3. Produce an interactive stacked bar chart showing custody level distribution by race and age
4. Explore the relationship between mental health observation status and recorded infractions
5. All visualizations and outputs are generated directly within the notebook; no external configuration is required.

