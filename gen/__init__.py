import generator as gen
import edf_generators as edf
import run_generators as run

# gen.register_generator("G-EDF", edf.GedfGenerator)
# gen.register_generator("P-EDF", edf.PedfGenerator)
# gen.register_generator("C-EDF", edf.CedfGenerator)
gen.register_generator("RUN", run.RUNGenerator)
gen.register_generator_resources("RUN_SBLP", run.RUNGeneratorRes)
gen.register_generator_resources("RUN_MrsP", run.RUNGeneratorMrsP)
gen.register_generator_resources("RUN_SBLP_OBT", run.RUNGeneratorSBLP_OBT)
# gen.register_generator_resources("RUN_Comparativo", run.RUNGeneratorComparativo)
