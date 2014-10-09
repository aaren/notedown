{% extends 'display_priority.tpl' %}

{% block input %}
```{.python .input n={{ cell.prompt_number }}}
{{ cell.input }}
```
{% endblock input %}

{% block markdowncell scoped %}
{{ cell.source }}
{% endblock markdowncell %}

{% block outputs %}
```{.json .output n={{ cell.prompt_number }}}
{{ cell.outputs | json2string }}
```
{% endblock outputs %}

{% block headingcell scoped %}
{{ '#' * cell.level }} {{ cell.source | replace('\n', ' ') }}
{% endblock headingcell %}

{% block unknowncell scoped %}
unknown type  {{ cell.type }}
{% endblock unknowncell %}

{% block pyerr %}
{{ super() }}
{% endblock pyerr %}

{% block traceback_line %}
{{ line | indent | strip_ansi }}
{% endblock traceback_line %}
