from typing import Literal, Dict, Optional

from .. import _GraphAPIMethods

class DueDateTime(dict):
    def __init__(self, dateTime: str, timeZone: str):
        super().__init__()
        self["dateTime"] = dateTime
        self["timeZone"] = timeZone

class ToDo:
    def __init__(self, graph: _GraphAPIMethods):
        self.graph = graph

    def get_lists(self):
        response = self.graph.safe_request(
            method="GET",
            path="/me/todo/lists"
        )
        return response

    def post_list(self, displayName: str):
        data = {
            "displayName": displayName
        }
        response = self.graph.safe_request(
            method="POST",
            path="/me/todo/lists",
            json=data
        )
        return response

    def delete_list(self, id: str):
        response = self.graph.safe_request(
            method="DELETE",
            path=f"/me/todo/lists/{id}"
        )
        return response

    def post_task(self, taskListId: str, title: str, body: str = None, importance: Literal["low", "normal", "high"] = None, status: Literal["notStarted", "inProgress", "completed", "waitingOnOthers", "deferred"] = None, dueDateTime: DueDateTime = None, isReminderOn: bool = False):
        data = {}
        if title: data["title"] = title
        if body: data["body"] = {"content": body, "contentType": "text"}
        if importance: data["importance"] = importance
        if status: data["status"] = status
        if dueDateTime: data["dueDateTime"] = dueDateTime
        if isReminderOn: data["isReminderOn"] = isReminderOn
        response = self.graph.safe_request(
            method="POST",
            path=f"/me/todo/lists/{taskListId}/tasks",
            json=data
        )
        return response

    def patch_task(self, taskListId: str, taskId: str, title: str = None, body: str = None, importance: Literal["low", "normal", "high"] = None, status: Literal["notStarted", "inProgress", "completed", "waitingOnOthers", "deferred"] = None, dueDateTime: DueDateTime = None, isReminderOn: bool = None):
        data = {}
        if title: data["title"] = title
        if body: data["body"] = {"content": body, "contentType": "text"}
        if importance: data["importance"] = importance
        if status: data["status"] = status
        if dueDateTime: data["dueDateTime"] = dueDateTime
        if isReminderOn is not None: data["isReminderOn"] = isReminderOn
        response = self.graph.safe_request(
            method="PATCH",
            path=f"/me/todo/lists/{taskListId}/tasks/{taskId}",
            json=data
        )
        return response

    def delete_task(self, taskListId: str, taskId: str):
        response = self.graph.safe_request(
            method="DELETE",
            path=f"/me/todo/lists/{taskListId}/tasks/{taskId}"
        )
        return response

    def get_tasks(self, taskListId: str):
        response = self.graph.safe_request(
            method="GET",
            path=f"/me/todo/lists/{taskListId}/tasks"
        )
        return response