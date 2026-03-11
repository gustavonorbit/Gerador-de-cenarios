"""
Dynamic action form.

Responsibility:
 - Render input fields for a selected action based on its JSON `inputs` definition.
 - Provide a simple API to read entered values (to be used later by the executor).

Supported field types:
 - `text` -> `QLineEdit`
 - `number` -> `QSpinBox`
 - `select` -> `QComboBox` (expects `options` list in input definition)
"""
from typing import Dict, Any, Optional
from PySide6.QtWidgets import (
    QWidget,
    QFormLayout,
    QLineEdit,
    QLabel,
    QSpinBox,
    QComboBox,
)


class ActionForm(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QFormLayout(self)
        self.inputs: Dict[str, QWidget] = {}

    def clear(self) -> None:
        while self.layout.count():
            item = self.layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.inputs.clear()

    def load_action(self, action: Optional[Dict[str, Any]]) -> None:
        """Populate the form for the given action dictionary.

        Expected `action` structure matches the JSON files under `actions/`.
        """
        self.clear()
        if not action:
            self.layout.addRow(QLabel("Nenhuma ação selecionada"))
            return

        # Show description
        desc = action.get("description", "")
        if desc:
            self.layout.addRow(QLabel(desc))

        for inp in action.get("inputs", []):
            name = inp.get("name")
            label = inp.get("label", name)
            typ = inp.get("type", "text")
            default = inp.get("default")

            if typ == "text":
                widget = QLineEdit()
                if default is not None:
                    widget.setText(str(default))
            elif typ == "number":
                widget = QSpinBox()
                widget.setRange(-2147483648, 2147483647)
                if default is not None:
                    try:
                        widget.setValue(int(default))
                    except Exception:
                        pass
            elif typ == "select":
                widget = QComboBox()
                options = inp.get("options", [])
                for opt in options:
                    widget.addItem(str(opt))
                if default is not None:
                    idx = widget.findText(str(default))
                    if idx >= 0:
                        widget.setCurrentIndex(idx)
            else:
                # Fallback: text input
                widget = QLineEdit()
                if default is not None:
                    widget.setText(str(default))

            self.layout.addRow(label, widget)
            self.inputs[name] = widget

    def load_arguments(self, args: list) -> None:
        """Populate the form using a list of argument names (strings).

        Each argument will be rendered as a text input by default.
        """
        self.clear()
        if not args:
            self.layout.addRow(QLabel("Nenhuma argumento detectado"))
            return

        for name in args:
            label = name.replace("_", " ").capitalize()
            widget = QLineEdit()
            self.layout.addRow(label, widget)
            self.inputs[name] = widget

    def get_values(self) -> Dict[str, Any]:
        values: Dict[str, Any] = {}
        for name, widget in self.inputs.items():
            if isinstance(widget, QLineEdit):
                values[name] = widget.text()
            else:
                # import here to avoid top-level typing import issues
                from PySide6.QtWidgets import QSpinBox, QComboBox

                if isinstance(widget, QSpinBox):
                    values[name] = widget.value()
                elif isinstance(widget, QComboBox):
                    values[name] = widget.currentText()
                else:
                    # Generic fallback
                    try:
                        values[name] = widget.text()
                    except Exception:
                        values[name] = None
        return values
