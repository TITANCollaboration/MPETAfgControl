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
        #self.openConnection('142.90.119.225')
        afgAddress = Midas.varget("/Experiment/Variables/AFG Addresses/Dipole")
        print afgAddress
        #self.openConnection('mpetswift')
        self.openConnection(ipAddress=afgAddress)
        #self.afgName = 'swiftdipole'
        self.afgName = 'Dipole'
        self.varOnOff = '/Experiment/Variables/SwiftDipole/RF Amplitude (V)'
        self.varFreqC = ('/Experiment/Variables/SwiftDipole/' +
                         'Center Frequency (Hz)')
        self.varFreqMod = ('/Experiment/Variables/SwiftDipole/' +
                           'Frequency Modulation (Hz)')
        self.varSpecies = '/Experiment/Variables/SwiftDipole/Species'
        self.varFreqList = "/Experiment/Variables/Dipole FreqList"
        #self.afgClear()
        #self.afgSetSine()
        #self.afgSetModeList()
        self.CF = CF.calcFreq()
        self.CF.getReference()

        self.afgOnPath = "/Experiment/Variables/SwiftDipole/AFG On"

    def setAmplitude(self):
        rfamp = float(Midas.varget(self.varOnOff))
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

    def afgSetFreqList(self):
        self.afgClear()
        self.afgSetSine()
        self.afgSetModeList()

        self.setAmplitude()
        self.afgOnOff()
        afglist = self.genFreqList()
        # Join the list so it is ready for the AFG
        afglist = ",".join(afglist)
        self.afgWrite("LIST:FREQ " + afglist)
        self.freqListMessage()

        self.afgResetTrigger()
