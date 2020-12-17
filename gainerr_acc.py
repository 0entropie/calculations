import errpp,math

# values
r1,dr1 = r2,dr2 = r4,dr4 = r5,dr5   = (93500, 0.1)
r3,dr3 = r6,dr6                     = (130e3, 0.1)
Vcc,dVcc                            = (3.6, 2)
Vacc,dVacc                          = (3.24, None)                                      # @50g
fctr, dfctr                         = (2, 0)
Vocm, dVocm                         = (2.5, errpp.abserr_to_relerr([(2.5, 0.07)])[0])   # LTC1992 grade H

print("factor = {0} \u00B1 {1}%".format(fctr, dfctr))
print("Vocm = {0:.3f} \u00B1 {1:.3f}%".format(Vocm, dVocm))

# calculations
dVacc = errpp.abspp_rel(Vacc,        [(Vacc,2), (Vacc,5)])      # PS:2%, Temp:5%
print("Vacc = {0:.3f} \u00B1 {1:.3f}% \u004050g".format(Vacc, dVacc))

r1r1, dr1r1 = (r1 + r1,                 errpp.abspp_rel(r1 + r1,        [(r1,dr1), (r1,dr1)]))
Vref, dVref = (Vcc * r1/(r1 + r1),      errpp.relpp(                    [dVcc, dr1, dr1r1]))
print("Vref = {0:.3f} \u00B1 {1:.3f}%".format(Vref, dVref))

r4r5, dr4r5 = (r4 + r5,                 errpp.abspp_rel(r4 + r5,        [(r4,dr4), (r5,dr5)]))
Gain, dGain = (r6*r4r5/(r4*r5)),        errpp.relpp(                    [dr4, dr5, dr6, dr4r5])
print("Gain = {0:.3f} \u00B1 {1:.3f}%".format(Gain, dGain))

VaVr, dVaVr = (Vacc - Vref,             errpp.abspp_rel(Vacc - Vref,    [(Vacc,dVacc), (Vref, dVref)]))
print("VaVr = {0:.3f} \u00B1 {1:.3f}%".format(VaVr, dVaVr))
Vodm, dVodm = (VaVr*Gain/fctr,          errpp.relpp(                    [dVaVr, dGain, dfctr]))
print("Vodm = {0:.3f} \u00B1 {1:.3f}%".format(Vodm, dVodm))
Vpn, dVpn   = (Vodm + Vocm,             errpp.abspp_rel(Vodm + Vocm,    [(Vodm, dVodm), (Vocm, dVocm)]))
print("Vpn  = (Vacc - Vref)*G/factor + Vocm = {0:.3f} \u00B1 {1:.3f}%".format(Vpn, dVpn))

print(math.sqrt((Vacc*2/100)**2 + (Vacc*5/100)**2)/(Vacc)*100)