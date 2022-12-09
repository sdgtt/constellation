from urllib.parse import unquote, urlparse

from app.models import boards as b
from app.models import boot_tests as bt
from app.models.db import DB
from app.models.score import Score
from app.pages.hwtests import allboards as ab
from app.pages.publicci.dashboard import Dashboard
from app.pages.pyadi.plots import gen_line_plot_html
from app.utility import artifact_url_gen, filter_gen, url_gen
from flask import (
    Blueprint,
    Flask,
    Markup,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask.helpers import get_root_path

# from junit2htmlreport import parser

# app = Flask(__name__)
server_bp = Blueprint("constellation", __name__)

JENKINS_SERVER = "gateway.englab"
JENKINS_PORT = None

pci_dash = Dashboard(
    gh_projects=[
        {"repo": "linux"},
        {"repo": "libiio"},
        {"repo": "iio-oscilloscope"},
        {"repo": "libad9361-iio"},
        {"repo": "libsmu"},
        {"repo": "libm2k"},
        {"repo": "scopy"},
        {"repo": "pyadi-iio"},
        {"repo": "pyadi-jif", "branch": "main"},
        {"repo": "pyadi-dt", "branch": "main"},
        {"repo": "genalyzer", "branch": "main"},
        {"repo": "TransceiverToolbox"},
        {"repo": "HighSpeedConverterToolbox"},
        {"repo": "SensorToolbox"},
        {"repo": "RFMicrowaveToolbox", "branch": "main"},
        {"repo": "TimeOfFlightToolbox"},
    ]
)


@server_bp.route("/")
def welcome():
    svg = open(get_root_path(__name__) + "/static/sdg.svg").read()
    return render_template("index.html", sdg_logo=Markup(svg))


@server_bp.route("api/")
@server_bp.route("api/<param>")
def api(param=None):
    size = 10000
    order = "desc"
    agg_field = None
    kwargs = {}
    filters = filter_gen(urlparse(unquote(request.url)).query)
    for f, v in filters.items():
        if isinstance(v, list):
            for el in v:
                if f == "size":
                    size = int(el)
                elif f == "order":
                    order = el
                elif f == "agg_field":
                    agg_field = el
                else:
                    kwargs.update({f: el})
    result_json = DB().search(size=size, order=order, agg_field=agg_field, **kwargs)
    return result_json


@server_bp.route("api/board/<board_name>/")
@server_bp.route("api/board/<board_name>/<param>")
def board_api(board_name, param=None):
    boot_test_filtered = []
    jenkins_project_name = "HW_tests/HW_test_multiconfig"
    filters = filter_gen(urlparse(request.url).query)
    boot_tests = bt.BoardBootTests(
        boot_folder_name=board_name,
        jenkins_project_name=jenkins_project_name,
        filters=filters,
    ).boot_tests_dict
    for index, boot_test in enumerate(boot_tests):
        new_dict = {}
        for k, v in boot_test.items():
            if k not in ["boot_test_failure", "raw_boot_test_result"]:
                new_dict.update({k: v})
        boot_test_filtered.append(new_dict)
    return {"hits": boot_test_filtered}


@server_bp.route("api/sc/")
@server_bp.route("api/sc/<param>")
def score_api(param=None):
    default_jenkins_project = "HW_tests/HW_test_multiconfig"
    default_branch = "boot_partition_master"
    default_size = 7
    filters = filter_gen(urlparse(unquote(request.url)).query)
    jenkins_project = (
        filters["jenkins_project"][0]
        if "jenkins_project" in filters
        else default_jenkins_project
    )
    size = filters["size"][0] if "size" in filters else default_size
    board = filters["board"][0] if "board" in filters else None
    branch = filters["branch"][0] if "branch" in filters else default_branch
    deprecated = []
    sc = Score(
        jenkins_project=jenkins_project,
        size=int(size),
        branch=branch,
        board=board,
        deprecated=deprecated,
    )
    return sc.to_json()


@server_bp.route("boards")
def allboards():
    # retrieve boards from elastic server
    # filter by jenkins_project_name
    jenkins_project_name = "HW_tests/HW_test_multiconfig"
    source_adjacency_matrix = "boot_partition_master"
    deprecated = []
    boards_ref = b.Boards(
        jenkins_project_name, source_adjacency_matrix, deprecated
    ).boards
    headers = ["Board", "Status"]
    boards = [
        {
            "Job Date": board.jenkins_job_date,
            "Board": board.board_name,
            "Jenkins Project Name": board.jenkins_project_name,
            "Jenkins Build Number": board.jenkins_build_number,
            "Artifactory source branch": board.source_adjacency_matrix,
            "HDL Commit": board.hdl_hash,
            "Linux Commit": board.linux_hash,
            "Status": {
                "Online": board.is_online,
                "Status": board.boot_test_result,
                "Failure reason": "None"
                if len(board.boot_test_failure) == 0
                else board.boot_test_failure,
            },
            "Action": "NA",
            "url": url_gen(
                JENKINS_SERVER,
                JENKINS_PORT,
                board.jenkins_project_name,
                board.jenkins_build_number,
                board.board_name,
                board.hdl_hash.split(" ")[0].strip(),
                board.linux_hash.split(" ")[0].strip(),
            ),
        }
        for board in boards_ref
    ]

    summary = {
        "Active Boards": len(boards),
        "Passing": len(
            [board for board in boards if board["Status"]["Status"] == "Pass"]
        ),
        "Online": len([board for board in boards if board["Status"]["Online"]]),
        "deprecated": len(deprecated),
    }
    summary["Passing Percent"] = 100 * summary["Passing"] / summary["Active Boards"]

    summary["Online Percent"] = 100 * summary["Online"] / summary["Active Boards"]
    return render_template(
        "hwtests/allboards.html", headers=headers, boards=boards, summary=summary
    )


@server_bp.route("board/<board_name>/")
@server_bp.route("board/<board_name>/<param>")
def board(board_name, param=None):
    # filter by jenkins_project_name
    jenkins_project_name = "HW_tests/HW_test_multiconfig"
    filters = filter_gen(urlparse(request.url).query)
    boot_tests = bt.BoardBootTests(
        boot_folder_name=board_name,
        jenkins_project_name=jenkins_project_name,
        filters=filters,
    ).boot_tests
    boards = [
        {
            "Jenkins Job Date": test.jenkins_job_date,
            "Trigger": test.jenkins_trigger.split(":")[-1],
            "Artifactory source branch": test.source_adjacency_matrix,
            "HDL Commit": test.hdl_hash,
            "Linux Commit": test.linux_hash,
            "u-boot Reached": test.uboot_reached,
            "Linux Booted": test.linux_prompt_reached,
            "Linux Tests": {
                "dmesg_errors": test.dmesg_errors_found,
                "drivers_missing": test.drivers_missing,
            },
            "pyadi Tests": {
                "pass": str(
                    int(test.pytest_tests)
                    - int(test.pytest_failures)
                    - int(test.pytest_skipped)
                ),
                "fail": test.pytest_failures,
            },
            "Jenkins Build Number": test.jenkins_build_number,
            "Failure reason": "None"
            if len(test.boot_test_failure) == 0
            else test.boot_test_failure,
            "Artifacts": artifact_url_gen(
                JENKINS_SERVER,
                JENKINS_PORT,
                test.jenkins_project_name,
                test.jenkins_build_number,
                board_name,
            ),
            "Result": test.boot_test_result,
            "url": url_gen(
                JENKINS_SERVER,
                JENKINS_PORT,
                test.jenkins_project_name,
                test.jenkins_build_number,
                board_name,
                test.hdl_hash.split(" ")[0].strip(),
                test.linux_hash.split(" ")[0].strip(),
                test.jenkins_trigger,
            ),
        }
        for test in boot_tests
    ]
    return render_template("hwtests/board.html", board_name=board_name, boards=boards)


@server_bp.route("kibana/<visualization>")
def kibana(visualization):
    return render_template("kibana/index.html", visualization=visualization)


@server_bp.route("pyadi-iio/<vendor>")
def pyadi(vendor: str):
    import yaml

    with open("app/board_table.yaml", "r") as stream:
        data_loaded = yaml.safe_load(stream)
    # boards = list(data_loaded.keys())
    # print(boards)
    # print("vendor", vendor)
    if vendor == "all" or vendor == "":
        return render_template("pyadi_iio/index.html", boards=data_loaded)

    out = {}
    for board in data_loaded:
        if vendor == "xilinx":
            if "xilinx" in board or "zynq" in board or "pluto" in board:
                out[board] = data_loaded[board]
        if vendor == "intel":
            if "intel" in board or "socfpga" in board or "arria10" in board:
                out[board] = data_loaded[board]

    return render_template("pyadi_iio/index.html", boards=out)


@server_bp.route("pyadi-iio/design/<design>")
def pyadi_design(design: str):
    # import yaml
    # with open("board_table.yaml", 'r') as stream:
    #     data_loaded = yaml.safe_load(stream)
    # print(design)
    fightml = gen_line_plot_html([1, 2, 3], [1, 2, 3], "x", "y", "Test")

    return render_template("pyadi_iio/boards.html", fig=fightml, design=design)


# Serve some static files
@server_bp.route("files/<path:name>")
def send_file(name):
    return send_from_directory("templates/", name)


@server_bp.route("static/<path:filename>")
def send_assets(filename):
    return send_from_directory("static/", filename)


@server_bp.route("publicci")
def public_ci():
    return pci_dash.get_status_html()
