{% extends 'display_priority.tpl' %}

{% block input %}
{{ cell | create_input_codeblock }}
{% endblock input %}

{% block markdowncell scoped %}
{{ cell.source | wordwrap(80, False) }}
{% endblock markdowncell %}

{% block outputs %}
{{ cell | create_output_block }}
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
