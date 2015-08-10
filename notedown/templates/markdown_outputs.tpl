{% extends 'display_priority.tpl' %}

{% block input %}
{{ cell | create_input_codeblock }}
{% endblock input %}

{% block markdowncell scoped %}
{{ cell.source }}
{% endblock markdowncell %}

{% block headingcell scoped %}
{{ '#' * cell.level }} {{ cell.source | replace('\n', ' ') }}
{% endblock headingcell %}

{% block unknowncell scoped %}
unknown type  {{ cell.type }}
{% endblock unknowncell %}


{% block outputs %}
<div class='outputs' n={{ cell.execution_count }}>
{{ super () }}
</div>
{% endblock outputs %}

{% block output %}{{ super () }}{% endblock output %}

{% block error %}
{{ super() }}
{% endblock error %}

{% block traceback_line %}
{{ line | strip_ansi }}
{% endblock traceback_line %}

{% block execute_result %}{% endblock execute_result %}

{% block stream %}{{ output.text }}{% endblock stream %}

{% macro caption(cell) -%}
{{ cell.metadata.get('attributes', {}).get('caption', '') | dequote }}
{%- endmacro %}

{% block data_svg %}
<div {{ cell | create_attributes('figure') }}>
![{{ caption(cell) }}]({{ output.data | data2uri(data_type='svg') }})
</div>
{% endblock data_svg %}

{% block data_png %}
<div {{ cell | create_attributes('figure') }}>
![{{ caption(cell) }}]({{ output.data | data2uri(data_type='png') }})
</div>
{% endblock data_png %}

{% block data_jpg %}
<div {{ cell | create_attributes('figure') }}>
![{{ caption(cell) }}]({{ output.data | data2uri(data_type='jpeg') }})
</div>
{% endblock data_jpg %}

{% block data_latex %}
{{ output.latex }}
{% endblock data_latex %}

{% block data_html scoped %}
{{ output.html }}
{% endblock data_html %}

{% block data_text scoped %}
{{ output.text }}
{% endblock data_text %}
