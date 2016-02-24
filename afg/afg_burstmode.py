import pythonmidas.pythonmidas as Midas
from afgcontrol import afg
#import calcFreq.calcFreq as CF


class BurstAFG(afg):

    def __init__(self):
        afg.__init__(self)
        #self.openConnection('142.90.119.225')
        afgAddress = Midas.varget("/Experiment/Variables/AFG Addresses/Burst")
        print afgAddress
        #self.openConnection('mpetswift')
        self.openConnection(ipAddress=afgAddress)
        #self.afgName = 'swiftdipole'
        self.afgName = 'Burst'
        self.varOnOff = '/Experiment/Variables/Burst/AFG On'
        self.varFreqC = ('/Experiment/Variables/Burst/' +
                         'Center Frequency (Hz)')
        self.varFreqMod = ('/Experiment/Variables/Burst/Phase (degrees)')
        self.varRFAMP = ('/Experiment/Variables/Burst/RF Amplitude (V)')
        #self.varSpecies = '/Experiment/Variables/SwiftDipole/Species'
        #self.afgClear()
        #self.afgSetSine()
        #self.afgSetModeList()
        #self.CF = CF.calcFreq()
        #self.CF.getReference()

        self.afgOnPath = "/Experiment/Variables/Burst/AFG On"

    def afgSetFreqList(self):
        '''Over-ride the default afgSetFreqList, and instead
        program the afg into burst mode with the given
        centre frequency, and take the frequency modulation
        to be the phase offset.
        '''
        self.afgClear()

        print "In Here"

        RFAmp = float(Midas.varget(self.varRFAMP))

        # Get frequency, and if it's a list, only take the first element
        #self.getFrequencyCentre()
        centfreq = float(Midas.varget(self.varFreqC))
        centfreq = str(centfreq / 1000000.) + "E06"

        # Get frequency modulation, and use it as the phase offset
        # If it's a list, only take the first element
        #self.getFrequencyModulation()
        #phase = self.FreqMod[0]
        phase = float(Midas.varget(self.varFreqMod))

        self.afgWrite("APPL:SIN " + centfreq + ", " + str(RFAmp) + " VPP, 0")
        print "APPL:SIN " + centfreq + ", " + str(RFAmp) + " VPP, 0"
        self.afgSetTigger()
        self.afgWrite("BURS:MODE GATED")
        self.afgWrite("BURS:PHAS " + str(phase))
        self.afgWrite("BURS:STAT ON")

        self.afgOnOff()

    def afgOnOff(self):
        state = Midas.varget(self.afgOnPath)
        if state == 'y':
            self.afgWrite("OUTP ON")
        else:
            self.afgWrite("OUTP OFF")
