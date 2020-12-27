import math
import errpp

# values
r1, dr1 = r2, dr2 = r4, dr4 = r5, dr5 = (93500, 0.1)
r3, dr3 = r6, dr6 = (130e3, 0.1)
Vcc, dVcc = (3.6, 2)
Vacc, dVacc = (3.24, None)  # @50g
fctr, dfctr = (2, 0)
Vocm, dVocm = (2.5, errpp.abs_to_rel_err(2.5, 0.07))  # LTC1992 grade H

print("factor = {0} \u00B1 {1}%".format(fctr, dfctr))
print("Vocm = {0:.3f} \u00B1 {1:.3f}%".format(Vocm, dVocm))

# calculations
#dVacc = errpp.abspp_rel(Vacc, [(Vacc, 2), (Vacc, 5)])  # PS:2%, Temp:5%
#print("Vacc = {0:.3f} \u00B1 {1:.3f}% \u004050g".format(Vacc, dVacc))
#
#r1r1, dr1r1 = (r1 + r1, errpp.abspp_rel(r1 + r1, [(r1, dr1), (r1, dr1)]))
#Vref, dVref = (Vcc * r1 / (r1 + r1), errpp.relpp([dVcc, dr1, dr1r1]))
#print("Vref = {0:.3f} \u00B1 {1:.3f}%".format(Vref, dVref))
#
#r4r5, dr4r5 = (r4 + r5, errpp.abspp_rel(r4 + r5, [(r4, dr4), (r5, dr5)]))
#Gain, dGain = (r6 * r4r5 / (r4 * r5)), errpp.relpp([dr4, dr5, dr6, dr4r5])
#print("Gain = {0:.3f} \u00B1 {1:.3f}%".format(Gain, dGain))
#
#VaVr, dVaVr = (Vacc - Vref,
#               errpp.abspp_rel(Vacc - Vref, [(Vacc, dVacc), (Vref, dVref)]))
#print("VaVr = {0:.3f} \u00B1 {1:.3f}%".format(VaVr, dVaVr))
#Vodm, dVodm = (VaVr * Gain / fctr, errpp.relpp([dVaVr, dGain, dfctr]))
#print("Vodm = {0:.3f} \u00B1 {1:.3f}%".format(Vodm, dVodm))
#Vpn, dVpn = (Vodm + Vocm,
#             errpp.abspp_rel(Vodm + Vocm, [(Vodm, dVodm), (Vocm, dVocm)]))
#print("Vpn  = (Vacc - Vref)*G/factor + Vocm = {0:.3f} \u00B1 {1:.3f}%".format(
#    Vpn, dVpn))
#
#print(math.sqrt((Vacc * 2 / 100)**2 + (Vacc * 5 / 100)**2) / (Vacc) * 100)

#rr = 100 * (1.001 / 0.998 - 1)
#print("R//R: ", rr)
#print(100 * (0.999 / 1.002 - 1))
#vref = 100 * (1.02 * 1.003 - 1)
#print("Vref: ", vref)
#gain = 100 * (1.001 / ((0.999**2) / 1.002) - 1)
#print("Gain: ", gain)
#allgain = gain + 0.7
#print("allGain: ", allgain)
#print("VaVr: ", vref + 5.1)
#vodm = ((vref + 5.1) / 100 + 1) * ((allgain / 100) + 1)
#print("Vodm: ", (vodm - 1) * 100)
#print("Vpn: ", (vodm - 1) * 100 + 2.8)
#
#print("------")
#
#again = 7  # %
#aoffs = 0.2  # 200mV
#
#gain = 1.001 * (1.001) / (0.999 * 0.999)
#print("gain", gain)
#vref = 1.001 / 0.999 + 2 / 100
#print("vref", vref)
#
#g = (r6 * r4r5 / (r4 * r5))
#max = (aoffs + 3.6 * (vref - 1)) * g * (vref) / 2 + 2.5 * 0.028
#
#ge = 7 + (gain - 1) * 100
#
#print("offset error", max)
#print("gain error", ge)
#print(0.35 * 5)
#print(0.0035 * 5)
#print(aoffs + 3.6 * (vref - 1))
#
#print("hallo")
err = errpp.WorstCaseError

dr1245 = 0.001
val_r1245 = 93500
r1 = r2 = r4 = r5 = errpp.ValueWithError(val_r1245, err(dr1245, errpp.rel_to_abs_err(val_r1245, dr1245)))

dr36 = 0.001
val_r36 = 130e3
r3 = r6 = errpp.ValueWithError(val_r36, err(dr36, errpp.rel_to_abs_err(val_r36, dr36)))

val_vcc = 3.6
Vcc = errpp.ValueWithError(val_vcc, err(2 , errpp.rel_to_abs_err(val_vcc, 0.02)))

val_vacc = 3.24
Vacc = errpp.ValueWithError(val_vacc, err(7, errpp.rel_to_abs_err(val_vacc, 0.07)))  # @50g

fctr = errpp.ValueWithError(2, err(0, 0))  # @50g

dvocm = 0.07
val_vocm = 2.5
Vocm = errpp.ValueWithError(val_vocm,
                            err(dVocm, errpp.abs_to_rel_err(val_vocm, dVocm)))

dvaa = 0.2
val_vaa = 0
Vaa = errpp.ValueWithError(val_vaa, err(dvaa, None))

print(Vaa)

Vref = Vcc * r1 / (r1 + r1)
print("vref", Vref)
Gain = r6 * (r4 + r5) / (r4 * r5)
print("gain", Gain)
Vpn = (Vacc) * Gain / fctr
print("vpn", Vpn)
Voff = (Vaa - Vref) * Gain / fctr + Vocm
print("voff", Voff)
