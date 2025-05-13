package com.calculation_engine;

import org.semanticweb.owlapi.model.OWLOntology;
import org.semanticweb.HermiT.ReasonerFactory;
import org.semanticweb.owlapi.reasoner.OWLReasoner;
import org.semanticweb.owlapi.reasoner.ConsoleProgressMonitor;
import org.semanticweb.owlapi.reasoner.OWLReasonerConfiguration;
import org.semanticweb.owlapi.reasoner.SimpleConfiguration;

import com.calculation_engine.oquareMetrics.*;

public class OQuaRE {

        public static class Scores {
                public double ANOnto, AROnto, CBOnto, CROnto, DITOnto, INROnto, LCOMOnto, NACOnto, NOCOnto, NOMOnto,
                                POnto,
                                PROnto, RFCOnto, RROnto, TMOnto, WMCOnto;
                public double modularityScore, reusabilityScore, analysabilityScore, changeabilityScore,
                                modificationStabilityScore, testabilityScore;

                @Override
                public String toString() {
                        return String.format(
                                        "==============================================\n" +
                                                        "ANOnto: %.2f\nAROnto: %.2f\nCBOnto: %.2f\nCROnto: %.2f\nDITOnto: %.2f\nINROnto: %.2f\nLCOMOnto: %.2f\n"
                                                        +
                                                        "NACOnto: %.2f\nNOCOnto: %.2f\nNOMOnto: %.2f\nPOnto: %.2f\nPROnto: %.2f\nRFCOnto: %.2f\nRROnto: %.2f\n"
                                                        +
                                                        "TMOnto: %.2f\nWMCOnto: %.2f",
                                        ANOnto, AROnto, CBOnto, CROnto, DITOnto, INROnto, LCOMOnto, NACOnto, NOCOnto,
                                        NOMOnto, POnto,
                                        PROnto, RFCOnto, RROnto, TMOnto, WMCOnto);
                }
        }

        public static Scores calculateScores(OWLOntology ontology) {
                Scores scores = new Scores();
                try {
                        // Create and run reasoner
                        ConsoleProgressMonitor progressMonitor = new ConsoleProgressMonitor();
                        OWLReasonerConfiguration config = new SimpleConfiguration(progressMonitor);
                        OWLReasoner reasoner = new ReasonerFactory().createReasoner(ontology, config);

                        // Check consistency
                        if (!reasoner.isConsistent()) {
                                throw new RuntimeException("Ontology is inconsistent");
                        }

                        // Precompute inferences
                        reasoner.precomputeInferences();

                        // Calculate individual metrics
                        scores.ANOnto = new ANOntoCalculator().calculate(ontology);
                        scores.AROnto = new AROntoCalculator().calculate(ontology);
                        scores.CBOnto = new CBOntoCalculator().calculate(ontology);
                        // scores.CBOnto2 = new CBOnto2Calculator().calculate(ontology);
                        scores.CROnto = new CROntoCalculator().calculate(ontology);
                        scores.DITOnto = new DITOntoCalculator().calculate(ontology);
                        scores.INROnto = new INROntoCalculator().calculate(ontology);
                        scores.LCOMOnto = new LCOMOntoCalculator().calculate(ontology);
                        scores.NACOnto = new NACOntoCalculator().calculate(ontology);
                        scores.NOCOnto = new NOCOntoCalculator().calculate(ontology);
                        scores.NOMOnto = new NOMOntoCalculator().calculate(ontology);
                        scores.POnto = new POntoCalculator().calculate(ontology);
                        scores.PROnto = new PROntoCalculator().calculate(ontology);
                        scores.RFCOnto = new RFCOntoCalculator().calculate(ontology);
                        scores.RROnto = new RROntoCalculator().calculate(ontology);
                        scores.TMOnto = new TMOntoCalculator().calculate(ontology);
                        // scores.TMOnto2 = new TMOnto2Calculator().calculate(ontology);
                        scores.WMCOnto = new WMCOntoCalculator().calculate(ontology);
                        // scores.WMCOnto2 = new WMCOnto2Calculator().calculate(ontology);
                        // Calculate composite scores

                        scores.modularityScore = scores.CBOnto + scores.WMCOnto;
                        scores.reusabilityScore = scores.WMCOnto + scores.RFCOnto + scores.NOMOnto + scores.CBOnto
                                        + scores.DITOnto
                                        - scores.NOCOnto;
                        scores.analysabilityScore = scores.WMCOnto + scores.RFCOnto + scores.NOMOnto
                                        + scores.LCOMOnto + scores.CBOnto + scores.DITOnto;
                        scores.changeabilityScore = scores.WMCOnto + scores.DITOnto + scores.NOCOnto
                                        + scores.RFCOnto + scores.NOMOnto + scores.CBOnto + scores.LCOMOnto;
                        scores.modificationStabilityScore = scores.WMCOnto + scores.NOCOnto + scores.RFCOnto
                                        + scores.CBOnto + scores.LCOMOnto;
                        scores.testabilityScore = scores.WMCOnto + scores.DITOnto + scores.RFCOnto
                                        + scores.NOMOnto + scores.CBOnto + scores.LCOMOnto;

                        // Don't forget to dispose the reasoner
                        reasoner.dispose();

                } catch (Exception e) {
                        System.err.println("Error calculating metrics: " + e.getMessage());
                        throw new RuntimeException("Failed to calculate metrics", e);
                }

                return scores;
        }
}
