package com.calculation_engine.oquareMetrics;

import java.util.Set;

import org.semanticweb.owlapi.model.AxiomType;
import org.semanticweb.owlapi.model.OWLClass;
import org.semanticweb.owlapi.model.OWLOntology;

import com.calculation_engine.MetricCalculator;

public class CROntoCalculator implements MetricCalculator {

    @Override
    public double calculate(OWLOntology ontology) {
        double CROnto = 0;
        Set<OWLClass> classes = ontology.getClassesInSignature();
        int classAssertionAxioms = ontology.getAxiomCount(AxiomType.CLASS_ASSERTION);

        if (!classes.isEmpty()) {
            CROnto = (double) classAssertionAxioms / classes.size();
        }
        return CROnto;
    }

}
