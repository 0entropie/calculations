import abc
import math
from numbers import Number
from contextlib import contextmanager
import operator

__percent_scale_factor = 100
__ppm_scale_factor = 1_000_000

def decimal_to_percent(dec):
    return dec * __percent_scale_factor

def decimal_to_ppm(dec):
    return dec * __ppm_scale_factor

def rel_to_abs_err(value, rel_err):
    return value * rel_err


def abs_to_rel_err(value, abs_err):
    return abs_err / value


def percent_to_decimal(per):
    return per / __percent_scale_factor


def _binary_arithmetic_op(method):
    def perform_arithmetic_op(left, right):
        lprop = left.prop or _GLOBAL_PROPAGATION_METHOD
        rprop = right.prop or _GLOBAL_PROPAGATION_METHOD

        if (not lprop):
            raise ValueError("Propagation Method on Value was set to global, but global propagation method is None")

        if not lprop.is_compatible(rprop):
            raise ValueError("Incompatible propagation methods")
        # Call original method, only for division to check dividend basically..
        method(left, right)
        
        operation = ValueWithError._op_map[method.__name__]
        new_val = operation(left.value, right.value)

        prop_method = getattr(lprop, ValueWithError._prop_map[operation])
        new_abs_err = prop_method(new_val, left, right)
        return ValueWithError.from_val_abs_err_pair(new_val, new_abs_err, left.prop)

    return perform_arithmetic_op


_REL_ERROR_FACTOR_LIMIT = 10


class ExcessiveErrorException(Exception):
    def __init__(self, val, rel_err):
        super().__init__(f"Relative Error {rel_err} ({decimal_to_percent(rel_err)})"
                         f"for value {val} exceeds Limit of"
                         f" {_REL_ERROR_FACTOR_LIMIT} ({decimal_to_percent(_REL_ERROR_FACTOR_LIMIT)}).")


_GLOBAL_PROPAGATION_METHOD = None


def set_global_propagator(prop):
    if prop is not None and not isinstance(prop, ErrorPropagationMethod):
        raise TypeError("Propagator must be instance of ErrorPropagationMethod")
    
    global _GLOBAL_PROPAGATION_METHOD
    _GLOBAL_PROPAGATION_METHOD = prop


def get_global_propagator():
    return _GLOBAL_PROPAGATION_METHOD


@contextmanager
def propagation_context(prop):
    old_prop = get_global_propagator()
    try:
        set_global_propagator(prop)
        yield object()
    finally:
        set_global_propagator(old_prop)

class ErrorPropagationMethod(abc.ABC):

    @abc.abstractmethod
    def propagate_error_add(self, add_result, left, right):
        pass

    @abc.abstractmethod
    def propagate_error_sub(self, sub_result, left, right):
        pass

    @abc.abstractmethod
    def propagate_error_mul(self, mul_result, left, right):
        pass

    @abc.abstractmethod
    def propagate_error_div(self, div_result, left, right):
        pass

    @abc.abstractmethod
    def is_compatible(self, other):
        pass

class ValueWithError:

    _prop_map = {operator.add: ErrorPropagationMethod.propagate_error_add.__name__,
                 operator.sub: ErrorPropagationMethod.propagate_error_sub.__name__, 
                 operator.mul: ErrorPropagationMethod.propagate_error_mul.__name__,
                 operator.truediv: ErrorPropagationMethod.propagate_error_div.__name__}
        
    _op_map = {'__add__': operator.add,
               '__sub__': operator.sub,
               '__mul__': operator.mul,
               '__truediv__': operator.truediv}

    def __init__(self, value, abs_err, rel_err, prop_method=None):
        if not (isinstance(value, Number) or isinstance(abs_err, Number))\
                or (rel_err is not None and not isinstance(rel_err, Number)):
            raise TypeError("Value and Errors need to be numeric types")

        if rel_err is not None and rel_err > _REL_ERROR_FACTOR_LIMIT:
            raise ExcessiveErrorException(value, rel_err)

        self.value = value
        self.__abs_err = abs(abs_err)
        self.__rel_err = abs(rel_err) if rel_err is not None else None

        self.prop = prop_method


    @property
    def abs_err(self):
        return self.__abs_err

    @property
    def rel_err(self):
        return self.__rel_err

    @classmethod
    def from_val_abs_err_pair(cls, val, abs_err, prop_method=None):
        rel_err = abs_err/val if val != 0 else None
        return ValueWithError(val, abs_err, rel_err, prop_method)

    @classmethod
    def from_val_rel_err_pair(cls, val, rel_err, prop_method=None):
        if rel_err is None:
            raise ValueError("Can not construct ValueWithError from value and invalid relative Error")
        abs_err = val * rel_err
        return ValueWithError(val, abs_err, rel_err, prop_method)

    def get_errors(self):
        return (self.abs_err, self.rel_err)

    def __value_with_same_prop(self, val, abs_err, rel_err):
        return ValueWithError(val, abs_err, rel_err, self.prop)

    @_binary_arithmetic_op
    def __add__(self, other):
        pass

    @_binary_arithmetic_op
    def __sub__(self, other):
        pass

    @_binary_arithmetic_op
    def __mul__(self, other):
        pass

    @_binary_arithmetic_op
    def __truediv__(self, other):
        if other.value == 0:
            raise ZeroDivisionError("Attempt to divide by 0 Value")

    def __neg__(self):
        return self.__value_with_same_prop(-self.value, self.abs_err, self.rel_err)

    def __repr__(self):
        return "{0:.3f} \u00B1 {1:.3f} {2}".format(self.value,
                                                   self.abs_err,
                                                   self.rel_err)

    __str__ = __repr__

    def get_percent_err(self):
        if self.__rel_err is not None:
            return decimal_to_percent(self.__rel_err)
        else:
            raise ValueError("Relative Error is not defined")

    def get_ppm_err(self):
        if self.__rel_err is not None:
            return decimal_to_ppm(self.__rel_err)
        else:
            raise ValueError("Relative Error is not defined")


