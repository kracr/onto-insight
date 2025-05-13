package com.calculation_engine.oquareMetrics;

import java.util.Set;

import org.semanticweb.owlapi.model.AxiomType;
import org.semanticweb.owlapi.model.OWLClass;
import org.semanticweb.owlapi.model.OWLEntity;
import org.semanticweb.owlapi.model.OWLOntology;
import org.semanticweb.owlapi.model.OWLSubClassOfAxiom;

import com.calculation_engine.MetricCalculator;

public class NOMOntoCalculator implements MetricCalculator {

    @Override
    public double calculate(OWLOntology ontology) {
        double NOMOnto = 0;
        Set<OWLClass> classes = ontology.getClassesInSignature();

        int dataPropAssertionAxiomCount = ontology.getAxiomCount(AxiomType.DATA_PROPERTY_ASSERTION);

        int objectPropOnClasses = 0;

        for (OWLClass owlClass : classes) {

            for (OWLSubClassOfAxiom classExpr : ontology.getSubClassAxiomsForSubClass(owlClass)) {
            for (OWLEntity entity : classExpr.getSignature()) {
                if (entity.isOWLObjectProperty()) {
                objectPropOnClasses++;
                }
            }
        }
    }

        NOMOnto = (double) (dataPropAssertionAxiomCount + objectPropOnClasses ) / classes.size();

        return NOMOnto;

    }

}
