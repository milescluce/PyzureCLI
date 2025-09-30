from typing import Literal, Dict

from .. import GraphAPI

class DueDateTime(dict):
    def __init__(self, dateTime: str, timeZone: str):
        super().__init__()
        self["dateTime"] = dateTime
        self["timeZone"] = timeZone

class ToDo:
    def __init__(self, graph: GraphAPI):
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
            data=data
        )
        return response

    def delete_list(self, id):
        pass

    def post_task(self, taskListId: str, title: str, body: str, importance: Literal["low", "normal", "high"], status: Literal["notStarted", "inProgress", "completed", "waitingOnOthers", "deferred"], dueDateTime: DueDateTime, isReminderOn: bool = False):
        data = {}
        if title: data["title"] = "title"
        if body: data["body"] = "body"
        if importance: data["importance"] = importance
        if status: data["status"] = status
        if dueDateTime: data["dueDateTime"] = dueDateTime
        if isReminderOn: data["isReminderOn"] = isReminderOn
        response = self.graph.safe_request(
            method="POST",
            path=f"me/todo/lists/{taskListId}/tasks",
            data=data
        )
        return response

    def patch_task(self):
        data = {}
    
