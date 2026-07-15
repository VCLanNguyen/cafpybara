"""Topology-agnostic mechanics shared by every analysis in cafpybara/analyses/.

Nothing in this package defaults to a specific analysis topology -- every
topology-specific value (rec_key, cut list, category dict, detvar/intime
paths) is a required parameter here. Each analysis under `cafpybara/analyses/`
supplies its own defaults via a thin wrapper layer.
"""
