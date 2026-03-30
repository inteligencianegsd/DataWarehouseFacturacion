from typing import Literal

from utils.RunMode import RunMode


class AppConfig:

    def __init__(
            self,
            db_alias: Literal["LOCAL", "QUANTA"] = "LOCAL",
            run_mode: RunMode = RunMode.INCREMENTAL
    ):
        self.db_alias = db_alias
        self.run_mode = run_mode
