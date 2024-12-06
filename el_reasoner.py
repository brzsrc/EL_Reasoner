from py4j.java_gateway import JavaGateway
from py4j.java_collections import JavaArray, JavaObject, JavaSet
from typing import List, Dict, Optional, cast, Callable, Set, Tuple
import utils

# connect to the java gateway of dl4python
gateway = JavaGateway()

# get a parser from OWL files to DL ontologies
parser = gateway.getOWLParser()

# get a formatter to print in nice DL format
formatter = gateway.getSimpleDLFormatter()

# Creating EL concepts and axioms
elFactory = gateway.getELFactory()

DEBUG = False

def printDebug(s):
    if DEBUG:
        print(formatter.format(s))

class Individual:
    idx: int
    init_concept: JavaObject
    concepts: set[JavaObject]
    #set[(role, individual_idx)]
    #add the role and the the individual it points to
    relatesTo: set[Tuple[JavaObject, int]]

    def __init__(self, idx: int, init_concept:JavaObject):
        self.concepts = {init_concept} # A set of concepts applicable to this individual
        self.relatesTo = set() # All other individuals this individual points to
        self.idx = idx
        self.init_concept = init_concept

    def get_init_concept(self)->JavaObject:
        return self.init_concept

    def get_idx(self) -> int:
        return self.idx
    
    def get_concepts(self) -> set[JavaObject]:
        return self.concepts
    
    def get_relations(self) -> set[Tuple[JavaObject, int]]:
        return self.relatesTo
    
    def add_concept(self, concept:JavaObject) -> bool:
        if concept not in self.concepts:
            self.concepts.add(concept)
            return True
        return False
    
    def add_relation(self, role:JavaObject, successor_idx:int) -> bool:
        if (role, successor_idx) not in self.relatesTo:
            self.relatesTo.add((role, successor_idx))
            return True
        return False
    
    def contain_concept(self, concept:JavaObject) -> bool:
        # for concept in self.concepts:
        #     printDebug(concept)
        if concept in self.concepts:
            return True
        # print(self.idx)
        return False

    def __str__(self) -> str:
        ret = utils.bold("INDIVIDUAL \"" + str(self.idx) + "\"\n")

        ret += utils.colorText(utils.color.CYAN, "\tconcepts: ")
        for idx, c in enumerate(self.concepts):
            if idx != 0:
                ret += ", " + formatter.format(c)
            else:
                ret += formatter.format(c)
        ret += "\n"

        ret +=  utils.colorText(utils.color.CYAN, "\trelatesTo: ")
        for idx, (r, s_idx) in enumerate(self.relatesTo):
            if idx != 0:
                ret += ", " + formatter.format(r) + "." + str(s_idx)
            else:
                ret += formatter.format(r) + "." + str(s_idx)
        ret += "\n"

        return ret


