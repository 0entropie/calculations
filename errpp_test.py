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


def perform_binary_op_on_vwes(left_vwes, right_vwes, op):
    return map(lambda xy: op(*xy), zip(left_vwes, right_vwes))


_TRIALS = 100000


def _relation_binary_op_test(operation):
    def wrapper(method):
        def perform_binary_op_test(self):
            for left, right in zip(self.left_vwes, self.right_vwes):
                try:
                    l, k, m = tuple(perform_binary_op_on_vwes(left, right, operation))
                except errpp.ExcessiveErrorException:
                    continue
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
                try:
                    self.calculated = operation(a, b)
                    method(self, a, b)
                    self.compare_values_and_errors()
                except errpp.ExcessiveErrorException:
                    continue
        return perform_binary_op_test
    return wrapper


class ErrorClassTest(abc.ABC):

    @abc.abstractmethod
    def getErrorType(self):
        pass

    def setUp(self):
        self.lefts = (vwe_from_val_abs_err_pair(self.getErrorType(), random_val_and_abs_error()) for _ in range(_TRIALS))
        self.rights = (vwe_from_val_abs_err_pair(self.getErrorType(), random_val_and_abs_error()) for _ in range(_TRIALS))
        self.err = self.getErrorType()()

    def round_dec(self, n, decs = 5):
        return round(n, decs)

    def compare_values_and_errors(self):
        self.assertEqual(self.round_dec(self.expected_val), self.round_dec(self.calculated.value))
        self.assertEqual(self.round_dec(abs(self.expected_error)), self.round_dec(self.calculated.abs_err))

    @_binary_op_propagation_test(operator.sub)
    def test_negation(self, a, b):
        # overwrite preset values by decorator
        self.expected_val = -a.value
        self.expected_error = a.abs_err
        self.calculated = -a

    def test_div_zero(self):
        a, b = errpp.ValueWithError.from_val_abs_err_pair(1, 0, self.err), errpp.ValueWithError.from_val_abs_err_pair(0, 0, self.err)
        with self.assertRaises(ZeroDivisionError):
            a / b

    def test_zero_val_rel_err_none(self):
        a = errpp.ValueWithError.from_val_abs_err_pair(0, 0, self.err)
        self.assertEqual(a.rel_err, None)

    def test_none_propagation(self):
        a, b = errpp.ValueWithError.from_val_abs_err_pair(1, 0.9, self.err), errpp.ValueWithError.from_val_abs_err_pair(0, 1, self.err)
        x = a * b
        self.assertEqual(x.rel_err, None)
        self.assertNotEqual(x.abs_err, 0)
        y = b / a
        self.assertEqual(y.rel_err, None)
        self.assertNotEqual(y.abs_err, 0)

    def test_scalar_propagation(self):
        a, b = errpp.ValueWithError.from_val_abs_err_pair(2, 0, self.err), errpp.ValueWithError.from_val_abs_err_pair(5, 0, self.err)
        x = a + b
        self.assertEqual((x.value, x.abs_err, x.rel_err), (7, 0, 0))
        y = a - b
        self.assertEqual((y.value, y.abs_err, y.rel_err), (-3, 0, 0))
        z = a * b
        self.assertEqual((z.value, z.abs_err, z.rel_err), (10, 0, 0))
        omega = a / b
        self.assertEqual((omega.value, omega.abs_err, omega.rel_err), (0.4, 0, 0))


def _create_error_class_test(testcls):
    class _ErrorTestImpl(testcls, ErrorClassTest, unittest.TestCase):
        def __new__(cls, *args, **kwargs):
            clsdict = vars(testcls)
            for attr_name in clsdict:
                if attr_name.startswith("test_random"):
                    new_attr_val = clsdict[attr_name]
                    if "add" in attr_name:
                        new_attr_val = _binary_op_propagation_test(operator.add)(new_attr_val)
                    elif "sub" in attr_name:
                        new_attr_val = _binary_op_propagation_test(operator.sub)(new_attr_val)
                    elif "mul" in attr_name:
                        new_attr_val = _binary_op_propagation_test(operator.mul)(new_attr_val)
                    elif "div" in attr_name:
                        new_attr_val = _binary_op_propagation_test(operator.truediv)(new_attr_val)
                    else:
                        continue
                    setattr(cls, attr_name, new_attr_val)
            instance = object.__new__(cls)

            return instance

    return _ErrorTestImpl


