package com.calculation_engine.oquareMetrics;

import java.util.Collection;
import java.util.Set;

import org.semanticweb.owlapi.model.OWLClass;
import org.semanticweb.owlapi.model.OWLOntology;
import org.semanticweb.owlapi.search.EntitySearcher;

import com.calculation_engine.MetricCalculator;
import com.calculation_engine.OntologyUtils;

import java.util.stream.Collectors;

public class POntoCalculator implements MetricCalculator {

    @Override
    public double calculate(OWLOntology ontology) {

        double POnto = 0;
        int superClassCount = 0;
        Set<OWLClass> classes = ontology.getClassesInSignature();

        for (OWLClass cls : classes) {
            Collection<OWLClass> superClassesofOwlClass = OntologyUtils
		    .classExpr2classes(EntitySearcher.getSuperClasses(cls, ontology).collect(Collectors.toList()));
            superClassCount += superClassesofOwlClass.size();
        }

        POnto = (double) superClassCount / classes.size();

        return POnto;
    }
}
