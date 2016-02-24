#import sys
#sys.path.append('/home/mpet/Aaron/TitanMidasScripts/pythonmidas')
#sys.path.append('/home/mpet/Aaron/TitanMidasScripts')

import pythonmidas.pythonmidas as Midas
from afgcontrol import afg
import calcFreq.calcFreq as CF
#import re


class SwiftDipole(afg):
    def __init__(self):
        afg.__init__(self)
        afgAddress = Midas.varget("/Experiment/Variables/AFG Addresses/Dipole")
        print afgAddress

        self.openConnection(ipAddress=afgAddress)

        self.afgName = 'Dipole'
        self.varRFAmp = '/Experiment/Variables/SwiftDipole/RF Amplitude (V)'
        self.varFreqC = ('/Experiment/Variables/SwiftDipole/' +
                         'Center Frequency (Hz)')
        self.varFreqMod = ('/Experiment/Variables/SwiftDipole/' +
                           'Frequency Modulation (Hz)')
        self.varSpecies = '/Experiment/Variables/SwiftDipole/Species'
        self.varCharge = '/Experiment/Variables/SwiftDipole/Species'
        self.varFreqList = "/Experiment/Variables/Dipole FreqList"

        self.CF = CF.calcFreq()
        self.CF.getReference()

        self.afgOnPath = "/Experiment/Variables/SwiftDipole/AFG On"

        self.varStartFreq = "/Experiment/Variables/StringDump"
        self.varStopFreq = "/Experiment/Variables/StringDump"

    def afgGetSpecies(self):
        species = Midas.varget(self.varSpecies).replace("+", "")
        species = [x.split()[0].strip() for x in species.split(";")]
        print species

        return species

    def afgGetCharge(self):
        charge = Midas.varget(self.varCharge).replace("+", "")
        charge = [x.split()[-1].strip() for x in charge.split(";")]
        print charge

        return charge

    def afgSetRFAmp(self):
        self.setAmplitude()

    def setAmplitude(self):
        rfamp = float(Midas.varget(self.varRFAmp))
        self.RFAmplitude = rfamp

        self.RFAmplitude = (self.RFAmplitude
                            if self.RFAmplitude > self.minRFAmp
                            else self.minRFAmp)
        self.RFAmplitude = (self.RFAmplitude
                            if self.RFAmplitude < self.maxRFAmp
                            else self.maxRFAmp)

        self.afgWrite("VOLT " + str(rfamp))

    def afgOnOff(self):
        state = Midas.varget("/Experiment/Variables/SwiftDipole/AFG On")
        if state == 'y':
            self.afgWrite("OUTP ON")
        else:
            self.afgWrite("OUTP OFF")
