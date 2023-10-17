# Copyright (c) Streamlit Inc. (2018-2022) Snowflake Inc. (2022)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import inspect
import textwrap
import numpy as np
import matplotlib.pyplot as plt
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.figure_factory as ff
import plotly.express as px
import gc
import streamlit as st

from constant import *

from streamlit_plotly_events import plotly_events

from dsymb import *

r = lambda: random.randint(50, 255)
DEFAULT_PLOTLY_COLORS = {
    str(i): "#%02X%02X%02X" % (r(), r(), r()) for i in range(25)
}


@st.cache_data(ttl=3600, max_entries=1, show_spinner=False)
def preprocess_data(uploaded_ts):
    with st.spinner("Preprocessing your data set..."):
        all_ts = []
        for ts in uploaded_ts:
            all_ts.append(np.genfromtxt(ts, delimiter=","))
    return all_ts
    gc.collect()


@st.cache_data(ttl=3600, max_entries=1, show_spinner=False)
def plot_matrix(D1, distance_name=""):
    return px.imshow(D1, aspect="auto", title=f"Distance matrix with {distance_name}")


@st.cache_data(ttl=3600, max_entries=3, show_spinner=False)
def plot_symbolization(df_temp, mode):
    tmp_df = df_temp
    tmp_df = tmp_df.rename(
        columns={
            "segment_start": "Start",
            "segment_end": "Finish",
            "signal_index": "Task",
        }
    )
    tmp_df["segment_symbol"] = tmp_df["segment_symbol"].apply(str)
    tmp_df["Task"] = tmp_df["Task"].apply(str)

    if mode == "Normalized":
        all_max_length = []
        for i in range(len(tmp_df)):
            sig_index = tmp_df["Task"].values[i]
            max_length = max(
                tmp_df.loc[tmp_df["Task"] == sig_index]["Finish"].values
            )
            all_max_length.append(max_length)
        tmp_df["max"] = all_max_length
        tmp_df["Start"] = tmp_df["Start"] / tmp_df["max"]
        tmp_df["Finish"] = tmp_df["Finish"] / tmp_df["max"]

    fig = ff.create_gantt(
        tmp_df,
        index_col="segment_symbol",
        bar_width=0.4,
        show_colorbar=True,
        group_tasks=True,
        colors={
            key: DEFAULT_PLOTLY_COLORS[key]
            for key in set(tmp_df["segment_symbol"].values)
        },
    )
    fig.update_layout(
        xaxis_type="linear",
        height=1000,
        title_text="All symbolic sequences in the data set",
        legend=dict(
        	title=dict(text="Symbol")
    	)
    )
    return fig


@st.cache_data(ttl=3600, max_entries=3, show_spinner=False)
def plot_symbol_distr(df_temp, mode):
    tmp_df = df_temp
    tmp_df = tmp_df.rename(
        columns={
            "segment_start": "Start",
            "segment_end": "Finish",
            "signal_index": "Task",
        }
    )
    tmp_df["segment_symbol"] = tmp_df["segment_symbol"].apply(str)
    tmp_df["Task"] = tmp_df["Task"].apply(str)

    all_max_length = []
    for i in range(len(tmp_df)):
        sig_index = tmp_df["Task"].values[i]
        max_length = max(
            tmp_df.loc[tmp_df["Task"] == sig_index]["Finish"].values
        )
        all_max_length.append(max_length)

    bin_size = 0.01 * max(all_max_length)

    if mode == "Normalized":
        bin_size = 0.01
        tmp_df["max"] = all_max_length
        tmp_df["Start"] = tmp_df["Start"] / tmp_df["max"]
        tmp_df["Finish"] = tmp_df["Finish"] / tmp_df["max"]

    n_symbols = len(set(tmp_df["segment_symbol"].values))

    fig = make_subplots(
        rows=len(list(set(tmp_df["segment_symbol"].values))),
        cols=1,
        shared_xaxes=True,
    )

    for i, symbol in enumerate(set(tmp_df["segment_symbol"].values)):
        pos_symb = 0.5 * np.array(
            tmp_df.loc[tmp_df["segment_symbol"] == symbol]["Finish"].values
            + tmp_df.loc[tmp_df["segment_symbol"] == symbol]["Start"].values
        )
        fig_symb = ff.create_distplot(
            [pos_symb],
            group_labels=["{}".format(symbol)],
            show_hist=True,
            colors=[DEFAULT_PLOTLY_COLORS[symbol]],
            bin_size=bin_size,
            show_curve=False,
            show_rug=False,
        )
        for trace in fig_symb.data:
            fig.add_trace(trace, row=1 + i, col=1)
    fig.update_layout(
        xaxis_type="linear",
        height=min(1000, 100 * n_symbols),
        title_text="Symbols' frequency over time",
        xaxis_title="Time stamp",
    	yaxis_title="Symbol",
        legend=dict(
        	title=dict(text="Symbol")
    	)
    )
    return fig