class EL_Reasoner:
    axioms: JavaSet
    allConcepts: JavaSet
    individuals: Set[Individual]

    def __init__(self, allConcepts: JavaSet, axioms: JavaSet):
        self.axioms = axioms
        self.allConcepts = allConcepts
        self.individuals = set()

    def get_individuals(self) -> Set[Individual]:
        return self.individuals

    def get_individual_by_init_conpect(self, init_concept: JavaObject) -> Individual:
        for individual in self.individuals:
            if individual.get_init_concept() == init_concept:
                return individual
        return None

    def get_individual_by_idx(self, idx: int) -> Individual:
        for individual in self.individuals:
            if individual.get_idx() == idx:
                return individual
        return None

    def get_individual_by_concept(self, concept: JavaObject) -> Individual:
        for individual in self.individuals:
            if individual.contain_concept(concept):
                return individual
        return None

    def convert_equivalence_axiom_to_gci(self, axiom:JavaObject) -> JavaObject:
        gci1 = elFactory.getGCI(axiom.getConcepts()[0],axiom.getConcepts()[1])
        gci2 = elFactory.getGCI(axiom.getConcepts()[1],axiom.getConcepts()[0])
        return gci1, gci2


    def _apply_true_rule(self, individual:Individual) -> bool:
        top = elFactory.getTop()
        return individual.add_concept(top)
            

    def _apply_concept_conjunction_rule1(self, individual:Individual , concept:JavaObject) -> bool:
        if individual.contain_concept(concept):
            res = True
            for conjunct in concept.getConjuncts():
                res = res & individual.add_concept(conjunct)
            return res
        return False


    def _apply_concept_conjunction_rule2(self, individual:Individual , conjunct_concpet:JavaObject) -> bool:
        conjunct1, conjunct2 = [conjunct for conjunct in conjunct_concpet.getConjuncts()]
        if individual.contain_concept(conjunct1) and individual.contain_concept(conjunct2):
            return individual.add_concept(conjunct_concpet)
        return False

    def _apply_existential_role_restriction_rule1(self, individual:Individual, role_concept:JavaObject) -> bool:
        role = role_concept.role()
        concept = role_concept.filler()
        if individual.contain_concept(role_concept):
            successor = self.get_individual_by_init_conpect(concept)
            if successor:
                return individual.add_relation(role, successor.get_idx())
            else:
                idx = len(self.individuals) + 1
                new_successor =  Individual(idx, concept)
                self.individuals.add(new_successor)
                return individual.add_relation(role, new_successor.get_idx())   
        return False


    def _apply_existential_role_restriction_rule2(self, individual:Individual, role_concept:JavaObject) -> bool:
        role = role_concept.role()
        concept = role_concept.filler()
        successor = self.get_individual_by_concept(concept)
        if successor:
            successor_idx = successor.get_idx()
        else:
            return False
        relations = individual.get_relations()
        for r, individual_idx in relations:
            if r == role and individual_idx == successor_idx:
                return individual.add_concept(role_concept)
        return False


    def _apply_GCI_rule(self, individual:Individual, gci_axiom:JavaObject) -> bool:
        lhs_concept = gci_axiom.lhs()
        printDebug(lhs_concept)
        # print(lhs_concept.toString())
        # margherita = elFactory.getConceptName('"Margherita"')
        # if margherita == lhs_concept:
            # for c in individual.get_concepts():
                # print("aaaaaaaa")
                # printDebug(c)
        rhs_concept = gci_axiom.rhs()
        printDebug(rhs_concept)
        if individual.contain_concept(lhs_concept):
            return individual.add_concept(rhs_concept)
        return False
    
    def apply_el_algo(self, init_concept:JavaObject):
        init_individual = Individual(1, init_concept)
        self.individuals.add(init_individual)
        changed = True
        while changed:
            changed = False
            for individual in list(self.individuals):
                for concept in self.allConcepts:
                    # printDebug(concept)
                    conceptType = concept.getClass().getSimpleName()
                    if(conceptType == "TopConcept$"):
                        changed = changed or self._apply_true_rule(individual)
                    elif(conceptType == "ConceptConjunction"):
                        changed = changed or self._apply_concept_conjunction_rule1(individual, concept)
                        changed = changed or self._apply_concept_conjunction_rule2(individual, concept)
                    elif(conceptType == "ExistentialRoleRestriction"):
                        changed = changed or self._apply_existential_role_restriction_rule1(individual, concept)
                        changed = changed or self._apply_existential_role_restriction_rule2(individual, concept)

                for axiom in self.axioms:
                    # printDebug(axiom)
                    axiomType = axiom.getClass().getSimpleName() 

                    if(axiomType == "GeneralConceptInclusion"):
                        # printDebug(axiom)
                        changed = changed or self._apply_GCI_rule(individual, axiom)
                    elif(axiomType == "EquivalenceAxiom"):
                        gci_axiom1, gci_axiom2 = self.convert_equivalence_axiom_to_gci(axiom)
                        changed = changed or self._apply_GCI_rule(individual, gci_axiom1)
                        changed = changed or self._apply_GCI_rule(individual, gci_axiom2)
    
    def get_subsumers(self, concept: JavaObject) -> list:
        for individual in self.individuals:
            if individual.get_init_concept() == concept:
                return list(map(formatter.format, list(individual.get_concepts())))
        return None
        




def main():
    # ontology = parser.parseFile("ABCD.owx")
    ontology = parser.parseFile("pizza.owl")

    # Simplify Conjunctions to two members
    gateway.convertToBinaryConjunctions(ontology)
    
    # get all concepts and axioms occurring in the ontology
    allConcepts = ontology.getSubConcepts()
    allAxioms = ontology.tbox().getAxioms()

    conceptD = elFactory.getConceptName('"Margherita"')
    # conceptD = elFactory.getConceptName("C")
    el_reasoner = EL_Reasoner(allConcepts, allAxioms)
    ind = el_reasoner.apply_el_algo(conceptD)
    for ind in el_reasoner.get_individuals():
        print(ind)
    
    subsumers = el_reasoner.get_subsumers(conceptD)
    if subsumers:
        print(subsumers)

if __name__ == '__main__':
    main()
    




