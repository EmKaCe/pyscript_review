"""SciProEvaluationOutput — Displays the generated evaluation report text."""

from __future__ import annotations

from puepy import Component, t

from src.browser.timer_manager import TimerManager


@t.component()
class SciProEvaluationOutput(Component):
    """Evaluation report card with Copy and Generate actions."""

    component_name = "sci-pro-evaluation-output"
    redraw_on_app_state_changes = ["generated_text"]

    def default_initial_state(self) -> dict[str, object]:
        return {"copied": False}

    def bind(self) -> None:
        self._timer_manager = TimerManager()

    def _on_copy(self, _event=None) -> None:
        text = self.application.state.get("generated_text", "")
        if not text:
            return
        try:
            from js import window
            window.navigator.clipboard.writeText(text)
            self.state["copied"] = True
            self._timer_manager.clear_all()
            self._timer_manager.set_timeout(lambda: self.state.update({"copied": False}) or self.page.redraw_tag(self), 2000)
            self.page.redraw_tag(self)
        except Exception:
            pass

    def _on_generate(self, _event=None) -> None:
        self.trigger_event("generate")

    def unbind(self) -> None:
        self._timer_manager.clear_all()

    def populate(self) -> None:
        report_text = self.application.state.get("generated_text", "")
        copied = self.state.get("copied", False)

        with t.sci_pro_card():
            with t.sci_pro_card_header():
                with t.div(class_name="flex items-center justify-between w-full"):
                    t.sci_pro_card_title("Evaluation Report", class_name="text-base")
                    with t.div(class_name="flex items-center gap-2"):
                        if report_text:
                            with t.sci_pro_button(variant="outline", size="sm", on_click=self._on_copy):
                                if copied:
                                    t.i(class_name="i-lucide-check size-3.5 mr-1 text-green-600")
                                    t("Copied")
                                else:
                                    t.i(class_name="i-lucide-copy size-3.5 mr-1")
                                    t("Copy")

                        with t.sci_pro_button(size="sm", on_click=self._on_generate):
                            t.i(class_name="i-lucide-message-square size-3.5 mr-1")
                            t("Generate")

            with t.sci_pro_card_content():
                if report_text:
                    t.sci_pro_textarea(
                        value=report_text,
                        readonly=True,
                        class_name="min-h-64 resize-y font-mono text-sm leading-relaxed"
                    )
                else:
                    with t.div(class_name="flex flex-col items-center gap-2 py-8 text-center"):
                        t.i(class_name="i-lucide-file-text size-8 text-muted-foreground/40")
                        with t.p(class_name="text-sm text-muted-foreground"):
                            t("Click ")
                            t.strong("Generate")
                            t(" to create the evaluation report from your selected criteria.")
