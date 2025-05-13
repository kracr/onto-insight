package com.calculation_engine;

public class SubcharacteristicsCalculator {
        public static class Scores {
                public double formalRelationsSupport;
                public double redundancy;
                public double tangledness;
                public double cohesion;
                public double controlledVocabulary;
                public double schemaValueReconciliation;
                public double consistentSearchQuery;
                public double knowledgeAcquisition;
                public double clustering;
                public double similarity;
                public double indexingLinking;
                public double resultRepresentation;
                public double guidance;
                public double decisionTrees;
                public double knowledgeReuse;
                public double inference;
                public double replaceability;
                public double adaptability;
                public double learnability;
                public double modularity;
                public double reusability;
                public double analyzability;
                public double changeability;
                public double modificationStability;

                @Override
                public String toString() {
                        return String.format(
                                        "================ Sub-characteristics Scores ================\n" +
                                                        "Formal Relations Support: %.2f\n" +
                                                        "Redundancy: %.2f\n" +
                                                        "Tangledness: %.2f\n" +
                                                        "Cohesion: %.2f\n" +
                                                        "Controlled Vocabulary: %.2f\n" +
                                                        "Schema & Value Reconciliation: %.2f\n" +
                                                        "Consistent Search & Query: %.2f\n" +
                                                        "Knowledge Acquisition: %.2f\n" +
                                                        "Clustering: %.2f\n" +
                                                        "Similarity: %.2f\n" +
                                                        "Indexing & Linking: %.2f\n" +
                                                        "Result Representation: %.2f\n" +
                                                        "Guidance: %.2f\n" +
                                                        "Decision Trees: %.2f\n" +
                                                        "Knowledge Reuse: %.2f\n" +
                                                        "Inference: %.2f\n" +
                                                        "Replaceability: %.2f\n" +
                                                        "Adaptability: %.2f\n" +
                                                        "Learnability: %.2f\n" +
                                                        "Modularity: %.2f\n" +
                                                        "Reusability: %.2f\n" +
                                                        "Analyzability: %.2f\n" +
                                                        "Changeability: %.2f\n" +
                                                        "Modification Stability: %.2f",
                                        formalRelationsSupport, redundancy, tangledness, cohesion,
                                        controlledVocabulary, schemaValueReconciliation, consistentSearchQuery,
                                        knowledgeAcquisition, clustering, similarity, indexingLinking,
                                        resultRepresentation, guidance, decisionTrees, knowledgeReuse,
                                        inference, replaceability, adaptability, learnability, modularity,
                                        reusability, analyzability, changeability, modificationStability);
                }
        }

        public static Scores calculateScores(OQuaRE.Scores metrics) {
                Scores scores = new Scores();

                // Calculate sub-characteristics based on formulas
                scores.formalRelationsSupport = metrics.RROnto;
                scores.redundancy = metrics.ANOnto;
                scores.tangledness = -metrics.TMOnto;
                scores.cohesion = -metrics.LCOMOnto;
                scores.controlledVocabulary = metrics.ANOnto;
                scores.schemaValueReconciliation = metrics.AROnto + metrics.RROnto;
                scores.consistentSearchQuery = metrics.ANOnto + metrics.AROnto + metrics.INROnto + metrics.RROnto;
                scores.knowledgeAcquisition = metrics.ANOnto + metrics.RROnto - metrics.NOMOnto;
                scores.clustering = metrics.ANOnto;
                scores.similarity = metrics.AROnto + metrics.RROnto;
                scores.indexingLinking = metrics.AROnto + metrics.RROnto + metrics.INROnto;
                scores.resultRepresentation = metrics.AROnto + metrics.CROnto;
                scores.guidance = metrics.AROnto + metrics.INROnto;
                scores.decisionTrees = metrics.AROnto + metrics.INROnto - metrics.TMOnto;
                scores.knowledgeReuse = metrics.ANOnto + metrics.AROnto + metrics.INROnto - metrics.NOMOnto
                                - metrics.LCOMOnto;
                scores.inference = metrics.RROnto + metrics.CROnto;
                scores.replaceability = (metrics.DITOnto + metrics.NOCOnto + metrics.NOMOnto + metrics.WMCOnto);
                scores.adaptability = (metrics.CBOnto + metrics.DITOnto + metrics.NOCOnto + metrics.NOMOnto
                                + metrics.RFCOnto
                                + metrics.WMCOnto);
                scores.learnability = (metrics.CBOnto + metrics.NOCOnto + metrics.NOMOnto + metrics.LCOMOnto
                                + metrics.RFCOnto
                                + metrics.WMCOnto);
                scores.modularity = (metrics.CBOnto + metrics.WMCOnto);
                scores.reusability = (metrics.CBOnto + metrics.DITOnto + metrics.NOCOnto + metrics.NOMOnto
                                + metrics.RFCOnto
                                + metrics.WMCOnto);
                scores.analyzability = (metrics.CBOnto + metrics.DITOnto + metrics.NOMOnto + metrics.LCOMOnto
                                + metrics.RFCOnto
                                + metrics.WMCOnto);
                scores.changeability = (metrics.CBOnto + metrics.DITOnto + metrics.NOCOnto + metrics.NOMOnto
                                + metrics.LCOMOnto
                                + metrics.RFCOnto + metrics.WMCOnto);
                scores.modificationStability = (metrics.CBOnto + metrics.NOCOnto + metrics.LCOMOnto + metrics.RFCOnto);

                return scores;
        }
}