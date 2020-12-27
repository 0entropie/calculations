import random, unittest, math, functools
import abc
import errpp
import operator

def random_val_and_abs_error(min = -100, max = 100, max_rel_err_factor = 1):
    value = random.uniform(min,max)
    abs_error = random.uniform(0,abs(value)*max_rel_err_factor)
    return (value, abs_error)


def vwe_from_val_abs_err_pair(errtype, val_err_pair):
    val, abs_err = val_err_pair
    rel_err = abs_err/val
    return errpp.ValueWithError(val, errtype(abs_err, rel_err))


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


class RelationTest(unittest.TestCase):

    __error_order_list = [errpp.WorstCaseError,
                          errpp.StatisticalError,
                          errpp.ExtremeError]

    def setUp(self):
        self.left_vwes = (vwes_from_errtype_list_and_val_abs_err_pair(
                                self.__error_order_list,
                                random_val_and_abs_error())
                          for _ in range(_TRIALS))

        self.right_vwes = (vwes_from_errtype_list_and_val_abs_err_pair(
                               self.__error_order_list,
                               random_val_and_abs_error())
                           for _ in range(_TRIALS))


    def test_add_error_strict_estimation_order(self):
        for left, right in zip(self.left_vwes, self.right_vwes):

            l, k, m = tuple(perform_binary_op_on_vwes(left, right, operator.add))

            self.assertEqual(k.value, l.value)
            self.assertEqual(l.value, m.value)

            self.assertLessEqual(abs(k.error.abs_err), abs(l.error.abs_err))
            self.assertLessEqual(abs(l.error.abs_err), abs(m.error.abs_err))


    def test_sub_error_strict_estimation_order(self):
        for left, right in zip(self.left_vwes, self.right_vwes):

            l, k, m = tuple(perform_binary_op_on_vwes(left, right, operator.sub))

            self.assertEqual(k.value, l.value)
            self.assertEqual(l.value, m.value)

            self.assertLessEqual(abs(k.error.abs_err), abs(l.error.abs_err))
            self.assertLessEqual(abs(l.error.abs_err), abs(m.error.abs_err))


    def test_mul_error_strict_estimation_order(self):
        for left, right in zip(self.left_vwes, self.right_vwes):
            
            l, k, m = tuple(perform_binary_op_on_vwes(left, right, operator.mul))

            self.assertEqual(k.value, l.value)
            self.assertEqual(l.value, m.value)

            self.assertLessEqual(k.error.abs_err, l.error.abs_err)
            self.assertLessEqual(l.error.abs_err, m.error.abs_err)


    def test_div_error_strict_estimation_order(self):
        for left, right in zip(self.left_vwes, self.right_vwes):
            
            l, k, m = tuple(perform_binary_op_on_vwes(left, right, operator.truediv))

            self.assertEqual(k.value, l.value)
            self.assertEqual(l.value, m.value)

            self.assertLessEqual(k.error.abs_err, l.error.abs_err, "is")
            self.assertLessEqual(l.error.abs_err, m.error.abs_err, "as")


class ErrorClassTest(unittest.TestCase, abc.ABC):

    @abc.abstractmethod
    def getErrorType(self):
        pass

    def setUp(self):
        self.lefts = (vwe_from_val_abs_err_pair(self.getErrorType(), random_val_and_abs_error()) for _ in range(_TRIALS))
        self.rights = (vwe_from_val_abs_err_pair(self.getErrorType(), random_val_and_abs_error()) for _ in range(_TRIALS))

    def round_dec(self, n, decs = 5):
        return round(n, decs)


    def compare_values_and_errors(self, expected_val, expected_err, actual):
        self.assertEqual(self.round_dec(expected_val), self.round_dec(actual.value))
        self.assertEqual(self.round_dec(abs(expected_err)), self.round_dec(actual.error.abs_err))


    def tst_neg(self):
        for gen in self.lefts:

            expected_val = -gen.value
            expected_error = gen.error.abs_err
            calculated = -gen

            self.compare_values_and_errors(expected_val, expected_error, calculated)


