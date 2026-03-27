import time

import streamlit as st

start_time = time.time()
st.set_page_config(page_title="NYC Public Safety Analysis", layout="wide")

st.title("NYC Public Safety: Inmates & Hate Crimes Analysis")
st.markdown("### Group sleepy-narwhal: Jinen (Gina) Wang, Jing Bu")
st.markdown("---")

st.header("Part 1: Original Proposal (As Is)")
st.markdown("""
**1. What dataset are you going to use?**
* **Dataset Name:** Daily Inmates In Custody
* **Source:** NYC Open Data (Department of Correction)
* **Link:** [https://data.cityofnewyork.us/Public-Safety/Daily-Inmates-In-Custody/7479-ugqb](https://data.cityofnewyork.us/Public-Safety/Daily-Inmates-In-Custody/7479-ugqb)

**2. What are your research question(s)?**
* **Option A (Focus on Demographics & Security):** How does the distribution of custody
            levels (Min, Med, Max) vary across different racial groups and age brackets
                within the NYC inmate population? Specifically, is there a statistically
            significant correlation between an inmate's age and their assigned security
            risk level (age will be broken down into age groups as brackets)?
* **Option B (Focus on Mental Health):** What is the prevalence of mental health observation
                (BRADH flag) among the inmate population, and how does this overlap with the
            'Infraction' status? Are inmates under mental observation more likely to have
                recorded infractions compared to the general population?

**3. What's the link to your notebook?**
* **Link:** [https://github.com/advanced-computing/sleepy-narwhal/blob/branch1/main.ipynb](https://github.com/advanced-computing/sleepy-narwhal/blob/branch1/main.ipynb)

**4. What's your target visualization? Include a picture.**
* **Description:** We plan to create an interactive Stacked Bar Chart (using Plotly) to
            visualize the relationship between Race and Custody Level. The x-axis will
            represent different racial groups, while the y-axis will show the count of
            inmates, color-coded by their Custody Level (Min, Med, Max). This will allow
            for a clear comparison of security classifications across demographics and this
            visualization allows both absolute comparison and proportional inter.
* **Picture:**
""")
st.markdown("")

st.markdown("""
**5. What are your known unknowns? What challenges do you anticipate?**
* **Data Snapshot vs. Trends:** The dataset provides a daily snapshot ("Daily Inmates In
            Custody"). It does not inherently show historical trends or how an individual's
                status changes over time unless I implement a script to collect data daily,
            which is outside the scope of a static analysis.
* **Missing or Categorical Ambiguity:** Columns like race or gender may have missing values
                or "Unknown" categories which could skew the demographic analysis. The definition
            of specific codes (like specific INFRACTION types) is not detailed in the dataset,
                limiting the depth of behavioral analysis.
* **Causality vs. Correlation:** While there’s evidence that certain groups have higher custody
            levels, the data does not contain the detailed case files or legal history required
            to explain why this is the case. So we must be careful not to imply causation from
            simple correlations.
""")

st.markdown("---")
st.header("Part 2: Revisiting the Proposal (Updates & Insights)")
# ... (把你原来 tab1 里的所有 Updates 文本粘贴到这里) ...
st.markdown("""
**Adjustments Made:**
1. **Addition of a Second Dataset:** We expanded our scope by incorporating the
        **NYPD Hate Crimes dataset**. The original proposal solely focused on
        the systemic side of public safety (inmates).
2. **Refined Focus:** While we kept our Option A research question regarding inmate
            demographics, we broadened our narrative to contrast "systemic penalization"
            with "community victimization."

**New Insights Discovered:**
* **Stark Demographic Contrasts:** The data reveals compelling concrete numbers
            regarding race. In the DOC Inmate data, Black and Hispanic individuals
            disproportionately make up the vast majority of the custody population
            (often exceeding **85%** combined), especially within the Maximum custody
            levels.
* **The Flip Side of Public Safety:** Conversely, the Hate Crimes data reveals
            different racial and ethnic dynamics in community victimization. For
            instance, specific minority groups (such as Jewish and Asian communities)
            frequently emerge as the top targets of bias motives (e.g., Anti-Semitic
            and Anti-Asian motives often account for hundreds of reported incidents
            annually).
* **Conclusion:** Relying solely on the inmate dataset would give a skewed,
            one-sided view of race in NYC public safety. By combining both, we
            can observe that racial vulnerability manifests differently: certain
            groups are more vulnerable to systemic incarceration, while others are
            highly vulnerable to targeted societal hate crimes.
""")


elapsed = time.time() - start_time
st.caption(f"⏱️ Page loaded in {elapsed:.2f} seconds")