@_create_error_class_test
class StatisticalErrorTest:

    def getErrorType(self):
        return errpp.StatisticalPropagation

    def test_random_StatisticalError_add_error_correctness(self, a, b):
            self.expected_error = math.sqrt(a.abs_err**2 + b.abs_err**2)

    def test_random_StatisticalError_sub_error_correctness(self, a, b):
        self.expected_error = math.sqrt(a.abs_err**2 + b.abs_err**2)

    def test_random_StatisticalError_mul_error_correctness(self, a, b):
        self.expected_error = self.expected_val * math.sqrt(a.rel_err**2 + b.rel_err**2)

    def test_random_StatisticalError_div_error_correctness(self, a, b):
        self.expected_error = self.expected_val * math.sqrt(a.rel_err**2 + b.rel_err**2)


@_create_error_class_test
class WorstCaseErrorTest:

    def getErrorType(self):
        return errpp.WorstCasePropogation

    def test_random_WorstCaseError_add_error_correctness(self, a, b):
        self.expected_error = a.abs_err + b.abs_err

    def test_random_WorstCaseError_sub_error_correctness(self, a, b):
        self.expected_error = a.abs_err + b.abs_err

    def test_random_WorstCaseError_mul_error_correctness(self, a, b):
        self.expected_error = self.expected_val * (a.rel_err + b.rel_err)

    def test_random_WorstCaseError_div_error_correctness(self, a, b):
        self.expected_error = (a.rel_err + b.rel_err) * self.expected_val


@_create_error_class_test
class ExtremeErrorTest:

    def getErrorType(self):
        return errpp.ExtremePropagation

    def test_random_ExtremeError_add_error_correctness(self, a, b):
        self.expected_error = a.abs_err + b.abs_err

    def test_random_ExtremeError_sub_error_correctness(self, a, b):
        self.expected_error = a.abs_err + b.abs_err

    def test_random_ExtremeError_mul_error_correctness(self, a, b):
        self.expected_error = self.expected_val * (a.rel_err + b.rel_err + a.rel_err * b.rel_err)

    def test_random_ExtremeError_div_error_correctness(self, a, b):
        lim1 = (abs(a.value) + a.abs_err) / (abs(b.value) - b.abs_err) - abs(self.expected_val)
        lim2 = (abs(a.value) - a.abs_err) / (abs(b.value) + b.abs_err) - abs(self.expected_val)
        # makes 0 fucking sense to me, how can there be a choice here when there is no choice in the impl...
        self.expected_error = max(lim1, lim2)


class ValueWithErrorBasicTest(unittest.TestCase):

    def test_default_propagator_get_set(self):
        err1 = errpp.StatisticalPropagation()
        errpp.set_global_propagator(err1)
        self.assertEqual(errpp.get_global_propagator(), err1)
        err2 = errpp.WorstCasePropogation()
        errpp.set_global_propagator(err2)
        self.assertEqual(errpp.get_global_propagator(), err2)

    def test_default_propagator_context(self):
        a, b = [errpp.ValueWithError.from_val_abs_err_pair(1, 1)] * 2
        cur_glob_prop = errpp.get_global_propagator()
        with errpp.propagation_context(errpp.WorstCasePropogation()):
            c = a + b
            self.assertEqual((2, 2, 1), (c.value, c.abs_err, c.rel_err))
        self.assertEqual(errpp.get_global_propagator(), cur_glob_prop)

class ErrorPropagation(unittest.TestSuite):

    def __init__(self):
        self.addTests((RelationTest(), StatisticalErrorTest(), ExtremeErrorTest(), WorstCaseErrorTest(), ValueWithErrorBasicTest()))


if __name__ == '__main__':
    unittest.main()
