from flask_parameter_validation import ValidateParameters, Query

import boardlib.api.aurora
import flask
import requests
import json
import logging

import climbdex.db

blueprint = flask.Blueprint("api", __name__)

def parameter_error(e):
    code = 400
    name = str(type(e).__name__)
    description = f"Parameters were missing and/or misconfigured. If the issue persists, please <a href=\"https://github.com/lemeryfertitta/Climbdex/issues/new?title={str(type(e).__name__)}: {str(e)} ({code})\" target='_blank'>report it</a> (code: {code})"

    response =  {
        "error": True,
        "code": code,
        "name": name,
        "description": description,
    }, code

    logging.error(response)
    return response

@blueprint.errorhandler(Exception)
def handle_exception(e):
    response = e.get_response()
    response.data = json.dumps({
        "error": True,
        "code": e.code,
        "name": e.name,
        "description": f"There was a problem while getting results from the server. If the issue persists, please <a href=\"https://github.com/lemeryfertitta/Climbdex/issues/new?title={e.name} ({e.code})&body={e.description}\" target='_blank'>report it</a> (code: {e.code})",
    })
    response.content_type = "application/json"
    logging.error(response.data)
    return response



@blueprint.route("/api/v1/<board_name>/layouts")
def layouts(board_name):
    return flask.jsonify(climbdex.db.get_data(board_name, "layouts"))


@blueprint.route("/api/v1/<board_name>/layouts/<layout_id>/sizes")
def sizes(board_name, layout_id):
    return flask.jsonify(
        climbdex.db.get_data(board_name, "sizes", {"layout_id": int(layout_id)})
    )


@blueprint.route("/api/v1/<board_name>/layouts/<layout_id>/sizes/<size_id>/sets")
def sets(board_name, layout_id, size_id):
    return flask.jsonify(
        climbdex.db.get_data(
            board_name, "sets", {"layout_id": int(layout_id), "size_id": int(size_id)}
        )
    )


@blueprint.route("/api/v1/search/count")
@ValidateParameters(parameter_error)
def resultsCount(
    gradeAccuracy: float = Query(),
    layout: int = Query(),
    maxGrade: int = Query(),
    minAscents: int = Query(),
    minGrade: int = Query(),
    minRating: float = Query(),
    size: int = Query(),
):
    return flask.jsonify(climbdex.db.get_search_count(flask.request.args))

@blueprint.route("/api/v1/search")
@ValidateParameters(parameter_error)
def search(
    gradeAccuracy: float = Query(),
    layout: int = Query(),
    maxGrade: int = Query(),
    minAscents: int = Query(),
    minGrade: int = Query(),
    minRating: float = Query(),
    size: int = Query(),
):
    return flask.jsonify(climbdex.db.get_search_results(flask.request.args))


@blueprint.route("/api/v1/<board_name>/beta/<uuid>")
def beta(board_name, uuid):
    return flask.jsonify(climbdex.db.get_data(board_name, "beta", {"uuid": uuid}))


@blueprint.route("/api/v1/login/", methods=["POST"])
def login():
    try:
        login_details = boardlib.api.aurora.login(
            flask.request.json["board"],
            flask.request.json["username"],
            flask.request.json["password"],
        )
        return flask.jsonify(
            {"token": login_details["token"], "user_id": login_details["user_id"]}
        )
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == requests.codes.unprocessable_entity:
            return (
                flask.jsonify({"error": "Invalid username/password combination"}),
                e.response.status_code,
            )
        else:
            return flask.jsonify({"error": str(e)}), e.response.status_code
