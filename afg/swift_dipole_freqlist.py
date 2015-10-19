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

    def genFreqList(self):
        """
        Given a semi-colon delimited list of center frequencies and
        modulations from the odb generate a frequency list.

        The number of points defined in the odb should be a multiple
        of the number of frequencies.
        If not the 'extra' points are included in the last frequency to be
        scanned.

        If the frequency modulation list is shorter than the center
        frequency list then the last modulation listed is repeated until
        the lists are the same length.

        If the Frequency Modulation list is longer than the center frequency
        list then the 'extra' elements are ignored.
        """
        self.freqlist = []  # reset freqlist

        self.FreqC = str(Midas.varget(self.varFreqC))
        self.FreqC = [x.strip() for x in self.FreqC.split(";")]

        self.Species = Midas.varget(self.varSpecies)
        self.Species = [x.strip() for x in self.Species.split(";")]
        for i in range(len(self.FreqC)):
            if self.FreqC[i].lower() == 'freqp':
                self.FreqC[i] = self.CF.dipole_frequencies(self.Species[i])[0]
            else:
                self.FreqC[i] = float(self.FreqC[i])

        self.FreqMod = str(Midas.varget(self.varFreqMod))
        self.FreqMod = [float(x.strip()) for x in self.FreqMod.split(";")]

        self.getNumberOfPoints()

        while len(self.FreqMod) < len(self.FreqC):
            self.FreqMod.append(self.FreqMod[-1])
        print self.FreqMod

        n = [self.NumberPoints / len(self.FreqC)
             for x in range(len(self.FreqC))]
        # Add the left-overs to the last element
        n[-1] += self.NumberPoints % n[0]
        print n

        for i in range(len(self.FreqC)):
            fstart = self.FreqC[i] - self.FreqMod[i]
            df = 2. * self.FreqMod[i] / float(n[i] - 1)
            for j in range(n[i]):
                self.freqlist.append(str((fstart + j * df) / 1000000.) + "E06")

        freqstring = map(lambda x, y, z: "(" + str(x) + ", " + str(y) + ", "
                         + str(z) + ")",
                         self.FreqC, self.FreqMod, n)
        freqstring = "; ".join(freqstring)
        Midas.varset("/Experiment/Variables/Dipole FreqList", freqstring)
        print freqstring
        print self.freqlist
        return self.freqlist

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
