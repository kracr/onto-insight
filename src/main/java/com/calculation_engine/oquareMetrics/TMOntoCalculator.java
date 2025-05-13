package com.calculation_engine.oquareMetrics;
import java.util.Collection;
import java.util.Set;
import java.util.stream.Collectors;
import org.semanticweb.owlapi.model.OWLClass;
import org.semanticweb.owlapi.model.OWLOntology;
import org.semanticweb.owlapi.search.EntitySearcher;

import com.calculation_engine.MetricCalculator;
import com.calculation_engine.OntologyUtils;

public class TMOntoCalculator implements MetricCalculator {
    @Override
    public double calculate(OWLOntology ontology) {

        double TMOnto = 0;
        int superClassCount = 0;
        Set<OWLClass> classes = ontology.getClassesInSignature();

        for (OWLClass cls : classes) {
            Collection<OWLClass> superClassesofOwlClass = OntologyUtils
		    .classExpr2classes(EntitySearcher.getSuperClasses(cls, ontology).collect(Collectors.toList()));
            superClassCount += superClassesofOwlClass.size();
        }

        TMOnto = (double) superClassCount / classes.size();

        return TMOnto;
    }
}

