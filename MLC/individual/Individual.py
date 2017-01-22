import numpy as np
import math

from collections import Counter
from MLC.mlc_parameters.mlc_parameters import Config
from MLC.Common.Operations import Operations
from MLC.Common.Lisp_Tree_Expr.Lisp_Tree_Expr import Lisp_Tree_Expr
from MLC.Common.RandomManager import RandomManager


class IndividualException(Exception):
    pass


class OperationOverIndividualFail(IndividualException):
    def __init__(self, individual_value, operation_name, cause):
        IndividualException.__init__(self, "Operation '%s' over individual '%s' fail due %s" % (operation_name, individual_value, cause) )


class TreeException(Exception):
    pass


class Individual(object):
    """
    MLCind constructor of the Machine Learning Control individual class.
    Part of the MLC2 Toolbox.

    Implements the individual type, value and costs. Archives history of
    evaluation and other informations.

    This class requires a valid MLCparameters object for most of its
    functionnalities.

    MLCind properties:
        type:
            type of individual (expression trees only now)
        value:
            string or matrice representing the individual in the representation
            considered in 'type'
        formal:
            matlab interpretable expression of the individual
        complexity:
            weighted addition of operators

    MLCind methods:
        generate:
            creates one indiv according to the current MLCparameters object
            and type of individual.
        evaluate:
            evaluates one individual according to the current MLCparameters
            object.
        mutate:
            mutates one individual according to the current MLCparameters
            object and type of indiv.
        crossover:
            crosses two indiv according to the current MLCparameters object
            and type of individuals.
        compare:
            stricly compares two individuals' values
        textoutput:
            display indiviudal value as text string
        preev:
            calls preevaluation function

    See also MLCPARAMETERS, MLCTABLE, MLCPOP, MLC2
    """
    class MutationType:
        ANY = 0
        REMOVE_SUBTREE_AND_REPLACE = 1
        REPARAMETRIZATION = 2
        HOIST = 3
        SHRINK = 4

    _maxdepthfirst = None

    def __init__(self, value, formal=None, complexity=None):
        self._config = Config.get_instance()

        # Tree expression initialized using lazing initialization through
        # _tree property. Use self._tree instead of self._lazy_tree to
        # obtain the tree expression.
        self._lazy_tree = None
        self._value = value

        if formal is not None and complexity is not None:
            self._formal = formal
            self._complexity = complexity
        else:
            self._formal = self._tree.formal()
            self._complexity = self._tree.complexity()

        self._range = self._config.getint("POPULATION", "range")
        self._precision = self._config.getint("POPULATION", "precision")

    @property
    def _tree(self):
        if self._lazy_tree is None:
            self._lazy_tree = Lisp_Tree_Expr(self.get_value())
        return self._lazy_tree

    @staticmethod
    def set_maxdepthfirst(value):
        Individual._maxdepthfirst = value

    def mutate(self, mutation_type=MutationType.ANY):
        try:
            new_value = self.__mutate_tree(mutation_type)
            return Individual(new_value)

        except TreeException, ex:
            raise OperationOverIndividualFail(self._value, "MUTATE", str(ex))

    def crossover(self, other_individual):
        """
            CROSSOVER crosses two MLCind individuals.
            [NEW_IND1,NEW_IND2,FAIL]=CROSSOVER(MLCIND1,MLCIND2,MLC_PARAMETERS)
        """
        try:
            new_value_1, new_value_2 = self.__crossover_tree(other_individual)
            return Individual(new_value_1), Individual(new_value_2)

        except TreeException, ex:
            raise OperationOverIndividualFail(self._value, "CROSSOVER", str(ex))

    def compare(self, other_individual):
        return self.get_value() == other_individual.get_value()

    def get_value(self):
        return self._value

    def set_value(self, value):
        self._value = value

    def get_formal(self):
        return self._formal

    def set_formal(self, formal):
        self._formal = formal

    def get_complexity(self):
        return self._complexity

    def set_complexity(self, complexity):
        self._complexity = complexity

    def get_tree(self):
        return self._tree

    def __crossover_tree(self, other_individual):
        """
            Extract a subtree out of a tree, extract a correct subtree out of
            another tree (with depth that can fit into maxdepth).
            Then interchange the two subtrees inputs:

            :return: (first new tree, second new tree) as strings
        """
        maxtries = self._config.getint("GP", "maxtries")
        mutmindepth = self._config.getint("GP", "mutmindepth")
        maxdepth = self._config.getint("GP", "maxdepth")

        correct = False
        count = 0

        while not correct and count < maxtries:
            try:
                # Extracting subtrees
                value_1, sm1, n = self.__extract_subtree(self.get_tree(), mutmindepth, maxdepth, maxdepth)
                value_2, sm2, _ = self.__extract_subtree(other_individual.get_tree(), mutmindepth, n, maxdepth - n + 1)
                correct = True

            except TreeException, ex:
                pass

            count += 1

        if not correct:
            raise TreeException("we could not find a candidate substitution in %s tests" % maxtries)

        # Replacing subtrees
        value_1 = value_1.replace('@', sm2)
        value_2 = value_2.replace('@', sm1)

        # TODO preevaluation over value_1 and value_2

        return value_1, value_2

    def __mutate_tree(self, mutation_type):
        mutmindepth = self._config.getint("GP", "mutmindepth")
        maxdepth = self._config.getint("GP", "maxdepth")
        sensor_spec = self._config.getboolean("POPULATION", "sensor_spec")
        sensors = self._config.getint("POPULATION", 'sensors')
        mutation_types = self._config.get_list("GP", 'mutation_types')

        # equi probability for each mutation type selected.
        if mutation_type == Individual.MutationType.ANY:
            rand_number = RandomManager.rand()
            mutation_type = mutation_types[int(np.floor(rand_number * len(mutation_types)))]

        if mutation_type in [Individual.MutationType.REMOVE_SUBTREE_AND_REPLACE, Individual.MutationType.SHRINK]:
            new_individual_value = None
            preevok = False
            while not preevok:
                # remove subtree and grow new subtree
                try:
                    subtree, _, _ = self.__extract_subtree(self._tree, mutmindepth, maxdepth, maxdepth)
                    if mutation_type == Individual.MutationType.REMOVE_SUBTREE_AND_REPLACE:
                        next_individual_type = 0
                    else:
                        next_individual_type = 4

                    new_individual_value = Individual.__generate_indiv_regressive_tree(subtree, self._config, next_individual_type)

                    if new_individual_value:
                        if sensor_spec:
                            config_sensor_list = sorted(self._config.get_list('POPULATION', 'sensor_list'))
                        else:
                            config_sensor_list = range(sensors - 1, -1, -1)

                        for i in range(len(config_sensor_list)):
                            new_individual_value = new_individual_value.replace("z%d" % i, "S%d" % config_sensor_list[i])

                except TreeException:
                    pass

                preevok = True

            if not new_individual_value:
                raise TreeException("Subtree cannot be generated")

            return new_individual_value

        elif mutation_type == Individual.MutationType.REPARAMETRIZATION:
            return self.__reparam_tree(Lisp_Tree_Expr(self.get_value()))

        elif mutation_type == Individual.MutationType.HOIST:
            controls = self._config.getint("POPULATION", "controls")
            prob_threshold = 1 / float(controls)

            cl = [stree.to_string() for stree in self.get_tree().get_root_node()._nodes]

            changed = False
            k = 0

            for nc in RandomManager.randperm(controls):
                k += 1
                # control law is cropped if it is the last one and no change happend before
                if (RandomManager.rand() < prob_threshold) or (k == controls and not changed):

                    try:
                        _, sm, _ = self.__extract_subtree(Lisp_Tree_Expr('(root '+cl[nc - 1]+')'), mutmindepth+1, maxdepth, maxdepth+1)
                        cl[nc - 1] = sm
                        changed = True

                    except TreeException:
                        changed = False

            return "(root %s)" % " ".join(cl[:controls])

        else:
            raise NotImplementedError("Mutation type %s not implemented" % mutation_type)

    def __extract_subtree(self, expression_tree, mindepth, subtreedepthmax, maxdepth):
        candidates = []
        for node in expression_tree.internal_nodes():
            if mindepth <= node.get_depth() <= maxdepth:
                if node.get_subtreedepth() <= subtreedepthmax:
                    candidates.append(node)

        if not candidates:
            raise TreeException("No subtrees to extract from '%s' "
                                "with mindepth=%s, maxdepth=%s, subtreedepthmax=%s" %
                                (expression_tree, mindepth, maxdepth, subtreedepthmax))

        candidates.sort(key=lambda x: x.get_expr_index(), reverse=False)
        n = int(np.ceil(RandomManager.rand() * len(candidates))) - 1
        extracted_node = candidates[n]
        index = extracted_node.get_expr_index()
        old_value = expression_tree.get_expanded_tree_as_string()
        new_value = old_value[:index] + old_value[index:].replace(extracted_node.to_string(), '@', 1)
        return new_value, extracted_node.to_string(), extracted_node.get_subtreedepth()

    def __reparam_tree(self, tree_expression):
        def leaf_value_generator():
            leaf_value = (RandomManager.rand() - 0.5) * 2 * self._range
            return "%0.*f" % (self._precision, leaf_value)

        return self.__change_const_tree(tree_expression, leaf_value_generator)

    def __change_const_tree(self, tree_expression, leaf_value_generator):
        for leaf in tree_expression.leaf_nodes():
            if not leaf.is_sensor():
                leaf._arg = leaf_value_generator()
        return tree_expression.get_expanded_tree_as_string()

    def __str__(self):
        return "value: %s\n" % self.get_value() + \
               "formal: %s\n" % self.get_formal() + \
               "complexity: %s\n" % self.get_complexity()

    # Individual creation
    @staticmethod
    def generate(config, individual_type=None, rhs_value=None):
        """
            generate individual from scratch
            MLCIND.generate(MLC_PARAMETERS,MODE) creates an individual using
            mode MODE. MODE is a number which interpretation depends on the
            MLCIND.type property.
        """
        value = None
        if rhs_value is None:
            controls = config.getint('POPULATION', 'controls')
            value = '(root%s)' % (' @' * controls)
            for i in range(controls):
                value = Individual.__generate_indiv_regressive_tree(value, config, individual_type)
        else:
            value = rhs_value

        value = Individual.__simplify_and_sensors_tree(value, config)
        return Individual(value)

    @staticmethod
    def __generate_indiv_regressive_tree(value, config, indiv_type):
        min_depth = 0
        max_depth = 0
        new_value = ""

        # Maxdepthfirst change while we are creating the first population
        if indiv_type:
            if indiv_type == 1:
                min_depth = Individual._maxdepthfirst
                max_depth = Individual._maxdepthfirst
            elif indiv_type == 2 or indiv_type == 3:
                min_depth = int(config.get('GP', 'mindepth'))
                max_depth = Individual._maxdepthfirst
            elif indiv_type == 4:
                min_depth = int(config.get('GP', 'mindepth'))
                max_depth = 1
            else:
                min_depth = int(config.get('GP', 'mindepth'))
                max_depth = int(config.get('GP', 'maxdepth'))

        else:
            min_depth = int(config.get('GP', 'mindepth'))
            max_depth = int(config.get('GP', 'maxdepth'))

        # Check if the seed character is in the string
        index = value.find('@')
        if index == -1:
            return

        # Split the value in two strings, not containing the first seed character
        begin_str = value[:index]
        end_str = value[index + 1:]

        # Count the amounts of '(' until the first seed character (This is the depth of the seed)
        counter = Counter(begin_str)
        begin_depth = counter['('] - counter[')']

        leaf_node = False
        if begin_depth >= max_depth:
            leaf_node = True
        elif (begin_depth < min_depth and end_str.find(
                '@') == -1) or indiv_type == 3:
            leaf_node = False
        else:
            leaf_node = RandomManager.rand() < config.getfloat(
                'POPULATION', 'leaf_prob')

        if leaf_node:
            use_sensor = RandomManager.rand() < config.getfloat(
                'POPULATION', 'sensor_prob')
            if use_sensor:
                sensor_number = math.ceil(RandomManager.rand() * config.getint('POPULATION', 'sensors')) - 1
                new_value = begin_str + 'z' + str(sensor_number).rstrip('0').rstrip('.') + end_str
            else:
                range = config.getfloat('POPULATION', 'range')
                precision = config.get('POPULATION', 'precision')
                # Generate a float number between -range and +range with a precision of 'precision'
                new_exp = (("%." + precision + "f") % (
                (RandomManager.rand() - 0.5) * 2 * range))
                new_value = begin_str + new_exp + end_str
        else:
            # Create a node
            op_num = math.ceil(RandomManager.rand() * Operations.get_instance().length())
            op = Operations.get_instance().get_operation_from_op_num(op_num)
            if (op["nbarg"] == 1):
                new_value = begin_str + '(' + op["op"] + ' @)' + end_str
                new_value = Individual.__generate_indiv_regressive_tree(new_value, config, indiv_type)
            else:
                # nbrag == 2
                new_value = begin_str + '(' + op["op"] + ' @ @)' + end_str
                new_value = Individual.__generate_indiv_regressive_tree(new_value, config, indiv_type)
                new_value = Individual.__generate_indiv_regressive_tree(new_value, config, indiv_type)
        return new_value

    @staticmethod
    def __simplify_and_sensors_tree(value, config):
        sensor_list = ()
        replace_list = ()

        if config.getboolean('POPULATION', 'sensor_spec'):
            config_sensor_list = sorted(config.get_list('POPULATION', 'sensor_list'))
            sensor_list = ['S' + str(x) for x in config_sensor_list]
            replace_list = ['z' + str(x) for x in range(len(config_sensor_list))]
        else:
            amount_sensors = config.getint('POPULATION', 'sensors')
            # Replace the available sensors in the individual expression
            sensor_list = ['S' + str(x) for x in range(amount_sensors)]
            replace_list = ['z' + str(x) for x in range(amount_sensors)]

        for i in range(len(replace_list)):
            value = value.replace(replace_list[i], sensor_list[i])

        if config.getboolean('OPTIMIZATION', 'simplify'):
            return Lisp_Tree_Expr(value).get_simplified_tree_as_string()

        return value

    def __cmp__(self, other):
        self._value == other.get_value()

    def __hash__(self):
        return hash(self._value)