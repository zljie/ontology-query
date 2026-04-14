from ontology_query import Ontology


def test_load_and_query_examples():
    onto = Ontology.load("examples/p2p_behavior_effects_minimal.yaml")
    assert "suppliers" in onto.datasets()
    assert "status" in onto.fields("suppliers")
    actions = onto.actions_affecting_field("suppliers", "status")
    assert "suppliers/block" in actions
    assert "suppliers/unblock" in actions

