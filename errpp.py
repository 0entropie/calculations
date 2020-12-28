import abc
import math

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

class ValueWithError:
    def __init__(self, value, error):
        self.value = value
        if not isinstance(error, BaseError):
            raise TypeError(f"Expected Error Object but got {type(error)}")
        self.error = error  # Error Object not number

    def get_error(self):
        return self.error

    def __add__(self, other):
        new_val = self.value + other.value
        return ValueWithError(new_val, self.error.update_err_add(new_val, other.error))

    def __sub__(self, other):
        new_val = self.value - other.value
        return ValueWithError(new_val, self.error.update_err_sub(new_val, other.error))

    def __mul__(self, other):
        new_val = self.value * other.value
        if new_val == 0:
            ref_val = max(self.value, other.value)
        else:
            ref_val = new_val
        return ValueWithError(new_val, self.error.update_err_mul(ref_val, other.error))

    def __truediv__(self, other):
        if other.value == 0:
            raise ZeroDivisionError("Attempt to divide by 0 Value")
        new_val = self.value / other.value

        if new_val == 0:
            ref_val = other.value
        else:
            ref_val = new_val

        return ValueWithError(new_val, self.error.update_err_div(ref_val, other.error))

    def __neg__(self):
        return ValueWithError(-self.value, self.error)

    def __repr__(self):
        try:
            rel_error = "[{0:.3f}%]".format(self.error.get_percent_err())
        except ValueError:
            rel_error = "--%"
        return "{0:.3f} \u00B1 {1:.3f} {2}".format(self.value,
                                                   self.error.abs_err,
                                                   rel_error)

    def __str__(self):
        return self.__repr__()

class BaseError(abc.ABC):
    def __init__(self, abs_err, rel_err):
        self.__abs_err = abs(abs_err)
        if rel_err is not None:
            self.__rel_err = abs(rel_err)
        else:
            self.__rel_err = None

    @property
    def abs_err(self):
        return self.__abs_err

    @property
    def rel_err(self):
        return self.__rel_err

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

    def type_check(self, other):
        if not isinstance(other, self.__class__):
            raise TypeError("Different error types: ", type(self), type(other))

    def calculate_rel_err_from_abs(self, ref_val, abs_err):
        if ref_val == 0:
            return None
        else:
            return abs(abs_err / ref_val)

    @abc.abstractmethod
    def update_err_add(self, ref_val, other):
        pass

    @abc.abstractmethod
    def update_err_sub(self, ref_val, other):
        pass

    @abc.abstractmethod
    def update_err_mul(self, ref_val, other):
        pass

    @abc.abstractmethod
    def update_err_div(self, ref_val, other):
        pass

class StatisticalError(BaseError):

    # q = x+y , dq = sqrt( dx**2 + dy**2 )
    def update_err_add(self, ref_val, other):
        self.type_check(other)
        new_abs_err = math.sqrt(self.abs_err**2 + other.abs_err**2)

        return StatisticalError(new_abs_err, self.calculate_rel_err_from_abs(ref_val, new_abs_err))

    # q = x-y , sqrt( dx**2 + dy**2 )
    def update_err_sub(self, ref_val, other):
        return self.update_err_add(ref_val, other)

    # q = xy , dq = q * sqrt( (dx/x)**2 + (dy/y)**2 ) = sqrt( (dx*y)**2 + (dy*x)**2 )
    def update_err_mul(self, ref_val, other):
        self.type_check(other)

        if self.rel_err is None:
            new_abs_error = abs(ref_val * other.abs_err)
            new_rel_error = None
        elif other.rel_err is None:
            new_abs_error = abs(ref_val * self.abs_err)
            new_rel_error = None
        else:
            new_rel_error = math.sqrt(self.rel_err**2 + other.rel_err**2)
            new_abs_error = abs(ref_val * new_rel_error)
        return StatisticalError(new_abs_error, new_rel_error)

    # q = x/y , dq = q * sqrt( (dx/x)**2 + (dy/y)**2 ) = sqrt( (dx/y)**2 + (dy*x/(y*y))**2 )
    def update_err_div(self, ref_val, other):
        return self.update_err_mul(ref_val, other)

class WorstCaseError(BaseError):

    # q = x+y , dq = dx+dy
    def update_err_add(self, ref_val, other):
        self.type_check(other)
        new_abs_error = self.abs_err + other.abs_err

        return WorstCaseError(new_abs_error, self.calculate_rel_err_from_abs(ref_val, new_abs_error))

    # q = x-y , dq = dx+dy
    def update_err_sub(self, ref_val, other):
        return self.update_err_add(ref_val, other)

    # q = xy , dq = |q|*(dx/|x| + dy/|y|) = dx*|y| + dy*|x|
    def update_err_mul(self, ref_val, other):
        self.type_check(other)

        if self.rel_err is None:
            new_abs_error = abs(ref_val * other.abs_err)
            new_rel_error = None
        elif other.rel_err is None:
            new_abs_error = abs(ref_val * self.abs_err)
            new_rel_error = None
        else:
            new_rel_error = self.rel_err + other.rel_err
            new_abs_error = abs(new_rel_error * ref_val)
        return WorstCaseError(new_abs_error, new_rel_error)

    # q = x/y , dq = |q|*(dx/|x| + dy/|y|) = dx/|y| + dy*|x|/|y*y|
    def update_err_div(self, ref_val, other):
        return self.update_err_mul(ref_val, other)


class ExtremeError(BaseError):

    # q = x+y , dq = dx+dy
    def update_err_add(self, ref_val, other):
        self.type_check(other)
        new_abs_error = self.abs_err + other.abs_err

        return ExtremeError(new_abs_error, self.calculate_rel_err_from_abs(ref_val, new_abs_error))

    # q = x-y , dq = dx+dy
    def update_err_sub(self, ref_val, other):
        return self.update_err_add(ref_val, other)

    # q = xy , dq = |q|*(dx/|x| + dy/|y| + (dx/x)*(dy/y)) = dx*|y| + dy*|x| + dx*dy
    def update_err_mul(self, ref_val, other):
        self.type_check(other)

        if self.rel_err is None:
            new_abs_error = abs(ref_val * other.abs_err + self.abs_to_rel_err * other.abs_err)
            new_rel_error = None
        elif other.rel_err is None:
            new_abs_error = abs(ref_val * self.abs_err + self.abs_to_rel_err * other.abs_err)
            new_rel_error = None
        else:
            new_rel_error = self.rel_err + other.rel_err + self.rel_err * other.rel_err
            new_abs_error = abs(new_rel_error * ref_val)

        return ExtremeError(new_abs_error, new_rel_error)

    # q = x/y , q(1 + dq/|q|) = x(1 + dx/|x|) / (y(1 + dy/|y|)) ,, dq = (|x| + dx) / (|y| - dy) - |x/y|
    def update_err_div(self, ref_val, other):
        #self.type_check(other)
        #self.zeroDiv_check(other)
        #return ExtremeError(
        #    self.value / other.value, (abs(self.value) + self.error) /
        #    (abs(other.value) - other.error) - abs(self.value / other.value))
        raise NotImplementedError("Left as excercise to the reader")
