# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from datetime import date, datetime, timedelta

import dash_bootstrap_components as dbc
import dash_dangerously_set_inner_html
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from dash import Input, Output, dash_table, dcc, html
from flask import Markup

from ..models.score import Score


########################### Models #####################################
def request_data(project=None, branch=None, size=None, board=None):
    default_jenkins_project = "HW_tests/HW_test_multiconfig"
    default_branch = "boot_partition_master"
    default_size = 2
    jenkins_project = project if project else default_jenkins_project
    size = size if size else default_size
    board = board if board else None
    branch = branch if branch else default_branch
    deprecated = []
    sc = Score(
        jenkins_project=jenkins_project,
        size=int(size),
        branch=branch,
        board=board,
        deprecated=deprecated,
    )
    return sc.to_dict()

    # request_raw = 'http://localhost:5000/constellation/api/sc?'
    # if project:
    #     request_raw += 'jenkins_project={}'.format(project)
    # if branch:
    #     request_raw += '&branch={}'.format(branch)
    # if size:
    #     request_raw += '&size={}'.format(size)
    # if board:
    #     request_raw += '&board={}'.format(board)

    # response = requests.get(request_raw)
    # if response.status_code == 200:
    #     return response.json()
    # else:
    #     print("Query Failed!")


def get_df_booted(data):
    # create time-series based data frame
    data_dict = {
        "total": [],
        "logs_missing": [],
        "boards": [],
        "booted": [],
        "not_booted": [],
        "linux_prompt_not_reached": [],
        "uboot_not_reached": [],
        "drivers_enumerated": [],
        "drivers_missing": [],
        "dmesg_warnings_found": [],
        "dmesg_errors_found": [],
        "pytest_errors": [],
        "pytest_failures": [],
        "pytest_skipped": [],
        "pytest_tests": [],
    }
    index_set = []
    builds = [build for build in data["builds"].keys()]
    sd = datetime.strptime(
        data["builds"][builds[-1]]["jenkins_job_date"].split("T")[0], "%Y-%m-%d"
    )
    ed = datetime.strptime(
        data["builds"][builds[0]]["jenkins_job_date"].split("T")[0], "%Y-%m-%d"
    )
    drs = [sd + timedelta(days=x) for x in range((ed - sd).days + 1)]
    for dr in drs:
        found = False
        for build, build_data in data["builds"].items():
            dr_string = dr.strftime("%Y-%m-%d")
            build_data_d = build_data["jenkins_job_date"].split("T")[0]
            build_data_summary = data["summaries"][build]
            regression_data_summary = data["regressions"][build]
            if build_data_d == dr_string:
                index_set.append((dr, build, build_data["jenkins_trigger"]))
                # index_set.append(dr)
                data_dict["total"].append(len(data["boards"]))
                for k in data_dict:
                    if k in ["total"]:
                        continue
                    elif k in ["logs_missing"]:
                        data_dict[k].append(
                            len(regression_data_summary["regress_missing_logs"])
                        )
                        continue
                    data_dict[k].append(int(build_data_summary[k]["count"]))
                found = True
        if not found:
            index_set.append((dr, "NA", "NA"))
            # index_set.append(dr)
            for k in data_dict:
                data_dict[k].append(0)

    df = pd.DataFrame(
        data_dict,
        # index = pd.to_datetime(index_set)
        index=pd.MultiIndex.from_tuples(index_set, names=["date", "build", "trigger"]),
    )
    return df


def get_fig_logs(data):
    df = get_df_booted(data)
    df_index_ts = [index_ts[0] for index_ts in df.index.tolist()]
    # df_index_build = [index_ts[1] for index_ts in df.index.tolist()]
    # missing = df.loc[:, "boards"]
    fig = go.Figure(
        data=[
            go.Bar(
                name="Logs",
                x=df_index_ts,
                y=df.loc[:, "boards"].values.tolist(),
                text=df.loc[:, "boards"].values.tolist(),
            ),
            go.Bar(
                name="Missing Logs",
                x=df_index_ts,
                y=df.loc[:, "logs_missing"].values.tolist(),
                text=df.loc[:, "logs_missing"].values.tolist(),
            ),
        ]
    )
    fig.update_layout(barmode="stack", title="Boot Logs Turnout")
    return fig


