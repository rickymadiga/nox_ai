import requests
from api import BASE_URL, get_headers


def get_builds(token):
    res = requests.get(
        f"{BASE_URL}/builds",
        headers=get_headers(token)
    )
    return res.json()


def get_build_history(token):
    res = requests.get(
        f"{BASE_URL}/builds/history",
        headers=get_headers(token)
    )
    return res.json()


def record_build(token, project_name):
    res = requests.post(
        f"{BASE_URL}/builds/record",
        params={
            "project_name": project_name,
            "status": "success"
        },
        headers=get_headers(token)
    )
    return res.json()


def delete_build(token, build_id):
    res = requests.delete(
        f"{BASE_URL}/builds/{build_id}",
        headers=get_headers(token)
    )
    return res.json()