class StatisticalErrorTest(ErrorClassTest):

    def getErrorType(self):
        return errpp.StatisticalError

    test_negation = ErrorClassTest.tst_neg

    def test_StatisticalError_add_error_correctness(self):
        for a, b in zip(self.lefts, self.rights):
            expected_val = a.value + b.value
            expected_error = math.sqrt(a.error.abs_err**2 + b.error.abs_err**2)
            calculated = a + b

            self.compare_values_and_errors(expected_val, expected_error, calculated)


    def test_StatisticalError_sub_error_correctness(self):
        for a, b in zip(self.lefts, self.rights):

            expected_val = a.value - b.value
            expected_error = math.sqrt(a.error.abs_err**2 + b.error.abs_err**2)
            calculated = a - b

            self.compare_values_and_errors(expected_val, expected_error, calculated)


    def test_StatisticalError_mul_error_correctness(self):
        for a, b in zip(self.lefts, self.rights):

            expected_val = a.value * b.value
            expected_error = expected_val * math.sqrt(a.error.rel_err**2 + b.error.rel_err**2)
            calculated = a * b

            self.compare_values_and_errors(expected_val, expected_error, calculated)

    def test_StatisticalError_div_error_correctness(self):
        for a, b in zip(self.lefts, self.rights):

            expected_val = a.value / b.value
            expected_error = expected_val * math.sqrt(a.error.rel_err**2 + b.error.rel_err**2)
            calculated = a / b

            self.compare_values_and_errors(expected_val, expected_error, calculated)

class WorstCaseErrorTest(ErrorClassTest):

    def getErrorType(self):
        return errpp.WorstCaseError

    test_negation = ErrorClassTest.tst_neg

    def test_WorstCaseError_add_error_correctness(self):
        for a, b in zip(self.lefts, self.rights):

            expected_val = a.value + b.value
            expected_error = a.error.abs_err + b.error.abs_err
            calculated = a + b

            self.compare_values_and_errors(expected_val, expected_error, calculated)


    def test_WorstCaseError_sub_error_correctness(self):
        for a, b in zip(self.lefts, self.rights):

            expected_val = a.value - b.value
            expected_error = a.error.abs_err + b.error.abs_err
            calculated = a - b

            self.compare_values_and_errors(expected_val, expected_error, calculated)


    def test_WorstCaseError_mul_error_correctness(self):
        for a, b in zip(self.lefts, self.rights):

            expected_val = a.value * b.value
            expected_error = expected_val * (a.error.rel_err + b.error.rel_err)
            calculated = a * b

            self.compare_values_and_errors(expected_val, expected_error, calculated)


    def test_WorstCaseError_div_error_correctness(self):
        for a, b in zip(self.lefts, self.rights):

            expected_val = a.value / b.value
            expected_error = (a.error.rel_err + b.error.rel_err) * expected_val
            calculated = a / b

            self.compare_values_and_errors(expected_val, expected_error, calculated)


class ExtremeErrorTest(ErrorClassTest):

    def getErrorType(self):
        return errpp.ExtremeError
    
    test_negation = ErrorClassTest.tst_neg

    def test_ExtremeError_add_error_correctness(self):
        for a, b in zip(self.lefts, self.rights):

            expected_val = a.value + b.value
            expected_error = a.error.abs_err + b.error.abs_err
            calculated = a + b

            self.compare_values_and_errors(expected_val, expected_error, calculated)


    def test_ExtremeError_sub_error_correctness(self):
        for a, b in zip(self.lefts, self.rights):

            expected_val = a.value - b.value
            expected_error = a.error.abs_err + b.error.abs_err
            calculated = a - b

            self.compare_values_and_errors(expected_val, expected_error, calculated)


    def test_ExtremeError_mul_error_correctness(self):
        for a, b in zip(self.lefts, self.rights):

            expected_val = a.value * b.value
            expected_error = expected_val * (a.error.rel_err + b.error.rel_err + a.error.rel_err * b.error.rel_err)
            calculated = a * b

            self.compare_values_and_errors(expected_val, expected_error, calculated)


    def test_ExtremeError_div_error_correctness(self):
        for a, b in zip(self.lefts, self.rights):

            expected_val = a.value / b.value
            lim1 = (abs(a.value) + a.error.abs_err) / (abs(b.value) - b.error.abs_err) - abs(expected_val)
            lim2 = (abs(a.value) - a.error.abs_err) / (abs(b.value) + b.error.abs_err) - abs(expected_val)
            # makes 0 fucking sense to me, how can there be a choice here when there is no choice in the impl...
            expected_error = max(lim1, lim2)
            calculated = a / b

            self.compare_values_and_errors(expected_val, expected_error, calculated)

class ErrorPropagation(unittest.TestSuite):

    def __init__(self):
        self.addTests((RelationTest(), StatisticalErrorTest(), ExtremeErrorTest()))


if __name__ == '__main__':
    unittest.main()
