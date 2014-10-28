{% extends 'display_priority.tpl' %}

{% block input %}{{ cell | create_input_codeblock }}{% endblock input %}


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
<div class='outputs' n={{ cell.prompt_number }}>
{{ super () }}
</div>
{% endblock outputs %}

{% block output %}{{ super () }}{% endblock output %}

{% block pyerr %}
{{ super() }}
{% endblock pyerr %}

{% block traceback_line %}
{{ line | strip_ansi }}
{% endblock traceback_line %}

{% block pyout %}{% endblock pyout %}

{% block stream %}{{ output.text }}{% endblock stream %}

{% macro caption(cell) -%}
{{ cell.metadata.get('attributes', {}).get('caption', '') | dequote }}
{%- endmacro %}

{% block data_svg %}
![{{ caption(cell) }}]({{ output.svg | data2uri(data_type='svg') }}){{ cell | create_attributes('figure') }}
{% endblock data_svg %}

{% block data_png %}
![{{ caption(cell) }}]({{ output.png | data2uri(data_type='png') }}){{ cell | create_attributes('figure') }}
{% endblock data_png %}

{% block data_jpg %}
![{{ caption(cell) }}]({{ output.jpeg | data2uri(data_type='jpeg') }}){{ cell | create_attributes('figure') }}
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
