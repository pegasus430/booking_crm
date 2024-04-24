from django import forms
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe


class CustomSelectWidget(forms.Select):
    def __init__(self, add_url=None, *args, **kwargs):
        self.add_url = add_url
        super().__init__(*args, **kwargs)

    def render(self, name, value, attrs=None, renderer=None):
        output = super().render(name, value, attrs=attrs, renderer=renderer)
        if self.add_url:
            add_link = reverse_lazy(self.add_url)
            output += mark_safe(f'<a href="{add_link}" class="add-another btn btn-link ml-2">Add New</a>')
        return output