def get_fig_booted(data):
    df = get_df_booted(data)
    df_index_ts = [index_ts[0] for index_ts in df.index.tolist()]
    # df_index_build = [index_ts[1] for index_ts in df.index.tolist()]
    fig = go.Figure(
        data=[
            go.Bar(
                name="Booted",
                x=df_index_ts,
                y=df.loc[:, "booted"].values.tolist(),
                text=df.loc[:, "booted"].values.tolist(),
            ),
            go.Bar(
                name="Linux Not Reached",
                x=df_index_ts,
                y=df.loc[:, "linux_prompt_not_reached"].values.tolist(),
                text=df.loc[:, "linux_prompt_not_reached"].values.tolist(),
            ),
            go.Bar(
                name="U-boot Not Reached",
                x=df_index_ts,
                y=df.loc[:, "uboot_not_reached"].values.tolist(),
                text=df.loc[:, "uboot_not_reached"].values.tolist(),
            ),
        ]
    )
    fig.update_layout(barmode="stack", title="Boot Histogram")
    return fig


def get_fig_linux(data):
    df = get_df_booted(data)
    df_index_ts = [index_ts[0] for index_ts in df.index.tolist()]
    # df_index_build = [index_ts[1] for index_ts in df.index.tolist()]
    fig = go.Figure(
        data=[
            go.Bar(
                name="IIO Devices Found",
                x=df_index_ts,
                y=df.loc[:, "drivers_enumerated"].values.tolist(),
                text=df.loc[:, "drivers_enumerated"].values.tolist(),
            ),
            go.Bar(
                name="IIO Devices not Found",
                x=df_index_ts,
                y=df.loc[:, "drivers_missing"].values.tolist(),
                text=df.loc[:, "drivers_missing"].values.tolist(),
            ),
        ]
    )
    fig.update_layout(barmode="stack", title="IIO Devices")
    return fig


def get_fig_dmesg(data):
    df = get_df_booted(data)
    df_index_ts = [index_ts[0] for index_ts in df.index.tolist()]
    # df_index_build = [index_ts[1] for index_ts in df.index.tolist()]
    fig = go.Figure(
        data=[
            go.Bar(
                name="Dmesg Warnings Found",
                x=df_index_ts,
                y=df.loc[:, "dmesg_warnings_found"].values.tolist(),
                text=df.loc[:, "dmesg_warnings_found"].values.tolist(),
            ),
            go.Bar(
                name="Dmesg Errors Found",
                x=df_index_ts,
                y=df.loc[:, "dmesg_errors_found"].values.tolist(),
                text=df.loc[:, "dmesg_errors_found"].values.tolist(),
            ),
        ]
    )
    fig.update_layout(barmode="stack", title="DMESG Errors")
    return fig


def get_fig_pyadi(data):
    df = get_df_booted(data)
    df_index_ts = [index_ts[0] for index_ts in df.index.tolist()]
    # df_index_build = [index_ts[1] for index_ts in df.index.tolist()]
    pytest_fails = (
        df.loc[:, "pytest_failures"]
        + df.loc[:, "pytest_skipped"]
        + df.loc[:, "pytest_errors"]
    )

    pytest_passed = df.loc[:, "pytest_tests"] - pytest_fails

    fig = go.Figure(
        data=[
            go.Bar(
                name="PYADI-IIO Tests Passed",
                x=df_index_ts,
                y=pytest_passed.values.tolist(),
                text=pytest_passed.values.tolist(),
            ),
            go.Bar(
                name="PYADI-IIO Tests Failures",
                x=df_index_ts,
                y=df.loc[:, "pytest_failures"].values.tolist(),
                text=df.loc[:, "pytest_failures"].values.tolist(),
            ),
            go.Bar(
                name="PYADI-IIO Tests Skipped",
                x=df_index_ts,
                y=df.loc[:, "pytest_skipped"].values.tolist(),
                text=df.loc[:, "pytest_skipped"].values.tolist(),
            ),
        ]
    )
    fig.update_layout(barmode="stack", title="PYADI-IIO Tests")
    return fig


########################### Generators #####################################


def generate_logo():
    logo_path = "app/static/sdg.svg"
    svg = open(logo_path).read()
    sc_logo_div = html.Div(
        children=[
            dash_dangerously_set_inner_html.DangerouslySetInnerHTML(Markup(svg)),
            html.H5("Score Card Generator"),
        ],
        id="sc_logo_div",
        className="container",
        style={"margin-top": "2%", "margin-bottom": "2%"},
    )
    return sc_logo_div


