
from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px


# --------------------------------------------------
# 1. PAGE SETUP
# --------------------------------------------------

st.set_page_config(
    page_title="FlameGuard | FLEX Explorer",
    page_icon="🔥",
    layout="wide",
)

PROJECT_DIR = Path(__file__).resolve().parent
RAW_DATA_DIR = PROJECT_DIR / "raw_1"


# --------------------------------------------------
# 2. LOAD THE ORIGINAL DATA
# --------------------------------------------------f

@st.cache_data
def load_flex_data():
    csv_files = list(RAW_DATA_DIR.glob("*.csv"))

    if len(csv_files) == 0:
        raise FileNotFoundError(
            "No CSV found in data/raw/. "
            "Place the original NASA FLEX CSV there."
        )

    if len(csv_files) > 1:
        raise ValueError(
            "Multiple CSV files found in data/raw/. "
            "Keep only the intended FLEX CSV there."
        )

    return pd.read_csv(csv_files[0], encoding="cp1252")


try:
    df = load_flex_data()
except (FileNotFoundError, ValueError, UnicodeDecodeError) as error:
    st.error(str(error))
    st.stop()


# --------------------------------------------------
# 3. HELPER FUNCTIONS
# --------------------------------------------------

def categorical_filter(data, column, label):
    """Return the data matching the selected categories."""

    values = data[column].fillna("Not recorded").astype(str)
    options = sorted(values.unique().tolist())

    selected = st.sidebar.multiselect(
        label,
        options=options,
        default=options,
        key=f"filter_{column}",
    )

    return values.isin(selected)


def numeric_filter(data, column, label, include_missing=True):
    """
    Filter a numeric column without modifying the source data.

    Values that cannot be parsed as numbers are treated as
    unavailable for this filter, but their original values remain
    unchanged in the dataset.
    """

    numeric_values = pd.to_numeric(data[column], errors="coerce")
    valid_values = numeric_values.dropna()

    st.sidebar.markdown(f"**{label}**")

    # If no numeric measurements exist, don't offer a range slider.
    if valid_values.empty:
        st.sidebar.caption("No numeric measurements available.")
        return pd.Series(True, index=data.index)

    minimum = float(valid_values.min())
    maximum = float(valid_values.max())

    if minimum == maximum:
        st.sidebar.caption(f"Only one numeric value: {minimum:g}")
        return pd.Series(True, index=data.index)

    selected_range = st.sidebar.slider(
        label,
        min_value=minimum,
        max_value=maximum,
        value=(minimum, maximum),
        key=f"range_{column}",
    )

    low, high = selected_range

    # Missing or non-numeric values are retained by default.
    missing_mask = numeric_values.isna()

    keep_mask = numeric_values.between(low, high)

    if include_missing:
        keep_mask = keep_mask | missing_mask

    return keep_mask


# --------------------------------------------------
# 4. DASHBOARD HEADER
# --------------------------------------------------

st.title("🔥 FlameGuard")
st.subheader("FLEX Experiment Explorer")

st.write(
    "Search, filter, and explore NASA FLEX "
    "liquid-fuel droplet combustion experiments."
)

if len(df) == 274:
    st.success("Dataset loaded: all 274 experiments are available.")
else:
    st.warning(
        f"Expected 274 experiments; loaded {len(df)}. "
        "Check the source CSV."
    )


# --------------------------------------------------
# 5. SIDEBAR: SEARCH AND FILTERS
# --------------------------------------------------

st.sidebar.title("Experiment Explorer")
st.sidebar.caption("Filters apply to the displayed results.")

# Search by test number or FLEX identifier.
search_query = st.sidebar.text_input(
    "Search test number or FLEX identifier",
    placeholder="e.g. 223 or FLEX identifier",
)

st.sidebar.divider()
st.sidebar.subheader("Categorical filters")

required_columns = [
    "FLEX Test #",
    "FLEX Identifier",
    "Fuel",
    "Test end",
    "Ambient pressure; mmHg",
    "Droplet initial diameter; mm",
    "Burn time; s",
]

missing_columns = [col for col in required_columns if col not in df.columns]

if missing_columns:
    st.error(
        "The CSV is missing expected columns: "
        + ", ".join(missing_columns)
    )
    st.stop()

fuel_mask = categorical_filter(df, "Fuel", "Fuel")
outcome_mask = categorical_filter(df, "Test end", "Test outcome")

st.sidebar.divider()
st.sidebar.subheader("Numerical filters")

include_missing = st.sidebar.checkbox(
    "Keep records with missing or non-numeric measurements",
    value=True,
    help=(
        "When enabled, records with unavailable measurements "
        "remain visible even when a numerical range is selected."
    ),
)

