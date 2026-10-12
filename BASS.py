from pathlib import Path

import pandas as pd
import streamlit as st


# --------------------------------------------------
# 1. PAGE SETUP
# --------------------------------------------------

st.set_page_config(
    page_title="Flame.ai | BASS Explorer",
    page_icon="🔥",
    layout="wide",
)

PROJECT_DIR = Path(__file__).resolve().parent
RAW_DATA_DIR = PROJECT_DIR / "raw_2"
DATA_FILE = RAW_DATA_DIR / "bass.csv"

EXPECTED_ROWS = 129
EXPECTED_COLUMNS = 17

# Keep the original NASA column names exactly as they appear in bass.csv.
PI_COLUMN = "PI"
TEST_COLUMN = "Test #"
O2_COLUMN = "Calibrated  initial O2 % by vol "
CO2_COLUMN = "Initial CO2 % by vol"
CO_COLUMN = "Initial CO (ppm)"

REQUIRED_COLUMNS = [
    "PI",
    "Test #",
    "Date",
    "GMT",
    "Sample #",
    "Fuel Sample Material",
    "Flow restrictor",
    "Fan display",
    "Air display",
    "Radiometer gain   (1000   250   50   10)",
    "Total Frames Shot",
    "Calibrated  initial O2 % by vol ",
    "Calibrated final O2 % by vol",
    "Initial CO2 % by vol",
    "Final CO2 % by vol",
    "Initial CO (ppm)",
    "Final CO (ppm)",
]


# --------------------------------------------------
# 2. LOAD THE ORIGINAL DATA
# --------------------------------------------------

@st.cache_data
def load_bass_data(file_path: str) -> pd.DataFrame:
    """Load the source CSV without cleaning or changing its values."""
    return pd.read_csv(file_path, encoding="utf-8-sig")


try:
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Could not find bass.csv at {DATA_FILE}. "
            "Place the original file in data/raw/."
        )

    df = load_bass_data(str(DATA_FILE))

except (FileNotFoundError, UnicodeDecodeError, pd.errors.ParserError, OSError) as error:
    st.error(str(error))
    st.stop()


# --------------------------------------------------
# 3. VALIDATE THE DATASET
# --------------------------------------------------

missing_columns = [
    column for column in REQUIRED_COLUMNS if column not in df.columns
]

if missing_columns:
    st.error(
        "The CSV is missing expected columns: "
        + ", ".join(repr(column) for column in missing_columns)
    )
    st.write("Columns found in the CSV:")
    st.write([repr(column) for column in df.columns.tolist()])
    st.stop()

if len(df) == EXPECTED_ROWS and len(df.columns) == EXPECTED_COLUMNS:
    dataset_status = f"Dataset loaded: all {EXPECTED_ROWS} experiments are available."
else:
    dataset_status = (
        f"Expected {EXPECTED_ROWS} experiments and {EXPECTED_COLUMNS} columns; "
        f"loaded {len(df)} experiments and {len(df.columns)} columns. "
        "Check the source CSV."
    )


# --------------------------------------------------
# 4. HELPER FUNCTIONS
# --------------------------------------------------

def numeric_filter(data, column, label, unit, key):
    """
    Filter a numeric column using a temporary numeric conversion.

    Missing or non-numeric values remain included by default, so an
    unusual recorded value does not cause its experiment to disappear.
    The original DataFrame is never modified.
    """
    numeric_values = pd.to_numeric(data[column], errors="coerce")
    valid_values = numeric_values.dropna()

    st.sidebar.markdown(f"**{label}**")

    if valid_values.empty:
        st.sidebar.caption(f"No numeric values available for {label}.")
        return pd.Series(True, index=data.index)

    minimum = float(valid_values.min())
    maximum = float(valid_values.max())

    if minimum == maximum:
        st.sidebar.caption(f"Only one numeric value: {minimum:g} {unit}")
        return pd.Series(True, index=data.index)

    selected_range = st.sidebar.slider(
        label,
        min_value=minimum,
        max_value=maximum,
        value=(minimum, maximum),
        key=key,
        help=f"Filter by {label.lower()}. Values are displayed in {unit}.",
    )

    low, high = selected_range
    numeric_mask = numeric_values.between(low, high)

    # Keep records with missing or text values, matching the FLEX pattern.
    unavailable_mask = numeric_values.isna()
    return numeric_mask | unavailable_mask


