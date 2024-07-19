from langchain_core.callbacks.base import BaseCallbackHandler
from typing import Any

from utils.logs import insert_logs
from utils.functions import clean_string, transform_json_to_string


def elapsed(run: Any) -> str:
    """Get the elapsed time of a run.
    Args:
        run: any object with a start_time and end_time attribute.
    Returns:
        A string with the elapsed time in seconds or
            milliseconds if time is less than a second
    """
    elapsed_time = run.end_time - run.start_time
    milliseconds = elapsed_time.total_seconds() * 1000
    if milliseconds < 1000:
        return f"{milliseconds:.0f}ms"
    return f"{(milliseconds / 1000):.2f}s"


class logsHandler(BaseCallbackHandler):
    def __init__(
        self,
        outFile=[],
        print_logs=False,
        print_starts=True,
        print_ends=True,
        print_errors=True,
        **kwargs,
    ):
        super()
        self.tracer = {}
        self.outFile = outFile
        self.print_logs = print_logs
        self.start = print_starts
        self.ends = print_ends
        self.errors = print_errors
        with open("./log.txt", "w") as log:
            log.write("[START]\n")

    def log_to_file(self, event):
        self.outFile.append(event)

        print(event)

        table = {
            "name": "steps",
            "schema": "chatbot",
            "columns": {
                "query_id": "text",
                "type": "text",
                "name_tags": "text",
                "input": "text",
                "name": "text",
                "output": "text",
                "error": "text",
                "tags": "text",
                "promps": "text",
                "duration": "text",
                "loading": "text",
                "tkn_cnt": "text",
            },
        }
        """
        values = {
            "type": str(event.get("type", "")),
            "name_tags": str(event.get("name_tags", "")),
            "input": str(event.get("input", "")),
            "name": str(event.get("name", "")),
            "output": clean_string(transform_json_to_string(event.get("output", ""))),
            "error": str(event.get("error", "")),
            "tags": str(event.get("tags", "")),
            "promps": str(event.get("promps", "")),
            "duration": str(event.get("duration", "")),
            "loading": str(event.get("loading", "")),
            "tkn_cnt": str(event.get("tkn_cnt", "")),
        }
        insert_logs(table=table, values=values, log_type="wrapper")
        """

        # with open("./log.txt", "a") as log:
        # log.write(str(event) + "\n")

    def parent_tracking(self, node):
        trace = []
        current_node = self.tracer[node]
        while current_node["parent_run_id"]:
            trace.append(current_node["name"])
            current_node = self.tracer[current_node["parent_run_id"]]
        trace.append(current_node["name"])
        trace.reverse()
        return ">".join(trace)

    # chain
    def on_chain_start(self, serialized, inputs, run_id, **kwargs):
        # print( 'Entering new chain {}'.format(kwargs.keys()))
        name = str(kwargs["name"]) if "name" in kwargs.keys() else ""

        formatted_response = {
            "type": "Chain start",
            "names_tags": name + ":" + ",".join(kwargs["tags"]),
            "input": inputs,
        }

        self.tracer[run_id] = {"parent_run_id": kwargs["parent_run_id"], "name": name}
        _track = self.parent_tracking(run_id)
        _id = name + ":" + ",".join(kwargs["tags"])
        # _serie = serialized['name']
        if self.print_logs and self.start:
            print(f"Entering new chain[{_track}]: {_id} ")
            self.log_to_file(formatted_response)

    def on_chain_end(self, outputs, run_id, **kwargs):
        if self.tracer[run_id]["name"] == "PromptTemplate":
            outputs = "Template"

        formatted_response = {
            "type": "Chain end",
            "name": self.tracer[run_id]["name"],
            "output": outputs,
        }

        _track = self.parent_tracking(run_id)
        # _run = elapsed(run)
        if self.print_logs and self.ends:
            print(f"Finish chain[{_track}formatted_response]:  {outputs}")
            self.log_to_file(formatted_response)

    def on_chain_error(self, error, run_id, **kwargs):
        formatted_response = {
            "type": "Chain error",
            "name": self.tracer[run_id]["name"],
            "error": error,
            "tags": kwargs["tags"],
        }

        _track = self.parent_tracking(run_id)
        if self.print_logs and self.errors:
            print(f"Error chain [{_track}]:  {error} ")
            self.log_to_file(formatted_response)

    # llms
    def on_llm_start(self, serialized, prompts, run_id, **kwargs):
        formatted_response = {
            "type": "LLM start",
            "name": str(kwargs["name"]) + ":" + str(serialized["name"]),
            "prompts": prompts,
        }

        self.tracer[run_id] = {
            "parent_run_id": kwargs["parent_run_id"],
            "name": kwargs["name"],
        }
        _serie = serialized["name"]
        _kwargs = kwargs["name"]
        if self.print_logs and self.start:
            print(f"Starting llm:  {_serie} {_kwargs} ")
            self.log_to_file(formatted_response)

    def on_llm_end(self, response, run_id, **kwargs):
        basis_response = response.generations[0][0]
        name = self.tracer[run_id]["name"]
        formatted_response = {
            "type": "LLM end",
            "name": name,
            "output": basis_response.text,
            "duration": basis_response.generation_info.get("total_duration", 0) / 1e9,
            "loading": basis_response.generation_info.get("load_duration", 0) / 1e9,
            "tkn_cnt": basis_response.generation_info.get("eval_count"),
        }

        metric = (basis_response.generation_info.get("total_duration", 0)) / 1e9
        loading = (basis_response.generation_info.get("load_duration", 0)) / 1e9
        model_only = metric - loading
        out = basis_response.text
        if self.print_logs and self.ends:
            print(f"Finish llm {name}[t:{metric},l:{loading},m:{model_only}]: {out}")
        self.log_to_file(formatted_response)

    def on_llm_error(self, error, **kwargs):
        formatted_response = {"type": "LLM error", "error": error}

        if self.print_logs and self.errors:
            print(f"Error llm:  {error}")
            self.log_to_file(formatted_response)
