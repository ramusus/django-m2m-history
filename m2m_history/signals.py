from django.dispatch import Signal

m2m_history_changed = Signal(providing_args=["action", "instance", "reverse", "model", "pk_set", "using", "field_name", "time"])