def display_value(value):
    """Show missing values clearly without changing the source data."""
    if pd.isna(value):
        return "Not recorded"
    return str(value)


# --------------------------------------------------
# 5. DASHBOARD HEADER
# --------------------------------------------------

st.title("🔥 Flame.ai")
st.subheader("BASS Experiment Explorer")

st.write(
    "Search, filter, and explore NASA BASS "
    "solid-fuel combustion experiments."
)

if len(df) == EXPECTED_ROWS and len(df.columns) == EXPECTED_COLUMNS:
    st.success(dataset_status)
else:
    st.warning(dataset_status)


# --------------------------------------------------
# 6. SIDEBAR: SEARCH AND FILTERS
# --------------------------------------------------

st.sidebar.title("Experiment Explorer")
st.sidebar.caption("Filters apply to the displayed results.")

# Search by Test #, using partial text matching.
search_query = st.sidebar.text_input(
    "Search by Test #",
    placeholder="e.g. 101",
)

st.sidebar.divider()
st.sidebar.subheader("Categorical filter")

pi_values = (
    df[PI_COLUMN]
    .dropna()
    .astype(str)
    .unique()
    .tolist()
)
pi_options = ["All scientists"] + sorted(pi_values)

selected_pi = st.sidebar.selectbox(
    "Principal Investigator (PI)",
    options=pi_options,
    index=0,
    key="filter_pi",
)

st.sidebar.divider()
st.sidebar.subheader("Numerical filters")

o2_mask = numeric_filter(
    df,
    O2_COLUMN,
    "Initial oxygen concentration (%)",
    "%",
    "filter_initial_o2",
)

co2_mask = numeric_filter(
    df,
    CO2_COLUMN,
    "Initial carbon dioxide concentration (%)",
    "%",
    "filter_initial_co2",
)

co_mask = numeric_filter(
    df,
    CO_COLUMN,
    "Initial carbon monoxide concentration (ppm)",
    "ppm",
    "filter_initial_co",
)


# --------------------------------------------------
# 7. COMBINE SEARCH AND FILTERS
# --------------------------------------------------

# Search Test # without changing its original stored values.
if search_query.strip():
    query = search_query.strip().casefold()
    search_mask = (
        df[TEST_COLUMN]
        .astype("string")
        .str.casefold()
        .str.contains(query, na=False, regex=False)
    )
else:
    search_mask = pd.Series(True, index=df.index)

# PI dropdown: "All scientists" means no PI restriction.
if selected_pi == "All scientists":
    pi_mask = pd.Series(True, index=df.index)
else:
    pi_mask = df[PI_COLUMN].astype("string").eq(selected_pi).fillna(False)

# All active conditions must match, just like the FLEX dashboard.
combined_mask = search_mask & pi_mask & o2_mask & co2_mask & co_mask

# Filtered copy for display; df itself remains unchanged.
filtered_df = df.loc[combined_mask].copy()


# --------------------------------------------------
# 8. RESULT SUMMARY
# --------------------------------------------------

st.divider()
st.subheader("Experiment search results")

col1, col2, col3 = st.columns(3)

col1.metric("Total source experiments", len(df))
col2.metric("Matching experiments", len(filtered_df))
col3.metric("Experiments not shown", len(df) - len(filtered_df))

st.caption(
    "Numerical filters use temporary numeric conversions. "
    "Original recorded values, including text and missing values, "
    "are preserved in the source dataset and displayed results."
)


# --------------------------------------------------
# 9. DISPLAY MATCHING EXPERIMENTS
# --------------------------------------------------

st.divider()
st.subheader("Matching experiment records")

if filtered_df.empty:
    st.info(
        "No experiments match the current search and filters. "
        "Try a different Test # or widen the numerical ranges."
    )
else:
    # Display all original columns and recorded values.
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
# 10. MILESTONE 3: INDIVIDUAL EXPERIMENT DETAILS
# --------------------------------------------------

st.divider()
st.subheader("Explore an individual experiment")
st.write(
    "Choose any experiment from the current search results to inspect its "
    "recorded details. The values below come directly from the original CSV."
)

if filtered_df.empty:
    st.info("An individual experiment can be explored once your filters return results.")
