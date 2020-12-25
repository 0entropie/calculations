from abc import ABC, abstractmethod
import math


class ValueWithError(ABC):

    def __init__(self, value, error=0):
        self.value = value
        self.error = error              # absolute error

    def get_percent_err(self):
        if self.value == 0:
            raise ZeroDivisionError(self)
        return 100 * self.error/abs(self.value)

    def get_ppm_err(self):
        if self.value == 0:
            raise ZeroDivisionError(self)
        return 1e6 * self.error/abs(self.value)

    def type_check(self, other):
        if type(self) != type(other):
            raise TypeError("Different error types: ", type(self), type(other))

    def zeroDiv_check(self, other):
        if other.value == 0 or abs(other.value) <= other.error:
            raise ZeroDivisionError(other)

    @abstractmethod
    def __add__(self, other): pass

    @abstractmethod
    def __sub__(self, other): pass

    @abstractmethod
    def __mul__(self, other): pass

    @abstractmethod
    def __truediv__(self, other): pass

    @abstractmethod
    def __neg__(self): pass

    def __repr__(self):
        try: rel_error = "[{0:.3f}%]".format(self.get_percent_err())
        except ZeroDivisionError: rel_error = ""
        return "{0:.3f} \u00B1 {1:.3f} {2}".format(self.value, self.error, rel_error)

    def __str__(self):
        return self.__repr__()

class StatisticalError(ValueWithError):

    # q = x+y , dq = sqrt( dx**2 + dy**2 )
    def __add__(self, other):
        self.type_check(other)
        return StatisticalError(self.value + other.value, math.sqrt(self.error**2 + other.error**2))

    # q = x-y , sqrt( dx**2 + dy**2 )
    def __sub__(self, other):
        self.type_check(other)
        return StatisticalError(self.value - other.value, math.sqrt(self.error**2 + other.error**2))

    # q = xy , dq = q * sqrt( (dx/x)**2 + (dy/y)**2 ) = sqrt( (dx*y)**2 + (dy*x)**2 )
    def __mul__(self, other):
        self.type_check(other)
        return StatisticalError(self.value * other.value,
                                math.sqrt((self.error * other.value)**2 + (other.error * self.value)**2))

    # q = x/y , dq = q * sqrt( (dx/x)**2 + (dy/y)**2 ) = sqrt( (dx/y)**2 + (dy*x/(y*y))**2 )
    def __truediv__(self, other):
        self.type_check(other)
        self.zeroDiv_check(other)
        return StatisticalError(self.value / other.value,
                                math.sqrt((self.error/other.value)**2 + (other.error*self.value/(other.value**2))**2))

    def __neg__(self):
        return StatisticalError(-self.value, self.error)

class WorstCaseError(ValueWithError):

    # q = x+y , dq = dx+dy
    def __add__(self, other):
        self.type_check(other)
        return WorstCaseError(self.value + other.value, self.error + other.error)

    # q = x-y , dq = dx+dy
    def __sub__(self, other):
        self.type_check(other)
        return WorstCaseError(self.value - other.value, self.error + other.error)

    # q = xy , dq = |q|*(dx/|x| + dy/|y|) = dx*|y| + dy*|x|
    def __mul__(self, other):
        self.type_check(other)
        return WorstCaseError(self.value * other.value, self.error * abs(other.value) + other.error * abs(self.value))

    # q = x/y , dq = |q|*(dx/|x| + dy/|y|) = dx/|y| + dy*|x|/|y*y|
    def __truediv__(self, other):
        self.type_check(other)
        self.zeroDiv_check(other)
        return WorstCaseError(self.value / other.value,
                              self.error / abs(other.value) + other.error * abs(self.value) / (other.value**2))

    def __neg__(self):
        return WorstCaseError(-self.value, self.error)

