package com.calculation_engine.oquareMetrics;
import java.util.Collection;
import java.util.Set;
import java.util.stream.Collectors;
import org.semanticweb.owlapi.model.OWLClass;
import org.semanticweb.owlapi.model.OWLOntology;
import org.semanticweb.owlapi.search.EntitySearcher;

import com.calculation_engine.MetricCalculator;
import com.calculation_engine.OntologyUtils;

public class TMOnto2Calculator implements MetricCalculator {
    @Override
    public double calculate(OWLOntology ontology) {
        Set<OWLClass> classes = ontology.getClassesInSignature();
        int superClassesSum = 0;  // Sum of superclasses for classes with multiple inheritance
        int classesWithMultipleInheritance = 0;

        for (OWLClass cls : classes) {
            // Get direct superclasses, excluding owl:Thing
            Collection<OWLClass> directSuperClasses = OntologyUtils
                .classExpr2classes(EntitySearcher.getSuperClasses(cls, ontology).collect(Collectors.toList()))
                .stream()
                .filter(superClass -> !superClass.isOWLThing())
                .collect(Collectors.toSet());
            
            // If class has multiple inheritance, add its superclass count to the sum
            if (directSuperClasses.size() > 1) {
                superClassesSum += directSuperClasses.size();
                classesWithMultipleInheritance++;
            }
        }

        // Return 0 if there are no classes with multiple inheritance to avoid division by zero
        if (classesWithMultipleInheritance == 0) {
            return 0.0;
        }

        // Calculate: (sum of superclasses for classes with multiple inheritance) / (number of classes with multiple inheritance)
        return (double) superClassesSum / classesWithMultipleInheritance;
    }
}

