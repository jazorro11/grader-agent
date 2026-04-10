from grader_agent.grading.llm_json import json_object_from_message_content


def test_json_object_vacio_si_content_no_es_str():
    assert json_object_from_message_content(None) == {}
    assert json_object_from_message_content(1) == {}


def test_json_object_vacio_si_json_invalido():
    assert json_object_from_message_content("not json") == {}


def test_json_object_dict_ok():
    assert json_object_from_message_content('{"a": 1}') == {"a": 1}


def test_json_object_lista_no_es_dict():
    assert json_object_from_message_content("[1,2]") == {}
