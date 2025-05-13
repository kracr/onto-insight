package com.calculation_engine.seedTermsExtraction;

import org.semanticweb.owlapi.model.OWLClass;
import org.semanticweb.owlapi.model.OWLOntology;
import java.util.Set;

public interface SeedTermExtractor {
    Set<OWLClass> getSeedTerms(OWLOntology ontology);

}