else:
    # Use the filtered results so the detail selector respects the current filters.
    # Test # values are displayed as text, preserving their original formatting.
    available_tests = filtered_df[TEST_COLUMN].astype(str).tolist()

    selected_test = st.selectbox(
        "Select a BASS experiment (Test #)",
        options=available_tests,
        key="detail_test_number",
    )

    selected_rows = filtered_df.loc[
        filtered_df[TEST_COLUMN].astype(str).eq(selected_test)
    ]

    if selected_rows.empty:
        st.warning("That experiment is no longer available in the current results.")
    else:
        # Test # is expected to be unique in this source. If duplicates ever
        # appear, show each matching source row rather than silently discarding one.
        for row_number, (_, experiment) in enumerate(selected_rows.iterrows(), start=1):
            if len(selected_rows) > 1:
                st.markdown(f"#### Matching source record {row_number}")

            st.markdown(f"### BASS Test #{display_value(experiment[TEST_COLUMN])}")

            # A few useful, directly recorded facts at the top, like the FLEX dashboard.
            metric1, metric2, metric3, metric4 = st.columns(4)
            metric1.metric("Principal investigator", display_value(experiment["PI"]))
            metric2.metric("Test date", display_value(experiment["Date"]))
            metric3.metric("Fuel material", display_value(experiment["Fuel Sample Material"]))
            metric4.metric("Sample #", display_value(experiment["Sample #"]))

            # Organize the source columns into readable groups. No source values
            # are normalized, inferred, or overwritten.
            detail_groups = {
                "Experiment identification": [
                    "PI",
                    "Test #",
                    "Date",
                    "GMT",
                    "Sample #",
                    "Fuel Sample Material",
                ],
                "Combustion environment and gas measurements": [
                    "Calibrated  initial O2 % by vol ",
                    "Calibrated final O2 % by vol",
                    "Initial CO2 % by vol",
                    "Final CO2 % by vol",
                    "Initial CO (ppm)",
                    "Final CO (ppm)",
                ],
                "Equipment and experiment settings": [
                    "Flow restrictor",
                    "Fan display",
                    "Air display",
                    "Radiometer gain   (1000   250   50   10)",
                    "Total Frames Shot",
                ],
            }

            for group_title, columns_in_group in detail_groups.items():
                with st.expander(group_title, expanded=(group_title == "Experiment identification")):
                    left, right = st.columns(2)
                    for index, column_name in enumerate(columns_in_group):
                        target_column = left if index % 2 == 0 else right
                        with target_column:
                            st.markdown(f"**{column_name.strip()}**")
                            st.write(display_value(experiment[column_name]))

            st.caption(
                "‘Not recorded’ means the original CSV has a missing value for that field. "
                "Other text entries are shown as recorded; they are not treated as errors."
            )


# --------------------------------------------------
# 11. MILESTONE 4: COMPARE TWO EXPERIMENTS
# --------------------------------------------------

import plotly.graph_objects as go

st.divider()
st.subheader("Compare Two BASS Experiments")
st.write(
    "Compare recorded measurements from any two experiments in the original "
    "dataset. These selectors are independent of the search and sidebar filters."
)

if len(df) < 2:
    st.info(
        "At least two experiments are needed for comparison. "
        f"The original dataset currently contains {len(df)} experiment(s)."
    )
