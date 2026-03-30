import yaml

from utils.RunMode import RunMode


class PipelineGlobalConfig:

    def __init__(self, path="config/pipeline_config.yaml"):
        with open(path, "r") as f:
            config = yaml.safe_load(f)

        run_mode_yml = config.get("run_mode", "INCREMENTAL")
        if run_mode_yml == "INICIAL":
            self.run_mode = RunMode.INICIAL
        elif run_mode_yml == "INCREMENTAL":
            self.run_mode = RunMode.INCREMENTAL

        self.db_alias = config.get("db_alias", "LOCAL")

    @property
    def is_full_load(self):
        return self.run_mode.upper() == "FULL"