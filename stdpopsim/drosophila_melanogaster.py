"""
Genome, genetic map and demographic model definitions for humans.
"""

import msprime

import stdpopsim.models as models
import stdpopsim.genomes as genomes
import stdpopsim.genetic_maps as genetic_maps
import stdpopsim.generic_models as generic_models

###########################################################
#
# Genetic maps
#
###########################################################


class Comeron2012_dm6(genetic_maps.GeneticMap):
    """
    Comeron et al. (2012) maps (lifted over to dm6) used in
    Currently needs a readme as to the lift over, etc.
    """
    url = (
        "http://sesame.uoregon.edu/~adkern/dmel_recombination_map/"
        "comeron2012_maps.tar.gz")
    file_pattern = "genetic_map_comeron2012_dm6_{name}.txt"


genetic_maps.register_genetic_map(Comeron2012_dm6())

###########################################################
#
# Genome definition
#
###########################################################

# List of chromosomes. Data for length information based on DM6,
# https://www.ncbi.nlm.nih.gov/genome/?term=drosophila+melanogaster.
# FIXME: add mean mutation and recombination rate data to this table.
_chromosome_data = """\
chrX   23542271
chr2L   23513712
chr2R   25286936
chr3L   28110227
chr3R   32079331
chr4   1348131
chrY   3667352
chrM   19524
"""

_chromosomes = []
for line in _chromosome_data.splitlines():
    name, length = line.split()[:2]
    _chromosomes.append(genomes.Chromosome(
        name=name, length=int(length),
        default_mutation_rate=8.4e-9,  # WRONG!, underestimate used in S&S
        default_recombination_rate=8.4e-9))  # WRONG, underestimate used in S&S!


#: :class:`stdpopsim.Genome` definition for D. melanogaster. Chromosome length data is
#: based on `dm6 <https://www.ncbi.nlm.nih.gov/assembly/GCF_000001215.4/>`_.
genome = genomes.Genome(
    species="drosophila_melanogaster",
    chromosomes=_chromosomes,
    default_genetic_map=Comeron2012_dm6.name)

genomes.register_genome(genome)

###########################################################
#
# Demographic models
#
###########################################################

default_generation_time = 0.1


# population definitions that are reused.
_afr_population = models.Population(
   name="AFR", description="African D. melanogaster population")
_eur_population = models.Population(
   name="EUR", description="European D. melanogaster population")


class DrosophilaMelanogasterModel(models.Model):
    """
    TODO: documentation
    """
    def __init__(self):
        super().__init__()
        self.generation_time = default_generation_time
        self.default_population_size = 10000


class GenericConstantSize(DrosophilaMelanogasterModel, generic_models.ConstantSizeMixin):
    def __init__(self):
        DrosophilaMelanogasterModel.__init__(self)
        generic_models.ConstantSizeMixin.__init__(self, self.default_population_size)


class GenericTwoEpoch(DrosophilaMelanogasterModel, generic_models.TwoEpochMixin):
    def __init__(self, n2=None, t=None):
        DrosophilaMelanogasterModel.__init__(self)
        n1 = self.default_population_size
        if n2 is None:
            n2 = n1 / 2.0
        if t is None:
            t = n1 / 100
        generic_models.TwoEpochMixin.__init__(self, n1, n2, t)


class SheehanSongThreeEpoch(DrosophilaMelanogasterModel):
    name = "SheehanSongThreeEpoch"
    short_description = "Three epoch model for single African population."
    description = """
        The three epoch (modern, bottleneck, ancestral) model estimated for a
        single African Drosophila Melanogaster population from `Sheehan and Song <https:/
        /doi.org/10.1371/journal.pcbi.1004845>`_ . Population sizes are estimated by a
        deep learning model trained on simulation data. NOTE: Due to differences in
        coalescence units between PSMC (2N) and msms (4N) the number of generations were
        doubled from PSMC estimates when simulating data from msms in the original
        publication. We have faithfully represented the published model here.
    """
    populations = [_afr_population]
    citations = [
        """
        Sheehan, S. & Song, Y. S. Deep Learning for Population Genetic Inference. PLOS
        Computational Biology 12, e1004845 (2016).
        """
    ]
    author = "Sheehan and Song"
    year = 2016
    doi = "https://doi.org/10.1371/journal.pcbi.1004845"

    def __init__(self):
        super().__init__()
        # Parameter values from "Simulating Data" section
        # these are assumptions, not estimates
        N_ref = 100000
        t_1_coal = 0.5
        t_2_coal = 5.0
        # estimates from the ANN
        N_R = 544200
        N_B = 145300
        N_A = 652700
        # Times are provided in 4N_ref generations, so we convert into generations.
        # generation_time = 10 / year
        t_1 = t_1_coal * 4 * N_ref
        t_2 = (t_1_coal + t_2_coal) * 4 * N_ref
        self.generation_time = default_generation_time

        self.population_configurations = [
            msprime.PopulationConfiguration(
                initial_size=N_R, metadata=self.populations[0].asdict())]

        self.demographic_events = [
            # Size change at bottleneck (back in time; BIT)
            msprime.PopulationParametersChange(
                time=t_1, initial_size=N_B, population_id=0),
            # Size change at recovery (BIT)
            msprime.PopulationParametersChange(
                time=t_2, initial_size=N_A, population_id=0)
        ]
        self.migration_matrix = [[0]]


SheehanSongThreeEpoch._write_docstring()


class LiStephanTwoPopulation(DrosophilaMelanogasterModel):
    name = "LiStephanTwoPopulation"
    short_description = "Three epoch model for African and European populations."
    description = """
        The three epoch (modern, bottleneck, ancestral) model estimated for two
        Drosophila Melanogaster populations: African (ancestral) and European (derived)
        from `Li and Stephan <https://doi.org/10.1371/journal.pgen.0020166>`_ .
    """
    populations = [_afr_population, _eur_population]
    citations = [
        """
        Li, H. & Stephan, W. Inferring the Demographic History and Rate of Adaptive
        Substitution in Drosophila. PLOS Genetics 2, e166 (2006).
        """
    ]
    author = "Li et al."
    year = 2006
    doi = "https://doi.org/10.1371/journal.pgen.0020166"

    def __init__(self):
        super().__init__()
        # African Parameter values from "Demographic History of the African
        # Population" section
        N_A0 = 8.603e06
        t_A0 = 600000  # assuming 10 generations / year
        N_A1 = N_A0 / 5.0
        self.generation_time = default_generation_time

        # European Parameter values from "Demo History of Euro Population"
        N_E0 = 1.075e06
        N_E1 = 2200
        t_AE = 158000  # generations
        t_E1 = t_AE - 3400

        self.population_configurations = [
            msprime.PopulationConfiguration(
                initial_size=N_A0, metadata=self.populations[0].asdict()),
            msprime.PopulationConfiguration(
                initial_size=N_E0, metadata=self.populations[1].asdict())
        ]
        self.demographic_events = [
            # Size change at Euro bottleneck
            msprime.PopulationParametersChange(
                time=t_E1, initial_size=N_E1, population_id=1),
            # Split
            msprime.MassMigration(
                time=t_AE, source=1, destination=0, proportion=1.0),
            # African bottleneck
            msprime.PopulationParametersChange(
                time=t_A0, initial_size=N_A1, population_id=0)
        ]
        self.migration_matrix = [
            [0, 0],
            [0, 0],
        ]


LiStephanTwoPopulation._write_docstring()