else:
    # Use source-row positions as selector values. This keeps each record
    # distinct even if multiple records share the same Test #.
    def comparison_label(row_position):
        experiment = df.iloc[row_position]
        return (
            f"Test #{display_value(experiment[TEST_COLUMN])} — "
            f"{display_value(experiment[PI_COLUMN])} — "
            f"{display_value(experiment['Fuel Sample Material'])} "
            f"(source record {row_position + 1})"
        )

    selector_a, selector_b = st.columns(2)

    with selector_a:
        experiment_a_position = st.selectbox(
            "First experiment (Experiment A)",
            options=list(range(len(df))),
            index=0,
            format_func=comparison_label,
            key="compare_experiment_a",
        )

    # Start with a different record selected by default. The user can still
    # choose any record; selecting the same record is handled below.
    default_b_position = 1 if len(df) > 1 else 0
    with selector_b:
        experiment_b_position = st.selectbox(
            "Second experiment (Experiment B)",
            options=list(range(len(df))),
            index=default_b_position,
            format_func=comparison_label,
            key="compare_experiment_b",
        )

    if experiment_a_position == experiment_b_position:
        st.warning(
            "Please select two different source records. "
            "Experiment A and Experiment B currently refer to the same record."
        )
    else:
        experiment_a = df.iloc[experiment_a_position]
        experiment_b = df.iloc[experiment_b_position]

        st.markdown("#### Selected experiment summaries")
        summary_a, summary_b = st.columns(2)

        summary_fields = [
            ("Test #", TEST_COLUMN),
            ("PI", PI_COLUMN),
            ("Date", "Date"),
            ("Fuel Sample Material", "Fuel Sample Material"),
        ]

        with summary_a:
            st.markdown("**Experiment A**")
            for field_label, column_name in summary_fields:
                st.markdown(f"**{field_label}:** {display_value(experiment_a[column_name])}")

        with summary_b:
            st.markdown("**Experiment B**")
            for field_label, column_name in summary_fields:
                st.markdown(f"**{field_label}:** {display_value(experiment_b[column_name])}")

        # Each chart compares one measurement from the two source records.
        # Numeric conversion is temporary: the original values are untouched.
        comparison_parameters = [
            (
                "Initial oxygen concentration",
                "Calibrated  initial O2 % by vol ",
                "%",
            ),
            (
                "Final oxygen concentration",
                "Calibrated final O2 % by vol",
                "%",
            ),
            (
                "Initial carbon dioxide concentration",
                "Initial CO2 % by vol",
                "%",
            ),
            (
                "Final carbon dioxide concentration",
                "Final CO2 % by vol",
                "%",
            ),
            (
                "Initial carbon monoxide concentration",
                "Initial CO (ppm)",
                "ppm",
            ),
            (
                "Final carbon monoxide concentration",
                "Final CO (ppm)",
                "ppm",
            ),
            (
                "Total frames shot",
                "Total Frames Shot",
                "frames",
            ),
        ]

        st.markdown("#### Measurement comparisons")
        st.caption(
            "Each chart uses the recorded numeric values only. Missing or text "
            "values are not replaced with zero or estimated."
        )

        chart_columns = st.columns(2)

        for parameter_index, (chart_title, source_column, unit) in enumerate(
            comparison_parameters
        ):
            # Convert only the two values being plotted. errors='coerce'
            # turns non-numeric text into NaN for plotting without changing df.
            raw_value_a = experiment_a[source_column]
            raw_value_b = experiment_b[source_column]
            numeric_value_a = pd.to_numeric(
                pd.Series([raw_value_a]), errors="coerce"
            ).iloc[0]
            numeric_value_b = pd.to_numeric(
                pd.Series([raw_value_b]), errors="coerce"
            ).iloc[0]

            with chart_columns[parameter_index % 2]:
                if pd.isna(numeric_value_a) or pd.isna(numeric_value_b):
                    st.markdown(f"**{chart_title}**")
                    st.info(
                        "A grouped bar chart cannot be shown because at least "
                        "one experiment has a missing or non-numeric value."
                    )
                    st.write(
                        {
                            "Experiment A — Test #"
                            + display_value(experiment_a[TEST_COLUMN]): display_value(raw_value_a),
                            "Experiment B — Test #"
                            + display_value(experiment_b[TEST_COLUMN]): display_value(raw_value_b),
                        }
                    )
                else:
                    labels = [
                        f"Experiment A — Test #{display_value(experiment_a[TEST_COLUMN])}",
                        f"Experiment B — Test #{display_value(experiment_b[TEST_COLUMN])}",
                    ]
                    values = [float(numeric_value_a), float(numeric_value_b)]

                    figure = go.Figure(
                        data=[
                            go.Bar(
                                x=labels,
                                y=values,
                                text=[f"{value:g}" for value in values],
                                textposition="auto",
                                hovertemplate=(
                                    "%{x}<br>Value: %{y:g} " + unit + "<extra></extra>"
                                ),
                            )
                        ]
                    )
                    figure.update_layout(
                        title=chart_title,
                        yaxis_title=f"Value ({unit})",
                        xaxis_title="Selected experiment",
                        template="plotly_white",
                        showlegend=False,
                        margin=dict(l=20, r=20, t=60, b=70),
                        height=350,
                    )
                    figure.update_xaxes(tickangle=-15)
                    st.plotly_chart(
                        figure,
                        use_container_width=True,
                        key=f"comparison_chart_{parameter_index}",
                    )

        st.caption(
            "Source records are identified by their row positions in the original "
            "dataset, so duplicate Test # values remain selectable and are not merged."
        )