def generate_options(data):

    options_div = html.Div(
        children=[
            html.Div("Filters", id="sc_filters_header", className="display-6"),
            html.H5("Project"),
            dcc.Input(
                id="sc_project_options",
                type="text",
                placeholder="Jenkins project name",
                value="HW_tests/HW_test_multiconfig",
                style={"width": "100%"},
            ),
            html.H5("Branch"),
            dcc.Dropdown(
                options=[
                    {
                        "label": "Boot Partition Master",
                        "value": "boot_partition_master",
                    },
                    {
                        "label": "Boot Partition Release",
                        "value": "boot_partition_release",
                    },
                    {"label": "HDL & Linux Master", "value": "hdl_master_linux_master"},
                    {
                        "label": "HDL & Linux Release",
                        "value": "hdl_release_linux_release",
                    },
                ],
                placeholder="Select target branch",
                value="boot_partition_master",
                id="sc_branch_options",
                style={"width": "100%"},
            ),
            html.H5("Size"),
            dcc.Input(
                id="sc_size_options",
                type="number",
                min=1,
                max=10,
                placeholder="No. of builds to Analyze",
                value=7,
                style={"width": "100%"},
            ),
            html.H5("Board"),
            dcc.Dropdown(
                options=[{"label": board, "value": board} for board in data["boards"]],
                placeholder="Select target board",
                id="sc_board_options",
                style={"width": "100%"},
            ),
        ],
        id="sc_filters_div",
        className="col-5",
        style={"margin-top": "2%"},
    )

    sc_filters_row = html.Div(
        children=[options_div], id="sc_filters_row", className="row"
    )

    sc_filters_container = html.Div(
        children=[sc_filters_row], id="sc_filters_container", className="container"
    )

    return sc_filters_container


def generate_dash_table(data, target, groupby="item"):

    latest_build = list(data["builds"].keys())[0]
    label = " ".join([ele.title() for ele in target.split("_")])

    # groupby config
    table_cols = {"item": label, "board": "Board", "build": "Build"}
    if groupby == "board":
        table_cols = {"board": "Board", "item": label, "build": "Build"}

    # unpack data
    data_raw = []
    for build, build_data in data["summaries"].items():
        for item, boards in build_data[target]["data"].items():
            for board in boards:
                data_raw.append([build, item, board])

    # convert data into data frame
    df = pd.DataFrame(data_raw, columns=["build", "item", "board"])

    # group data by item
    data_processed = []
    for fname, fdata in df.groupby(by=groupby):
        fields = [k for k in table_cols.keys()]
        data_processed.append(
            {
                fields[0]: fname,
                fields[1]: "\n".join(fdata[fields[1]].tolist()),
                fields[2]: "\n".join(
                    [
                        f"{build} (L)" if build == latest_build else build
                        for build in fdata[fields[2]].tolist()
                    ]
                ),
            }
        )

    # generate dash table
    cols = [{"name": _label, "id": _id} for _id, _label in table_cols.items()]
    dt = dash_table.DataTable(
        style_data={"whiteSpace": "pre-line", "height": "auto"},
        style_cell={"textAlign": "left", "vertical-align": "top"},
        style_header={
            "backgroundColor": "#D3D3D3",
            "color": "black",
        },
        data=data_processed,
        columns=cols,
    )
    return dt


def generate_top_boot_failing(data):
    top_boot_failing_div = html.Div(
        children=[
            dbc.Tabs(
                [
                    dbc.Tab(
                        dbc.Col(
                            dcc.Graph(
                                id="g_boot_test_summary", figure=get_fig_booted(data)
                            ),
                            width=6,
                        ),
                        label="Trends",
                        className="active",
                    ),
                    dbc.Tab(
                        generate_dash_table(data, "not_booted", "board"),
                        label="Failing Boards (Non Booting)",
                    ),
                    dbc.Tab(generate_dash_table(data, "not_booted"), label="Failures"),
                ]
            )
        ],
        id="top_boot_failing_div",
    )
    return top_boot_failing_div


def generate_drivers_enumeration(data):
    drivers_enumeration_div = html.Div(
        children=[
            dbc.Tabs(
                [
                    dbc.Tab(
                        dbc.Col(
                            dcc.Graph(
                                id="g_linux_test_summary", figure=get_fig_linux(data)
                            ),
                            width=6,
                        ),
                        label="Trends",
                        className="active",
                    ),
                    dbc.Tab(
                        generate_dash_table(data, "drivers_missing", "board"),
                        label="Failing Boards (Failed Device Enumeration)",
                    ),
                    dbc.Tab(
                        generate_dash_table(data, "drivers_missing"),
                        label="Missing Drivers",
                    ),
                ]
            )
        ],
        id="drivers_enumeration_div",
    )

    return drivers_enumeration_div


def generate_dmesg_errors(data):
    dmesg_errors_div = html.Div(
        children=[
            dbc.Tabs(
                [
                    dbc.Tab(
                        dbc.Col(
                            dcc.Graph(
                                id="g_linux_dmesg_summary", figure=get_fig_dmesg(data)
                            ),
                            width=6,
                        ),
                        label="Trends",
                        className="active",
                    ),
                    dbc.Tab(
                        generate_dash_table(data, "dmesg_errors_found", "board"),
                        label="Failing Boards (Dmesg Errors)",
                    ),
                    dbc.Tab(
                        generate_dash_table(data, "dmesg_errors_found"),
                        label="Dmeg Errors",
                    ),
                ]
            )
        ],
        id="dmesg_errors_div",
    )
    return dmesg_errors_div