class StatisticalPropagation(ErrorPropagationMethod):

    # q = x+y , dq = sqrt( dx**2 + dy**2 )
    def propagate_error_add(self, add_result, left_val, right_val):
        return  math.sqrt(left_val.abs_err**2 + right_val.abs_err**2)

    # q = x-y , sqrt( dx**2 + dy**2 )
    def propagate_error_sub(self, sub_result, left, right):
        return self.propagate_error_add(sub_result, left, right)

    # q = xy , dq = q * sqrt( (dx/x)**2 + (dy/y)**2 ) = sqrt( (dx*y)**2 + (dy*x)**2 )
    def propagate_error_mul(self, mul_result, left, right):
        return math.sqrt((left.abs_err * right.value)**2 + (right.abs_err * left.value)**2)

    # q = x/y , dq = q * sqrt( (dx/x)**2 + (dy/y)**2 ) = sqrt( (dx/y)**2 + (dy*x/(y*y))**2 )
    def propagate_error_div(self, div_result, left, right):
        return math.sqrt((left.abs_err / right.value)**2
                         + (right.abs_err * left.value / right.value**2)**2)

    def is_compatible(self, other):
        return isinstance(other, self.__class__)


class WorstCasePropogation(ErrorPropagationMethod):
    # q = x+y , dq = dx+dy
    def propagate_error_add(self, add_result, left_val, right_val):
        return  left_val.abs_err + right_val.abs_err

    # q = x-y , dq = dx+dy
    def propagate_error_sub(self, sub_result, left, right):
        return self.propagate_error_add(sub_result, left, right)

    # q = xy , dq = |q|*(dx/|x| + dy/|y|) = dx*|y| + dy*|x|
    def propagate_error_mul(self, mul_result, left, right):
        return left.abs_err * abs(right.value) + right.abs_err * abs(left.value)

    # q = x/y , dq = |q|*(dx/|x| + dy/|y|) = dx/|y| + dy*|x|/|y*y| = dx*|y| + dy*|x|
    def propagate_error_div(self, div_result, left, right):
        return left.abs_err / abs(right.value) + right.abs_err * abs(left.value) / right.value**2

    def is_compatible(self, other):
        return isinstance(other, self.__class__)


class ExtremePropagation(ErrorPropagationMethod):
    # q = x+y , dq = dx+dy
    def propagate_error_add(self, add_result, left_val, right_val):
        return  left_val.abs_err + right_val.abs_err

    # q = x-y , dq = dx+dy
    def propagate_error_sub(self, sub_result, left, right):
        return self.propagate_error_add(sub_result, left, right)

    # q = xy , dq = |q|*(dx/|x| + dy/|y| + (dx/x)*(dy/y)) = dx*|y| + dy*|x| + dx*dy
    def propagate_error_mul(self, mul_result, left, right):
        return left.abs_err * abs(right.value)\
               + right.abs_err * abs(left.value)\
               + left.abs_err * right.abs_err

    # q = x/y , q(1 + dq/|q|) = x(1 + dx/|x|) / (y(1 + dy/|y|)) ,, dq = (|x| + dx) / (|y| - dy) - |x/y|
    def propagate_error_div(self, div_result, left, right):
        numerator = abs(left.value) + left.abs_err
        denominator = abs(right.value) - right.abs_err
        if denominator == 0:
            raise ValueError(
                    "Can not propagate Value with 100% relative Error with Extreme method."
                    f" Value: {right}")
        return numerator / denominator - abs(div_result)

    def is_compatible(self, other):
        return isinstance(other, self.__class__)