pressure_mask = numeric_filter(
    df, "Ambient pressure; mmHg", "Ambient pressure (mmHg)"
)

diameter_mask = numeric_filter(
    df, "Droplet initial diameter; mm", "Initial droplet diameter (mm)"
)

burn_time_mask = numeric_filter(
    df, "Burn time; s", "Burn time (s)"
)


# --------------------------------------------------
# 6. COMBINE FILTERS
# --------------------------------------------------

# Search both identifier columns using partial text matching.
if search_query.strip():
    query = search_query.strip().casefold()

    test_number_mask = (
        df["FLEX Test #"]
        .astype("string")
        .str.casefold()
        .str.contains(query, na=False, regex=False)
    )

    identifier_mask = (
        df["FLEX Identifier"]
        .astype("string")
        .str.casefold()
        .str.contains(query, na=False, regex=False)
    )

    search_mask = test_number_mask | identifier_mask
else:
    search_mask = pd.Series(True, index=df.index)


# Every selected condition must match.
combined_mask = (
    search_mask
    & fuel_mask
    & outcome_mask
    & pressure_mask
    & diameter_mask
    & burn_time_mask
)

# Create a filtered view. The original df remains unchanged.
filtered_df = df.loc[combined_mask].copy()


# --------------------------------------------------
# 7. RESULT SUMMARY
# --------------------------------------------------

st.divider()
st.subheader("Experiment search results")

col1, col2, col3 = st.columns(3)

col1.metric("Total source experiments", len(df))
col2.metric("Matching experiments", len(filtered_df))
col3.metric(
    "Experiments not shown",
    len(df) - len(filtered_df),
)

st.caption(
    "Numerical filtering uses temporary numeric conversions. "
    "Original recorded values are preserved in the results table."
)


# --------------------------------------------------
# 8. FILTERED DISTRIBUTION CHARTS
# --------------------------------------------------

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.markdown("**Fuel distribution in matching results**")

    fuel_counts = (
        filtered_df["Fuel"]
        .fillna("Not recorded")
        .astype(str)
        .value_counts()
        .rename_axis("Fuel")
        .reset_index(name="Experiments")
    )

    fig_fuel = px.bar(
        fuel_counts,
        x="Fuel",
        y="Experiments",
        text="Experiments",
    )

    st.plotly_chart(fig_fuel, use_container_width=True)

with chart_col2:
    st.markdown("**Test outcomes in matching results**")

    outcome_counts = (
        filtered_df["Test end"]
        .fillna("Not recorded")
        .astype(str)
        .value_counts()
        .rename_axis("Test outcome")
        .reset_index(name="Experiments")
    )

    fig_outcomes = px.bar(
        outcome_counts,
        x="Test outcome",
        y="Experiments",
        text="Experiments",
    )

    st.plotly_chart(fig_outcomes, use_container_width=True)


# --------------------------------------------------
# 9. DISPLAY MATCHING EXPERIMENTS
# --------------------------------------------------

st.divider()
st.subheader("Matching experiment records")

if filtered_df.empty:
    st.info(
        "No experiments match the current search and filters. "
        "Try a different search or widen the numerical ranges."
    )
else:
    st.dataframe(
        filtered_df,
        hide_index=True,
        use_container_width=True,
        height=450,
    )

    st.caption(
        f"Displaying {len(filtered_df)} matching experiments "
        f"out of {len(df)} original experiments."
    )


# --------------------------------------------------
# 10. INDIVIDUAL EXPERIMENT DETAILS
# --------------------------------------------------

st.divider()
st.subheader("Experiment details")

if filtered_df.empty:
    st.info(
        "No experiments are available to inspect. "
        "Adjust the search or filters above."
    )

