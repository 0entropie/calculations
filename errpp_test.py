import random, unittest, math, functools
import abc
import errpp
import operator

def random_val_and_abs_error(min = -100, max = 100, max_rel_err_factor = 1):
    value = random.uniform(min, max)
    abs_error = random.uniform(0, abs(value) * max_rel_err_factor)
    return (value, abs_error)


def vwe_from_val_abs_err_pair(propmethod, val_err_pair):
    return errpp.ValueWithError.from_val_abs_err_pair(*val_err_pair, propmethod())


def vwes_from_errtype_list_and_val_abs_err_pair(errtypelist, val_err_pair):
    return map(lambda et: vwe_from_val_abs_err_pair(et, val_err_pair), errtypelist)


def vwes_with_random_vals_errs(errtype, n=2):
    # closure, deal with it.
    def vwe_from_pair_fixed_type(val_err_pair):
        return vwe_from_val_abs_err_pair(errtype, val_err_pair)

    val_err_pairs = (random_val_and_abs_error() for i in range(n))
    return map(vwe_from_pair_fixed_type, val_err_pairs)


def perform_binary_op_on_vwes(left_vwes, right_vwes, op):
    return map(lambda xy: op(*xy), zip(left_vwes, right_vwes))


_TRIALS = 100000

def _relation_binary_op_test(operation):
    def wrapper(method):
        def perform_binary_op_test(self):
            for left, right in zip(self.left_vwes, self.right_vwes):
                l, k, m = tuple(perform_binary_op_on_vwes(left, right, operation))
                method(self, l, k, m)
        return perform_binary_op_test
    return wrapper

class RelationTest(unittest.TestCase):

    __error_order_list = [errpp.WorstCasePropogation,
                          errpp.StatisticalPropagation,
                          errpp.ExtremePropagation]

    def setUp(self):
        self.left_vwes = (vwes_from_errtype_list_and_val_abs_err_pair(
                                self.__error_order_list,
                                random_val_and_abs_error())
                          for _ in range(_TRIALS))

        self.right_vwes = (vwes_from_errtype_list_and_val_abs_err_pair(
                               self.__error_order_list,
                               random_val_and_abs_error())
                           for _ in range(_TRIALS))


    @_relation_binary_op_test(operator.add)
    def test_add_error_strict_estimation_order(self, l, k, m):
        self.assertEqual(k.value, l.value)
        self.assertEqual(l.value, m.value)

        self.assertLessEqual(abs(k.abs_err), abs(l.abs_err))
        self.assertLessEqual(abs(l.abs_err), abs(m.abs_err))

    @_relation_binary_op_test(operator.sub)
    def test_sub_error_strict_estimation_order(self, l, k, m):
        self.assertEqual(k.value, l.value)
        self.assertEqual(l.value, m.value)

        self.assertLessEqual(abs(k.abs_err), abs(l.abs_err))
        self.assertLessEqual(abs(l.abs_err), abs(m.abs_err))

    @_relation_binary_op_test(operator.mul)
    def test_mul_error_strict_estimation_order(self, l, k, m):
        self.assertEqual(k.value, l.value)
        self.assertEqual(l.value, m.value)

        self.assertLessEqual(k.abs_err, l.abs_err)
        self.assertLessEqual(l.abs_err, m.abs_err)

    @_relation_binary_op_test(operator.truediv)
    def test_div_error_strict_estimation_order(self, l, k, m):
        self.assertEqual(k.value, l.value)
        self.assertEqual(l.value, m.value)

        self.assertLessEqual(k.abs_err, l.abs_err, "is")
        self.assertLessEqual(l.abs_err, m.abs_err, "as")

def _binary_op_propagation_test(operation):
    def wrapper(method):
        def perform_binary_op_test(self):
            for a, b in zip(self.lefts, self.rights):
                self.expected_val = operation(a.value, b.value)
                self.calculated = operation(a, b)
                method(self, a, b)
                self.compare_values_and_errors()
        return perform_binary_op_test
    return wrapper

