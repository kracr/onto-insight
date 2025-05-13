package com.calculation_engine;

import org.semanticweb.owlapi.model.OWLOntology;

public interface MetricCalculator {
    double calculate(OWLOntology ontology);
}