def plot_time_series(ts, tmp_df, dims=[0, 20]):
    # tmp_df = df_temp.copy()
    tmp_df = tmp_df.rename(
        columns={
            "segment_start": "Start",
            "segment_end": "Finish",
            "signal_index": "Task",
        }
    )
    tmp_df["segment_symbol"] = tmp_df["segment_symbol"].apply(str)
    tmp_df["Task"] = tmp_df["Task"].apply(str)
    fig_symb = ff.create_gantt(
        tmp_df,
        index_col="segment_symbol",
        bar_width=0.4,
        show_colorbar=True,
        group_tasks=True,
        colors={
            key: DEFAULT_PLOTLY_COLORS[key]
            for key in set(tmp_df["segment_symbol"].values)
        },
    )

    fig = make_subplots(rows=(dims[1] - dims[0]) + 1, cols=1, shared_xaxes=True)

    for trace in fig_symb.data:
        fig.add_trace(trace, row=1, col=1)

    for i_row, i in enumerate(range(dims[0], dims[1])):
        fig.add_trace(
            go.Scattergl(
                x=list(range(len(ts))),
                y=ts[:, i],
                mode="lines",
                line=dict(color="white", width=1),
            ),
            row=i_row + 2,
            col=1,
        )
    fig.update_layout(
        xaxis_type="linear",
        height=min(2000, (dims[1] - dims[0]) * 50),
        showlegend=False,
        xaxis_title="Time stamp",
    	yaxis_title="Dimension",
        title_text=(
            "Plot of your chosen multivariate time series<br> along with its"
            "univariate d_symb symbolic sequence (on top)"
		),
    )
    st.plotly_chart(fig, use_container_width=True)
    del fig, fig_symb
    gc.collect()


def get_data_step():
    uploaded_ts = st.file_uploader(
        "Upload your time series:", accept_multiple_files=True
    )
    # if len(uploaded_ts) == 1:
    #     st.markdown("Multiple time series should be provided.")
    if len(uploaded_ts) >= 1: # before: 2
        try:
            st.session_state.ALL_TS = preprocess_data(uploaded_ts)
        except Exception as e:
            st.error(
                "An error occured while processing the files. Please check if the time series have the correct format (n_timestamps, n_dims). The exception is the following: {}",
                icon="🚨",
            )


def Visualize_step():
    if len(st.session_state.ALL_TS) > 1:
        n_symbols = st.slider("Choose the number of symbols:", 0, 25, 5)
        D1, df_temp, lookup_table = dsym(st.session_state.ALL_TS, n_symbols)
        tab_indiv, tab_all = st.tabs(["Single time series", "Data set of time series"])
        with tab_indiv:
            time_series_selected = st.selectbox(
                "Choose the index of a single time series :", list(range(len(st.session_state.ALL_TS)))
            )
            range_dims = [
                [20 * dim_s, 20 * (dim_s + 1)]
                for dim_s in range(
                    len(st.session_state.ALL_TS[time_series_selected][0]) // 20
                )
            ]
            if range_dims[-1][1] < len(
                st.session_state.ALL_TS[time_series_selected][0]
            ):
                range_dims += [
                    [
                        range_dims[-1][1],
                        len(st.session_state.ALL_TS[time_series_selected][0]),
                    ]
                ]
            range_dims += [
                [0, len(st.session_state.ALL_TS[time_series_selected][0])]
            ]
            dims = st.selectbox("Choose the dimensions' range:", range_dims)
            plot_time_series(
                st.session_state.ALL_TS[time_series_selected],
                df_temp.loc[df_temp["signal_index"] == time_series_selected],
                dims,
            )

        with tab_all:
            mode = st.radio(
                "Mode",
                ["Colorbars' list", "Distance matrix"],
                captions=[
                    "Visualize all the symbolized time series.",
                    "Visualize the distance matrix based on d_symb.",
                ],
                horizontal=True,
            )
            if mode == "Colorbars' list":
                mode_length = st.radio(
                    "Length",
                    ["True", "Normalized"],
                    captions=[
                        "Use the true time series' lengths.",
                        "Normalize the lengths between 0 and 1.",
                    ],
                    horizontal=True,
                )

                fig = plot_symbolization(df_temp, mode=mode_length)
                st.plotly_chart(fig, use_container_width=True)
                fig_dist = plot_symbol_distr(df_temp, mode=mode_length)
                st.plotly_chart(fig_dist, use_container_width=True)
            elif mode == "Distance matrix":
                fig = plot_matrix(D1, distance_name="d_symb")
                st.plotly_chart(fig, use_container_width=True)


