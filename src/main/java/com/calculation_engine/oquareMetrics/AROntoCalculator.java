package com.calculation_engine.oquareMetrics;

import java.util.Set;

import org.semanticweb.owlapi.model.AxiomType;
import org.semanticweb.owlapi.model.OWLClass;
import org.semanticweb.owlapi.model.OWLOntology;

import com.calculation_engine.MetricCalculator;

public class AROntoCalculator implements MetricCalculator {

    @Override
    public double calculate(OWLOntology ontology) {
        double AROnto = 0;
        Set<OWLClass> classes = ontology.getClassesInSignature();
        int dataPropertyDomainAxioms = ontology.getAxiomCount(AxiomType.DATA_PROPERTY_DOMAIN);
        int objectPropertyDomainAxioms = ontology.getAxiomCount(AxiomType.OBJECT_PROPERTY_DOMAIN);

        if (!classes.isEmpty()) {
            AROnto = (double) (dataPropertyDomainAxioms + objectPropertyDomainAxioms) / classes.size();
        }
        return AROnto;
    }

}
