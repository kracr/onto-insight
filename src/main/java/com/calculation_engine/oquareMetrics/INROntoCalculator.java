package com.calculation_engine.oquareMetrics;

import java.util.Set;

import org.semanticweb.owlapi.model.AxiomType;
import org.semanticweb.owlapi.model.OWLClass;
import org.semanticweb.owlapi.model.OWLOntology;

import com.calculation_engine.MetricCalculator;

public class INROntoCalculator implements MetricCalculator {

    @Override
    public double calculate(OWLOntology ontology) {
        double INROnto = 0;
        Set<OWLClass> classes = ontology.getClassesInSignature();
        int subClassofAxiomCount = ontology.getAxiomCount(AxiomType.SUBCLASS_OF);

        if (!classes.isEmpty()) {
            INROnto =  (double) subClassofAxiomCount / classes.size();
        }
        return INROnto;
    }

}
