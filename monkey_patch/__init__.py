# coding=utf-8
from drf_yasg import openapi
from drf_yasg.inspectors import ChoiceFieldInspector, NotHandled
from drf_yasg.inspectors.field import get_parent_serializer, get_model_field, get_basic_type_info, \
    get_basic_type_info_from_hint
from drf_yasg.utils import field_value_to_representation
from rest_framework import serializers
from rest_framework.fields import MultipleChoiceField


def field_to_swagger_object(self, field, swagger_object_type, use_references, **kwargs):
    SwaggerType, ChildSwaggerType = self._get_partial_types(field, swagger_object_type, use_references, **kwargs)

    if isinstance(field, (serializers.ChoiceField, MultipleChoiceField)):
        enum_type = openapi.TYPE_STRING
        enum_values = []
        choice_path = ""
        try:
            choice_path = str(field.parent.Meta.model._meta.get_field(field.field_name)).lower().replace(
                '.', '_')
        except Exception as e:
            pass

        choice_path and enum_values.append(f"选项接口字段为:{choice_path}")
        enum_values.append("选项为:")
        for choice, value in field.choices.items():
            if isinstance(field, serializers.MultipleChoiceField):
                choice = f"{field_value_to_representation(field, [choice])[0]}:{value}"
            else:
                choice = f"{field_value_to_representation(field, choice)}:{value}"

            enum_values.append(choice)

        serializer = get_parent_serializer(field)
        if isinstance(serializer, serializers.ModelSerializer):
            model = getattr(getattr(serializer, 'Meta'), 'model')
            model_field = get_model_field(model, field.source or field.parent.source)
            if getattr(model_field, "base_field", None):
                model_field = model_field.base_field
            if model_field:
                model_type = get_basic_type_info(model_field)
                if model_type:
                    enum_type = model_type.get('type', enum_type)
        else:
            # Try to infer field type based on enum values
            enum_value_types = {type(v) for v in enum_values}
            if len(enum_value_types) == 1:
                values_type = get_basic_type_info_from_hint(next(iter(enum_value_types)))
                if values_type:
                    enum_type = values_type.get('type', enum_type)

        result = SwaggerType(type=enum_type, enum=enum_values)

        return result

    return NotHandled


ChoiceFieldInspector.field_to_swagger_object = field_to_swagger_object