def generate_pytest_results(data):

    pyadi_test_div = html.Div(
        children=[
            dbc.Tabs(
                [
                    dbc.Tab(
                        dbc.Col(
                            dcc.Graph(id="g_pyadi_test", figure=get_fig_pyadi(data)),
                            width=6,
                        ),
                        label="Trends",
                        className="active",
                    ),
                    dbc.Tab(
                        generate_dash_table(data, "pytest_failures", "board"),
                        label="PyADI IIO Failures",
                    ),
                    dbc.Tab(
                        generate_dash_table(data, "pytest_errors", "board"),
                        label="PyADI IIO Errors",
                    ),
                    dbc.Tab(
                        generate_dash_table(data, "pytest_skipped", "board"),
                        label="PyADI IIO Skipped",
                    ),
                ]
            )
        ],
        id="pyadi_test_div",
    )
    return pyadi_test_div


def generate_at_glance(data):
    sc_at_glance_div = html.Ul(
        children=[
            html.Li("Summary", className="list-group-item display-6"),
            html.Li(
                "Jenkins Project: {}".format(data["jenkins_project"]),
                className="list-group-item",
            ),
            html.Li("Branch: {}".format(data["branch"]), className="list-group-item"),
            html.Li(
                "Builds Analyzed ({}):\n {}".format(
                    len(data["builds"]), ",".join([build for build in data["builds"]])
                ),
                className="list-group-item",
                style={"whiteSpace": "pre-line"},
            ),
            html.Li(
                "Boards Tested ({}):\n {}".format(
                    len(data["boards"]), "\n".join([build for build in data["boards"]])
                ),
                className="list-group-item",
                style={"whiteSpace": "pre-line"},
            ),
        ],
        id="sc_at_glance_div",
        className="list-group list-group-flush",
    )
    return sc_at_glance_div


def generate_panel(data):
    style = {"margin-top": "2%", "margin-bottom": "2%"}
    sc_panel_div = dbc.Row(
        children=[
            dbc.Col(generate_at_glance(data), style=style),
            dbc.Col(
                [
                    # dbc.Row(dcc.Graph(id='g_boot_test_summary',figure=get_fig_booted(data)), style=style),
                    # dbc.Row(dcc.Graph(id='g_linux_test_summary',figure=get_fig_linux(data)), style=style),
                    # dbc.Row(dcc.Graph(id='g_pyadi_test_summary',figure=get_fig_pyadi(data)), style=style),
                    dbc.Row(dcc.Graph(id="g_logs_turnout", figure=get_fig_logs(data))),
                ]
            ),
        ],
        id="sc_panel_div",
    )
    return sc_panel_div


def generate_details(data):
    sc_details_div = html.Div(
        children=[
            dbc.Card(
                [
                    dbc.CardBody(
                        [
                            html.H4("Boot Test", className="card-title"),
                            generate_top_boot_failing(data),
                        ]
                    ),
                    dbc.CardBody(
                        [
                            html.H4("Linux Test - IIO Drivers", className="card-title"),
                            generate_drivers_enumeration(data),
                        ]
                    ),
                    dbc.CardBody(
                        [
                            html.H4("Linux Test - DMESG", className="card-title"),
                            generate_dmesg_errors(data),
                        ]
                    ),
                    dbc.CardBody(
                        [
                            html.H4("PYADI-IIO Tests", className="card-title"),
                            generate_pytest_results(data),
                        ]
                    ),
                ]
            ),
            # generate_drivers_enumeration(data),
            # generate_dmesg_errors(data),
        ],
        id="sc_details_div",
        className="row",
    )
    return sc_details_div


def generate_summaries(data):
    sc_summaries_div = html.Div(
        children=[generate_panel(data), generate_details(data)],
        id="sc_summaries_div",
        className="container",
    )
    return sc_summaries_div


def generate_report(data):
    report_div = generate_summaries(data)
    return report_div


########################### Callbacks #####################################


def register_callbacks(app):
    @app.callback(
        Output("sc_report_div", "children"),
        [
            Input("sc_project_options", "value"),
            Input("sc_branch_options", "value"),
            Input("sc_size_options", "value"),
            Input("sc_board_options", "value"),
        ],
    )
    def update_report_by_branch(project, branch, size, board):
        return generate_report(
            request_data(project=project, branch=branch, size=size, board=board)
        )


########################### Main Layout #####################################

layout = html.Div(
    children=[
        generate_logo(),
        generate_options(request_data()),
        html.Div(children=generate_report(request_data()), id="sc_report_div"),
    ]
)
