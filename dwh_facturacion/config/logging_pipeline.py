from sklearn.pipeline import Pipeline
import logging
import time


class LoggingPipeline(Pipeline):
    def __init__(self, steps, *, pipeline_name="DefaultPipeline", logger=None, **kwargs):
        super().__init__(steps, **kwargs)
        self.pipeline_name = pipeline_name
        self.logger = logger or logging.getLogger("pipeline_logger")

    def fit_transform(self, X, y=None, **fit_params):
        Xt = X
        for name, transform in self.steps[:-1]:
            class_name = transform.__class__.__name__
            msg_prefix = f"[Pipeline: {self.pipeline_name}] [Step: {name}] [Class: {class_name}]"
            self.logger.info(f"▶️ {msg_prefix} Fit-Transform started.")
            start = time.time()
            if hasattr(transform, "fit_transform"):
                Xt = transform.fit_transform(Xt, y)
            else:
                Xt = transform.fit(Xt, y).transform(Xt)
            elapsed = time.time() - start
            self.logger.info(f"✅ {msg_prefix} Fit-Transform finished in {elapsed:.3f} s.")

        # Último paso
        name, final_step = self.steps[-1]
        class_name = final_step.__class__.__name__
        msg_prefix = f"[Pipeline: {self.pipeline_name}] [Step: {name}] [Class: {class_name}]"
        self.logger.info(f"▶️ {msg_prefix} Fit-Transform started.")
        start = time.time()
        if hasattr(final_step, "fit_transform"):
            Xt = final_step.fit_transform(Xt, y)
        else:
            Xt = final_step.fit(Xt, y).transform(Xt)
        elapsed = time.time() - start
        self.logger.info(f"✅ {msg_prefix} Fit-Transform finished in {elapsed:.3f} s.")

        return Xt

    def transform(self, X):
        Xt = X
        for name, transform in self.steps:
            class_name = transform.__class__.__name__
            msg_prefix = f"[Pipeline: {self.pipeline_name}] [Step: {name}] [Class: {class_name}]"
            self.logger.info(f"▶️ {msg_prefix} Transform started.")
            start = time.time()
            Xt = transform.transform(Xt)
            elapsed = time.time() - start
            self.logger.info(f"✅ {msg_prefix} Transform finished in {elapsed:.3f} s.")
        return Xt