class ExtremeError(WorstCaseError):

    # q = x+y , dq = dx+dy
    def __add__(self, other):
        self.type_check(other)
        return ExtremeError(self.value + other.value, self.error + other.error)

    # q = x-y , dq = dx+dy
    def __sub__(self, other):
        self.type_check(other)
        return ExtremeError(self.value - other.value, self.error + other.error)

    # q = xy , dq = |q|*(dx/|x| + dy/|y| + (dx/x)*(dy/y)) = dx*|y| + dy*|x| + dx*dy
    def __mul__(self, other):
        self.type_check(other)
        return ExtremeError(self.value * other.value,
                            self.error * abs(other.value) + other.error * abs(self.value) + self.error * other.error)

    # q = x/y , q(1 + dq/|q|) = x(1 + dx/|x|) / (y(1 + dy/|y|)) ,, dq = (|x| + dx) / (|y| - dy) - |x/y|
    def __truediv__(self, other):
        self.type_check(other)
        self.zeroDiv_check(other)
        return ExtremeError(self.value / other.value,
                            (abs(self.value) + self.error)/(abs(other.value) - other.error) - abs(self.value/other.value))

    def __neg__(self):
        return ExtremeError(-self.value, self.error)

conversion_dict = {StatisticalError: "toStatisticalError", WorstCaseError: "toWorstCaseError", ExtremeError: "toExtremeError"}

def mlt_percent(list_percentage, factor=100):
    return [p * factor for p in list_percentage]

def div_percent(list_percentage, factor=100):
    return [p / factor for p in list_percentage]

def abserr_to_relerr(list):
    return [mlt_percent([abserr / val])[0] for val,abserr in list]

def relerr_to_abserr(list):
    return [val * div_percent([relerr])[0] for val,relerr in list]

def abspp(list):
    return math.sqrt(sum([abserr ** 2 for abserr in list]))

def relpp(list):
    return mlt_percent([math.sqrt(sum([relerr ** 2 for relerr in div_percent(list)]))])[0]

def abspp_rel(res, list):
    return abserr_to_relerr([(res, abspp(relerr_to_abserr(list)))])[0]

def relpp_abs(res, list):
    return relerr_to_abserr([(res, relpp(abserr_to_relerr(list)))])[0]



 #import math

__percent_scale_factor = 100

#def decimal_to_percent(dec):
#    if not isinstance(dec, float):
#    raise TypeError("Only converting floats")
    #    return dec * __percent_scale_factor

def rel_to_abs_err(value, rel_err):
    return value * rel_err / __percent_scale_factor

def abs_to_rel_err(value, abs_err):
    return value * rel_err / __percent_scale_factor

def percent_to_decimal(per):
    return per / __percent_scale_factor

# too generic as a function, especially with selectable factor
#def mlt_percent(list_percentage, factor=100):
    #return [p * factor for p in list_percentage]

# same as above
#def div_percent(list_percentage, factor=100):
    #return [p / factor for p in list_percentage]

#avoid builtin names for variables and shit
#def abserr_to_relerr(val_err_list):
    #return [decimal_to_percent(abserr / val) for val,abserr in val_err_list]
#same as above
#def relerr_to_abserr(val_err_list):
    #return [val * percent_to_decimal(relerr) for val,relerr in val_err_list]

# ? standard deviation? Also builtin name again
#def abspp(abserrs):
    #return math.sqrt(sum([abserr ** 2 for abserr in abserrs]))

#def relpp(rel_errs):
    # ugly as hell
    # return mlt_percent([math.sqrt(sum([relerr ** 2 for relerr in div_percent(list)]))])[0]
    # don't need a list, iterator is more performant
    #rel_dec = (percent_to_decimal(per) for per in rel_errs)
    #rel_squares = (rel_err ** 2 for rel_err in rel_dec)
    #return decimal_to_percent(math.sqrt(sum(rel_squares)))


#def abspp_rel(res, rel_errs):
    # write once, read never again... also builtin name again >:-[
    # return abserr_to_relerr([(res, abspp(relerr_to_abserr(list)))])[0]
    #abs_errs = relerr_to_abserr(rel_errs)
    #abs_deviation = abspp(abs_errs)
    #return decimal_to_percent(abs_deviation/res)

#def relpp_abs(res, abs_errs):
    # same as above rly
    # return relerr_to_abserr([(res, relpp(abserr_to_relerr(list)))])[0]
    #rel_errs = abserr_to_relerr(abs_errs)
    #rel_deviation = relpp(rel_erss)
    #    return res * percent_to_decimal(rel_deviation)