else:
    # Build a readable label for each available experiment.
    def experiment_label(index):
        row = df.loc[index]

        test_number = row["FLEX Test #"]
        identifier = row["FLEX Identifier"]

        test_number = (
            "Not recorded"
            if pd.isna(test_number)
            else str(test_number)
        )

        identifier = (
            "Not recorded"
            if pd.isna(identifier)
            else str(identifier)
        )

        return f"Test {test_number} | {identifier}"

    available_indices = filtered_df.index.tolist()

    selected_index = st.selectbox(
        "Select an experiment to inspect",
        options=available_indices,
        format_func=experiment_label,
        key="selected_experiment",
    )

    selected_experiment = df.loc[selected_index]

    st.caption(
        "The selector contains only experiments matching "
        "your current search and filter settings."
    )


    # --------------------------------------------------
    # 11. FORMAT VALUES FOR DISPLAY
    # --------------------------------------------------

    def display_value(value):
        """Format missing values without changing the source."""

        if pd.isna(value):
            return "Not recorded"

        return str(value)


    # --------------------------------------------------
    # 12. EXPERIMENT SUMMARY
    # --------------------------------------------------

    st.markdown("### Experiment summary")

    summary_col1, summary_col2, summary_col3 = st.columns(3)

    summary_col1.metric(
        "FLEX Test #",
        display_value(selected_experiment["FLEX Test #"]),
    )

    summary_col2.metric(
        "Fuel",
        display_value(selected_experiment["Fuel"]),
    )

    summary_col3.metric(
        "Test outcome",
        display_value(selected_experiment["Test end"]),
    )


    # --------------------------------------------------
    # 13. GROUP RELATED MEASUREMENTS
    # --------------------------------------------------

    field_groups = {
        "Test information": [
            "FLEX Test #",
            "FLEX Identifier",
            "Test Date",
            "Test GMT",
            "Test end",
        ],

        "Combustion environment": [
            "Fuel",
            "Ambient pressure; mmHg",
            "O initial ambient composition; mole fraction",
            "N initial ambient composition; mole fraction",
            "CO initial ambient composition; mole fraction",
            "He initial ambient composition; mole fraction",
        ],

        "Droplet and combustion measurements": [
            "Droplet initial diameter; mm",
            "Visible flame extinction diameter; mm",
            "Burning rate; mm",
            "Burn time; s",
        ],
    }


    # --------------------------------------------------
    # 14. DISPLAY EACH GROUP
    # --------------------------------------------------

    st.markdown("### Recorded experimental conditions")

    for group_name, fields in field_groups.items():
        # Some NASA files may have extra or renamed columns.
        # Only display fields actually present in the CSV.
        available_fields = [
            field for field in fields
            if field in selected_experiment.index
        ]

        if not available_fields:
            continue

        st.markdown(f"#### {group_name}")

        details = pd.DataFrame({
            "Field": available_fields,
            "Recorded value": [
                display_value(selected_experiment[field])
                for field in available_fields
            ],
        })

        st.dataframe(
            details,
            hide_index=True,
            use_container_width=True,
        )


    # --------------------------------------------------
    # 15. SHOW THE COMPLETE ORIGINAL RECORD
    # --------------------------------------------------

    with st.expander("View all original columns"):
        complete_record = pd.DataFrame({
            "Original column": selected_experiment.index.tolist(),
            "Recorded value": [
                display_value(value)
                for value in selected_experiment.tolist()
            ],
        })

        st.dataframe(
            complete_record,
            hide_index=True,
            use_container_width=True,
        )



# --------------------------------------------------
# 16. COMPARE TWO EXPERIMENTS
# --------------------------------------------------

st.divider()
st.title("Compare Experiments")

st.write(
    "Compare two original FLEX experiment records and explore "
    "a selected measurement using an interactive graph."
)


def comparison_display_value(value):
    """Format a source value for display without changing it."""
    if pd.isna(value):
        return "Not recorded"
    return str(value)


def comparison_label(index):
    """Create a readable experiment selector label."""
    row = df.loc[index]

    test_number = comparison_display_value(row["FLEX Test #"])
    identifier = comparison_display_value(row["FLEX Identifier"])

    return f"Test {test_number} | {identifier}"


# Use all original records, not filtered_df.
all_indices = df.index.tolist()

if len(all_indices) < 2:
    st.warning("At least two experiments are required for comparison.")

