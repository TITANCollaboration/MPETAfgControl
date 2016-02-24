#import sys
#sys.path.append('/home/mpet/Aaron/TitanMidasScripts/pythonmidas')
#sys.path.append('/home/mpet/Aaron/TitanMidasScripts')

import time
import pythonmidas.pythonmidas as Midas
import calcFreq.calcFreq as CF
import telnetlib
#import operator


class afg:
    """
    afgcontrol is a class to program the afg. It uses the pythonmidas
    module to read and write to the midas odb.
    """

    # Frequency list
    freqlist = []
    # Frequency list vars
    FreqC = 0.
    FreqMod = 0.
    NumberPoints = 0

    # RF Settings
    RFAmplitude = 0.

    # telnet connection
    telnet = ""
    #host =  "142.90.120.108"
    # 20150901 changed because afg died during power bump
    #host = "mpetquad"
    host = ""
    #port = "5024"
    port = ""
    connectionOpen = False
    sleepTime = 0.1  # Silly sleep time to wait for telnet response

    regex = ['33521A>', '33500>']

    afgName = 'Quad'

    def __init__(self):
        #self.telnet = telnetlib.Telnet()
        self.CF = CF.calcFreq()
        self.CF.getReference()

        #self.maxRFAmp = 2.0
        # Maximum input voltage is 5V. Take 4.8V so that we are
        # far away from any distortions.
        self.maxRFAmp = 4.8
        self.minRFAmp = 0.002

        self.afgOnPath = "/Experiment/Variables/AFG On"
        self.afgAddress = "/Experiment/Variables/AFG Addresses/Quadrupole"

        self.varFreqC = "/Experiment/Variables/Center Frequency"
        self.varFreqMod = "/Experiment/Variables/Frequency Deviation"
        self.varSpecies = "/Experiment/Variables/Species"
        self.varCharge = "/Experiment/Variables/Charge"

        self.varNumberPoints = ("/Equipment/TITAN_ACQ/ppg cycle/begin_ramp/" +
                                "loop count")
        self.varStartFreq = "/Experiment/Variables/StartFreq (MHz)"
        self.varStopFreq = "/Experiment/Variables/EndFreq (MHz)"

        self.varFreqList = "/Experiment/Variables/Quad FreqList"

        self.varCalExTime = ("/Experiment/Variables/MPET RF Calibration/" +
                             "RF Excitation Time (ms)")
        self.varCalVolatage = ("/Experiment/Variables/MPET RF Calibration" +
                               "/RF Amplitude (V)")
        self.varTakeUser = "/Experiment/Edit on Start/Amplitude Override"

        self.varRFUserAmp = "/Experiment/Variables/MPETRFAmp"
        pass

    def setip(self, ipAddress):
        self.host = str(ipAddress).strip()
        #print self.host

    def setPort(self, Port):
        self.port = str(Port).strip()
        #print self.host

    #def openConnection(self,ipAddress="142.90.120.108",Port="5024"):
    def openConnection(self, ipAddress="", Port="5024"):
        if ipAddress is "":
            #ipAddress = Midas.varget("/Experiment/Variables/" +
            #                         "AFG Addresses/Quadrupole")
            ipAddress = Midas.varget(self.afgAddress)
            print ipAddress
        self.setip(ipAddress)
        self.setPort(Port)
        #print self.host
        #self.telnet.open(self.host,self.port)
        self.telnet = telnetlib.Telnet(self.host, self.port, 9999)
        if self.telnet.expect(self.regex)[0] > -1:
            self.connectionOpen = True
            #print self.telnet
            #print self.connectionOpen

    def closeConnection(self):
        self.telnet.close()
        #if self.telnet.expect(self.regex)[0] == -1:
        #    self.connectionOpen = False
        #    #print self.connectionOpen

    def afgWrite(self, command):
        # Write the command
        self.telnet.write(command + "\r")
        time.sleep(self.sleepTime)
        # Read the response
        expect = self.telnet.expect(self.regex)
        # Check if the command was sent
        #if expect[0] == 1:
        result = expect[2].split("\r")
        return result[0].strip().split(",")

    def afgClear(self):
        # Abort current frequency list sweep
        self.afgWrite("ABOR")
        # Clear device errors
        self.afgWrite("*CLS")

    def afgResetTrigger(self):
        self.afgClear()
        self.afgWrite("INIT:CONT ON")

    def afgSetSine(self):
        #self.afgWrite("FUNC SINC")
        self.afgWrite("FUNC SIN")

    def afgSetModeList(self):
        self.afgWrite("FREQ:MODE LIST")

    def afgSetOutputLoad(self, load="INF"):
        '''
        Set the output load to "load". Default is High-Z.
        '''
        print "Load: " + load
        self.afgWrite("OUTP:LOAD " + load)

    def afgSetTigger(self, source="EXT"):
        print "Tigger Source: " + source
        self.afgWrite("TRIG:SOUR " + source)

    def afgOn(self):
        self.afgWrite("OUTP ON")
        Midas.varset(self.afgOnPath, "y")

    def afgOff(self):
        self.afgWrite("OUTP OFF")
        Midas.varset(self.afgOnPath, "n")

    def afgTurnOnOff(self, state):
        #state = self.afgWrite("OUTP?")
        if state:
            self.afgOn()
            statemsg = "on"
        else:
            self.afgOff()
            statemsg = "off"
        Midas.sendmessage(self.afgName, "AFG is " + statemsg)

    def afgStartMenuOnOff(self):
        #userstate = Midas.varget("/Experiment/Variables/AFG On")
        userstate = Midas.varget(self.afgOnPath)
        userstate = (userstate == 'y')
        self.afgTurnOnOff(userstate)

    def afgOnOffOffOn(self):
        state = self.afgWrite("OUTP?")
        state = (state[0] == '0')
        self.afgTurnOnOff(state)

    def afgSetFreqList(self):
        self.afgClear()
        self.afgSetSine()
        self.afgSetModeList()

        self.afgSetRFAmp()
        afglist = self.genFreqList()
        #afglist = self.genFreqList_special()
        # Join the list so it is ready for the AFG
        afglist = ",".join(afglist)
        self.afgWrite("LIST:FREQ " + afglist)
        #self.afgWrite("LIST:FREQ "+afglist)
        self.freqListMessage()

        self.afgResetTrigger()

    def afgSetRFAmp(self):
        #rfamp = str(Midas.varget("/Experiment/Variables/MPETRFAmp"))
        #rfamp = "0.300"
        self.RFAmplitude = self.calcRFAmplitude()
        self.afgWrite("VOLT " + str(self.RFAmplitude))

    def getFrequencyCentre(self):
        """
        Get user input from the ODB and calculate the respective centre
        frequencies using the "calcFreq" module.

        Expected Midas Variable Structure:
            semi-colon delimited and equal-length lists.

        If any list is too short, the last value in the list is appended
        so that each list is the same length.
        """
        #self.FreqC = str(Midas.varget("/Experiment/Variables/" +
        #                              "Center Frequency"))
        self.FreqC = str(Midas.varget(self.varFreqC))
        self.FreqC = [x.strip() for x in self.FreqC.split(";")]

        #temp = Midas.varget("/Experiment/Variables/Species")
        temp = Midas.varget(self.varSpecies)
        temp = [x.strip() for x in temp.split(";")]
        #self.Charge = Midas.varget("/Experiment/Variables/Charge")
        self.Charge = Midas.varget(self.varCharge)
        self.Charge = [x.strip() for x in self.Charge.split(";")]

        listmax = max([len(x) for x in [self.FreqC, temp, self.Charge]])
        print listmax
        for mylist in [self.FreqC, temp, self.Charge]:
            if mylist == [""]:
                raise Exception("afgcontrol: An ODB variable is empty!")
            while len(mylist) < listmax:
                mylist.append(mylist[-1])
            #print mylist

        self.Species = []
        # 2015.10.6 ATG: Bug in this code, as it tries to lower() a float if
        # the list is longer than 1. I changed the code so that it just appends
        # any list that is too short with a value before it.
        #for i in range(len(temp)):
        #    self.Species.append(temp[i] + " " + self.Charge[i])
        #    for i in range(len(self.FreqC)):
        #        try:
        #            if self.FreqC[i].lower() == 'freqc':
        #                self.FreqC[i] = self.CF.cyclotron_frequencies(
        #                    self.Species[i])[0]
        #            else:
        #                self.FreqC[i] = float(self.FreqC[i])
        #                print self.FreqC
        #        except:
        #            pass
        for i in range(len(temp)):
            self.Species.append(temp[i] + " " + self.Charge[i])
            if self.FreqC[i].lower() == 'freqc':
                self.FreqC[i] = self.CF.cyclotron_frequencies(
                    self.Species[i])[0]
            else:
                self.FreqC[i] = float(self.FreqC[i])
        print self.FreqC

    def getFrequencyModulation(self):
        """
        Get the frequency modulation from the ODB.

        If the variable is empty, set the frequency modulation to zero.
        """
        #self.FreqMod = str(Midas.varget("/Experiment/Variables/" +
        #                                "Frequency Deviation"))
        self.FreqMod = str(Midas.varget(self.varFreqMod))
        try:
            self.FreqMod = [float(x.strip()) for x in self.FreqMod.split(";")]
        except ValueError:
            self.FreqMod = [0.0]
        print self.FreqMod

    def getNumberOfPoints(self):
        self.NumberPoints = int(Midas.varget("/Equipment/TITAN_ACQ/" +
                                             "ppg cycle/begin_ramp/" +
                                             "loop count"))
        print self.NumberPoints

    def genFreqList(self):
        """
        Given a semi-colon delimited list of center frequencies and
        modulations from the odb generate a frequency list.

        The number of points defined in the odb should be a multiple
        of the number of frequencies.  If not the 'extra' points are
        included in the last frequency to be scanned.

        If the frequency modulation list is shorter than the center
        frequency list then the last modulation listed is repeated
        until the lists are the same length.

        If the Frequency Modulation list is longer than the center
        frequency list then the 'extra' elements are ignored.
        """
        self.freqlist = []  # reset freqlist
        self.getFrequencyCentre()
        self.getFrequencyModulation()
        self.getNumberOfPoints()
        #self.NumberPoints = 34

        while(len(self.FreqMod) < len(self.FreqC)):
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

        # Update the start and end frequencies in the odb
        #Midas.varset("/Experiment/Variables/StartFreq (MHz)",
        Midas.varset(self.varStartFreq,
                     (float(self.freqlist[0]) / 1000000.))
        #Midas.varset("/Experiment/Variables/EndFreq (MHz)",
        Midas.varset(self.varStopFreq,
                     (float(self.freqlist[-1]) / 1000000.))

        print self.freqlist
        fltemp = map(lambda x, y, z: "(" + str(x) + ", "
                     + str(y) + ", " + str(z) + ")",
                     self.FreqC, self.FreqMod, n)
        fltemp = "; ".join(fltemp)
        #Midas.varset("/Experiment/Variables/Quad FreqList", fltemp)
        Midas.varset(self.varFreqList, fltemp)
        return self.freqlist

    #def genFreqList_special(self):
    #    """
    #    NOTE:
    #        This function was built specifically to test "frequency
    #        modulated" Ramsey excitations. There is no claim that
    #        the code here is correct. It has not been thoughly tested.
    #        Use at your own risk.
    #
    #    Given a semi-colon delimited list of center frequencies and
    #    modulations from the odb generate a frequency list.
    #
    #    The number of points defined in the odb should be a multiple of the
    #    number of frequencies. If not the 'extra' points are included in the
    #    last frequency to be scanned.
    #
    #    If the frequency modulation list is shorter than the center frequency
    #    list then the last modulation listed is repeated until the lists are
    #    the same length.
    #
    #    If the Frequency Modulation list is longer than the center frequency
    #    list then the 'extra' elements are ignored.
    #    """
    #    self.freqlist = []  # reset freqlist
    #    self.getFrequencyCentre()
    #    self.getFrequencyModulation()
    #    self.getNumberOfPoints()
    #    #self.NumberPoints = 34
    #
    #    while(len(self.FreqMod) < len(self.FreqC)):
    #        self.FreqMod.append(self.FreqMod[-1])
    #        print self.FreqMod
    #
    #    n = [self.NumberPoints / len(self.FreqC)
    #         for x in range(len(self.FreqC))]
    #    # Add the left-overs to the last element
    #    n[-1] += self.NumberPoints % n[0]
    #    print n
    #
    #    for i in range(len(self.FreqC)):
    #        # code check says fstart is never used.
    #        #XXX DOUBLE CHECK THIS
    #        #fstart = self.FreqC[i] - self.FreqMod[i]
    #        df = 2. * self.FreqMod[i] / float(n[i] - 1)
    #        for j in range(n[i]):
    #            delta = -self.FreqMod[i] + j * df
    #            self.freqlist.append(str((self.FreqC[i] + delta) / 1000000.)
    #                                 + "E06")
    #            self.freqlist.append(str((self.FreqC[i] + 3 * delta)
    #                                     / 1000000.) + "E06")
    #
    #    # Update the start and end frequencies in the odb
    #    Midas.varset("/Experiment/Variables/StartFreq (MHz)",
    #                 (float(self.freqlist[0]) / 1000000.))
    #    Midas.varset("/Experiment/Variables/EndFreq (MHz)",
    #                 (float(self.freqlist[-1]) / 1000000.))
    #
    #    print self.freqlist
    #    fltemp = map(lambda x, y, z: "(" + str(x) + ", "
    #                 + str(y) + ", " + str(z) + ")",
    #                 self.FreqC, self.FreqMod, n)
    #    fltemp = "; ".join(fltemp)
    #    Midas.varset("/Experiment/Variables/Quad FreqList", fltemp)
    #    return self.freqlist

    def freqListMessage(self, afgName=""):
        afgName = self.afgName + '(' + self.host + ')'
        fc = [str(x) for x in self.FreqC]
        fm = [str(x) for x in self.FreqMod]
        rfamp = str(self.RFAmplitude)

        msg = afgName + "{FreqC,FreqMod} = "
        for i in range(len(self.FreqC)):
            msg = msg + "{" + fc[i] + "," + fm[i] + "}, "
            #msg = msg + "RFAmp = " + rfamp
            print msg
            #XXX Is this a bug? Shouldn't really matter.....
            # should this be outside of the loop?
        msg = msg + "RFAmp = " + rfamp
        Midas.sendmessage("FreqList", msg)

        return msg

    def calcRFAmplitude(self):
        ExTime = self.getExcitationTime()
        #calExTime = float(Midas.varget("/Experiment/Variables/" +
        #                               "MPET RF Calibration/" +
        #                               "RF Excitation Time (ms)"))
        calExTime = float(Midas.varget(self.varCalExTime))
        #calVoltage = float(Midas.varget("/Experiment/Variables/" +
        #                                "MPET RF Calibration" +
        #                                "/RF Amplitude (V)"))
        calVoltage = float(Midas.varget(self.varCalVolatage))
        #takeUser = Midas.varget("/Experiment/Edit on Start/" +
        #                        "Amplitude Override")
        takeUser = Midas.varget(self.varTakeUser)

        if takeUser == "y":
            #RFAmpCalc = float(Midas.varget("/Experiment/Variables/MPETRFAmp"))
            RFAmpCalc = float(Midas.varget(self.varRFUserAmp))
        else:
            RFAmpCalc = calVoltage * calExTime / ExTime
            #Midas.varset("/Experiment/Variables/MPETRFAmp", str(RFAmpCalc))

        # Ensure RF amplitude is at least the minimum, and less than 2.0V
        if RFAmpCalc < self.minRFAmp:
            RFAmpCalc = self.minRFAmp
        elif RFAmpCalc > self.maxRFAmp:
            RFAmpCalc = self.maxRFAmp

        # Update RF amplitude in ODB with the calculated value
        #Midas.varset("/Experiment/Variables/MPETRFAmp", str(RFAmpCalc))
        Midas.varset(self.varRFUserAmp, str(RFAmpCalc))

        return RFAmpCalc

    def getExcitationTime(self):
        ExTime = 0.
        transition = 2
        while True:
            try:
                temp = Midas.varget("/Equipment/TITAN_ACQ/ppg cycle/" +
                                    "transition_QUAD" +
                                    str(transition) +
                                    "/time offset (ms)")
                transition += 2
                ExTime += float(temp)
            except:
                break
            #if temp[-9:] == 'not found':
            #    break
            #try:
            #    ExTime += float(temp)
            #except:
            #    break
        return ExTime