def run_explore_frame():
    st.markdown("## Explore your data set.")
    st.markdown(
        "Upload your data set of (multivariate) time series, each time series must be in a `.csv`"
        " file with the shape `(n_timestamps, n_dim)`."
        " Then, select the number of symbols to represent your time series."
    )

    get_data_step()

    Visualize_step()

    gc.collect()


def run_compare_frame():
    st.markdown(compare_text_1)

    tab_data_desc, tab_basesline_desc = st.tabs(
        ["Data set description", "Baselines description"]
    )

    with tab_data_desc:
        st.markdown(data_JIGSAW)

    with tab_basesline_desc:
        st.markdown(Baseline_desc)

    st.markdown(compare_text_2)

    df_exectime = pd.read_csv("data/eval/exectime.csv", index_col=0)
    df_acc = pd.read_csv("data/eval/accuracy.csv", index_col=0)
    d_replace_eval = {
        "rand_score":"Rand score",
        "Adjusted_rand_score":"Ajusted rand score",
        "Adjusted_Mutual_Information":"Adjusted mutual information",
        "Normalized_Multual_Information":"Normalized mutual information",
        "homogeneity":"Homogeneity",
        "Completeness":"Completeness",
        "V_measure":"V-measure",
        "Fowlkes_Mallows":"Fowlkes-Mallows index",
    }
    d_replace_distance = {
		"dtw_dep":"DTW dependent",
        "ddtw_dep":"DDTW dependent",
        "wdtw_dep":"WDTW dependent",
        "wddtw_dep":"WDDTW dependent",
        "msm":"MSM",
        "twe":"TWE",
        "lcss":"LCSS",
        "erp":"ERP",
        "edr":"EDR",
        "dsymb":"d_symb",
	}
    d_replace_distance_inv = dict()
    for key, value in d_replace_distance.items():
        d_replace_distance_inv[value] = key
    list_distances = [d_replace_distance[dist_abb] for dist_abb in df_acc.columns]

    # measure = st.selectbox('choose Evaluation Measures', list(df_acc.index))
    dist_name = st.selectbox("Choose a distance measure:", list_distances)
    dist_abb = d_replace_distance_inv[dist_name]

    fig_mat = plot_matrix(
        pd.read_csv(
            "data/simMatrix/{}_DistanceMatrix.csv".format(dist_abb), index_col=0
        ).to_numpy(),
        distance_name=dist_name
    )

    st.plotly_chart(fig_mat, use_container_width=True)

    st.markdown("#### Explore the clustering performances.")
	
    fig_time = px.bar(
        df_exectime.T.rename(columns=d_replace_distance).T,
        labels={"distance":"distance measure", "value":"execution time"},
    )
    fig_time.update_yaxes(
        type="log",
    )
    fig_time.update_layout(
    	xaxis_title="Distance measure",
        yaxis_title="Clustering execution time (in seconds)",
        showlegend=False,
	)
    st.plotly_chart(fig_time, use_container_width=True)

	
    fig_acc = px.bar(
        df_acc.rename(columns=d_replace_distance).T.rename(columns=d_replace_eval),
        barmode="group",
    )
    fig_acc.update_layout(
		xaxis_title="Distance measure",
        yaxis_title="Clustering performance evaluation",
        legend=dict(
        	title=dict(text="Evaluation metric")
    	)
	)
    st.plotly_chart(fig_acc, use_container_width=True)


def run_about_frame():
    st.markdown(about_text)