else:
    compare_col1, compare_col2 = st.columns(2)

    with compare_col1:
        experiment_a_index = st.selectbox(
            "Experiment A",
            options=all_indices,
            index=0,
            format_func=comparison_label,
            key="compare_experiment_a",
        )

    with compare_col2:
        # Default to a different record from Experiment A.
        default_b_position = 1

        experiment_b_index = st.selectbox(
            "Experiment B",
            options=all_indices,
            index=default_b_position,
            format_func=comparison_label,
            key="compare_experiment_b",
        )

    if experiment_a_index == experiment_b_index:
        st.warning(
            "Select two different experiments to compare them."
        )

    else:
        experiment_a = df.loc[experiment_a_index]
        experiment_b = df.loc[experiment_b_index]

        st.success("Two distinct experiments selected.")





        # ------------------------------------------
        # 17. SIDE-BY-SIDE RECORD COMPARISON
        # ------------------------------------------

        st.subheader("Recorded values side by side")

        comparison_table = pd.DataFrame({
            "Field": df.columns.tolist(),
            "Experiment A": [
                comparison_display_value(experiment_a[col])
                for col in df.columns
            ],
            "Experiment B": [
                comparison_display_value(experiment_b[col])
                for col in df.columns
            ],
        })

        st.dataframe(
            comparison_table,
            hide_index=True,
            use_container_width=True,
        )

        st.caption(
            "Values are shown as recorded in the original CSV. "
            "Not recorded indicates a missing value; approximate "
            "strings and unusual recorded values are preserved."
        )




        # ------------------------------------------
        # 18. AUTOMATIC LINE GRAPH COMPARISON
        # ------------------------------------------

        st.subheader("Experiment comparison profile")

        st.write(
            "Compare all available numeric measurements for both "
            "experiments in one line graph."
        )

        measurement_columns = [
            "Ambient pressure; mmHg",
            "O initial ambient composition; mole fraction",
            "N initial ambient composition; mole fraction",
            "CO initial ambient composition; mole fraction",
            "He initial ambient composition; mole fraction",
            "Droplet initial diameter; mm",
            "Visible flame extinction diameter; mm",
            "Burning rate; mm",
            "Burn time; s",
        ]

        # Keep only measurement columns present in the CSV.
        measurement_columns = [
            col for col in measurement_columns
            if col in df.columns
        ]

        # Convert measurements temporarily to numeric values.
        # Original values in df remain unchanged.
        numeric_data = pd.DataFrame(index=df.index)

        for column in measurement_columns:
            numeric_data[column] = pd.to_numeric(
                df[column],
                errors="coerce",
            )

        # Normalize each measurement against its range across
        # the complete dataset, not just the selected pair.
        normalized_data = pd.DataFrame(index=df.index)

        for column in measurement_columns:
            series = numeric_data[column]
            valid = series.dropna()

            if valid.empty:
                continue

            minimum = valid.min()
            maximum = valid.max()

            # A constant variable cannot show differences
            # after min-max normalization.
            if maximum == minimum:
                continue

            normalized_data[column] = (
                (series - minimum) / (maximum - minimum)
            )

        if normalized_data.empty:
            st.warning(
                "No variable measurements are available "
                "to create the comparison graph."
            )

        else:
            # Retrieve both experiments' normalized profiles.
            experiment_a_profile = normalized_data.loc[
                experiment_a_index
            ]

            experiment_b_profile = normalized_data.loc[
                experiment_b_index
            ]

            experiment_a_name = comparison_label(
                experiment_a_index
            )
            experiment_b_name = comparison_label(
                experiment_b_index
            )

            graph_rows = []

            for column in normalized_data.columns:
                graph_rows.append({
                    "Measurement": column,
                    "Experiment": experiment_a_name,
                    "Normalized value": experiment_a_profile[column],
                })

                graph_rows.append({
                    "Measurement": column,
                    "Experiment": experiment_b_name,
                    "Normalized value": experiment_b_profile[column],
                })

            graph_data = pd.DataFrame(graph_rows)

            # Missing measurements remain missing in the graph.
            # Plotly leaves gaps instead of inventing values.
            fig_compare = px.line(
                graph_data,
                x="Measurement",
                y="Normalized value",
                color="Experiment",
                markers=True,
                title="Normalized measurement profiles",
                category_orders={
                    "Measurement": normalized_data.columns.tolist()
                },
                hover_data={
                    "Measurement": True,
                    "Experiment": True,
                    "Normalized value": ":.3f",
                },
            )

            fig_compare.update_layout(
                xaxis_title="Recorded measurement",
                yaxis_title="Normalized value (0–1)",
                yaxis=dict(range=[0, 1]),
                hovermode="x unified",
                legend_title="Experiment",
            )

            fig_compare.update_xaxes(
                tickangle=-35,
            )

            st.plotly_chart(
                fig_compare,
                use_container_width=True,
            )

            st.caption(
                "Each measurement is scaled using its minimum and "
                "maximum numeric values across the complete dataset. "
                "A value near 0 is near that measurement's dataset "
                "minimum; a value near 1 is near its maximum. "
                "Approximate text values such as ~6 are not plotted "
                "as exact numbers, and missing values are not imputed. "
                "The connecting lines are a visual profile, not a "
                "physical trajectory or a causal relationship."
            )

            # Show which measurements could not be plotted
            # for either selected experiment.
            unavailable = []

            for column in measurement_columns:
                if (
                    column not in normalized_data.columns
                    or pd.isna(experiment_a_profile.get(column, float("nan")))
                    or pd.isna(experiment_b_profile.get(column, float("nan")))
                ):
                    unavailable.append(column)

            if unavailable:
                with st.expander(
                    "Measurements missing or unavailable in the graph"
                ):
                    st.write(
                        "These measurements could not be compared "
                        "numerically for both experiments:"
                    )
                    for column in unavailable:
                        st.write(f"- {column}")
       