class ErrorClassTest(unittest.TestCase, abc.ABC):

    @abc.abstractmethod
    def getErrorType(self):
        pass

    def setUp(self):
        self.lefts = (vwe_from_val_abs_err_pair(self.getErrorType(), random_val_and_abs_error()) for _ in range(_TRIALS))
        self.rights = (vwe_from_val_abs_err_pair(self.getErrorType(), random_val_and_abs_error()) for _ in range(_TRIALS))

    def round_dec(self, n, decs = 5):
        return round(n, decs)


    def compare_values_and_errors(self):
        self.assertEqual(self.round_dec(self.expected_val), self.round_dec(self.calculated.value))
        self.assertEqual(self.round_dec(abs(self.expected_error)), self.round_dec(self.calculated.abs_err))

    @_binary_op_propagation_test(operator.sub)
    def tst_neg(self, a, b):
        # overwrite preset values by decorator
        self.expected_val = -a.value
        self.expected_error = a.abs_err
        self.calculated = -a


class StatisticalErrorTest(ErrorClassTest):

    def getErrorType(self):
        return errpp.StatisticalPropagation

    test_negation = ErrorClassTest.tst_neg

    @_binary_op_propagation_test(operator.add)
    def test_StatisticalError_add_error_correctness(self, a, b):
            self.expected_error = math.sqrt(a.abs_err**2 + b.abs_err**2)

    @_binary_op_propagation_test(operator.sub)
    def test_StatisticalError_sub_error_correctness(self, a, b):
        self.expected_error = math.sqrt(a.abs_err**2 + b.abs_err**2)

    @_binary_op_propagation_test(operator.mul)
    def test_StatisticalError_mul_error_correctness(self, a, b):
        self.expected_error = self.expected_val * math.sqrt(a.rel_err**2 + b.rel_err**2)

    @_binary_op_propagation_test(operator.truediv)
    def test_StatisticalError_div_error_correctness(self, a, b):
        self.expected_error = self.expected_val * math.sqrt(a.rel_err**2 + b.rel_err**2)


class WorstCaseErrorTest(ErrorClassTest):

    def getErrorType(self):
        return errpp.WorstCasePropogation

    test_negation = ErrorClassTest.tst_neg

    @_binary_op_propagation_test(operator.add)
    def test_WorstCaseError_add_error_correctness(self, a, b):
        self.expected_error = a.abs_err + b.abs_err

    @_binary_op_propagation_test(operator.sub)
    def test_WorstCaseError_sub_error_correctness(self, a, b):
        self.expected_error = a.abs_err + b.abs_err

    @_binary_op_propagation_test(operator.mul)
    def test_WorstCaseError_mul_error_correctness(self, a, b):
        self.expected_error = self.expected_val * (a.rel_err + b.rel_err)

    @_binary_op_propagation_test(operator.truediv)
    def test_WorstCaseError_div_error_correctness(self, a, b):
        self.expected_error = (a.rel_err + b.rel_err) * self.expected_val


class ExtremeErrorTest(ErrorClassTest):

    def getErrorType(self):
        return errpp.ExtremePropagation
    
    test_negation = ErrorClassTest.tst_neg

    @_binary_op_propagation_test(operator.add)
    def test_ExtremeError_add_error_correctness(self, a, b):
        self.expected_error = a.abs_err + b.abs_err


    @_binary_op_propagation_test(operator.sub)
    def test_ExtremeError_sub_error_correctness(self, a, b):
        self.expected_error = a.abs_err + b.abs_err


    @_binary_op_propagation_test(operator.mul)
    def test_ExtremeError_mul_error_correctness(self, a, b):
        self.expected_error = self.expected_val * (a.rel_err + b.rel_err + a.rel_err * b.rel_err)

    @_binary_op_propagation_test(operator.truediv)
    def test_ExtremeError_div_error_correctness(self, a, b):
        lim1 = (abs(a.value) + a.abs_err) / (abs(b.value) - b.abs_err) - abs(self.expected_val)
        lim2 = (abs(a.value) - a.abs_err) / (abs(b.value) + b.abs_err) - abs(self.expected_val)
        # makes 0 fucking sense to me, how can there be a choice here when there is no choice in the impl...
        self.expected_error = max(lim1, lim2)

class ErrorPropagation(unittest.TestSuite):

    def __init__(self):
        self.addTests((RelationTest(), StatisticalErrorTest(), ExtremeErrorTest(), WorstCaseErrorTest()))


if __name__ == '__main__':
    unittest.main()
