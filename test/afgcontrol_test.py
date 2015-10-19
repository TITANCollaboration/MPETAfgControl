#!/usr/bin/python

from unittest import TestCase
import mock
import afgcontrol


@mock.patch('afgcontrol.CF')
class StandAloneTests(TestCase):
    """
    Test the standalone funcitons of afgcontrol.
    """

    def test_init(self, mock_CF):
        myafg = afgcontrol.afg()

        self.assertEqual(myafg.maxRFAmp, 4.8)
        self.assertEqual(myafg.minRFAmp, 0.002)

    def test_setip(self, mock_CF):
        myafg = afgcontrol.afg()
        myafg.setip("myipaddress.com")

        self.assertEqual(myafg.host, "myipaddress.com")

    def test_setPort(self, mock_CF):
        myafg = afgcontrol.afg()
        myafg.setPort(1000)

        self.assertEqual(myafg.port, "1000")


@mock.patch('afgcontrol.time')
@mock.patch('afgcontrol.CF')
@mock.patch('afgcontrol.Midas')
@mock.patch('afgcontrol.telnetlib')
class DependantTests(TestCase):
    def test_openConnection(self, mock_telnet, mock_Midas, mock_CF, mock_time):
        mock_Midas.varget.return_value = "mpetquad"
        mctelnet = mock_telnet.Telnet.return_value
        mctelnet.expect.return_value = [0, "somethingelse"]

        myafg = afgcontrol.afg()
        myafg.openConnection()

        #self.assertTrue(myafg.connectionOpen)
        self.assertEqual(myafg.host, "mpetquad")
        self.assertEqual(myafg.port, "5024")
        mock_telnet.Telnet.assert_called_once_with('mpetquad', '5024', 9999)
        self.assertEqual(mctelnet.expect.call_count, 1)

        myafg = afgcontrol.afg()

        #self.assertFalse(myafg.connectionOpen)
        myafg.openConnection("myip.com")
        #self.assertTrue(myafg.connectionOpen)

        self.assertEqual(myafg.host, "myip.com")

        myafg = afgcontrol.afg()
        myafg.openConnection(Port="1000", ipAddress="myip.com")

        self.assertEqual(myafg.port, "1000")
        #self.assertTrue(myafg.connectionOpen)

    def test_closeConnection(self, mock_telnet, mock_Midas,
                             mock_CF, mock_time):
        mock_Midas.varget.return_value = "mpetquad"
        mctelnet = mock_telnet.Telnet.return_value
        mctelnet.expect.return_value = [0, "somethingelse"]

        myafg = afgcontrol.afg()
        myafg.openConnection()

        myafg.closeConnection()

        mctelnet.close.assert_called_once_with()

    def test_afgWrite(self, mock_telnet, mock_Midas, mock_CF, mock_time):
        mock_Midas.varget.return_value = "mpetquad"
        mctelnet = mock_telnet.Telnet.return_value
        mctelnet.expect.return_value = [0, "somethingelse", "test\r"]

        myafg = afgcontrol.afg()
        myafg.openConnection()
        result = myafg.afgWrite("my command")
        expected = ["test"]

        self.assertEqual(result, expected)

        mctelnet.write.assert_called_once_with("my command" + "\r")
        mock_time.sleep.assert_called_once_with(myafg.sleepTime)

    def test_afgClear(self, mock_telnet, mock_Midas, mock_CF, mock_time):
        myafg = afgcontrol.afg()
        myafg.afgWrite = mock.MagicMock()

        myafg.afgClear()
        expected = [mock.call("ABOR"), mock.call("*CLS")]

        self.assertEqual(myafg.afgWrite.call_args_list, expected)

    def test_afgResetTrigger(self, mock_telnet, mock_Midas, mock_CF,
                             mock_time):
        myafg = afgcontrol.afg()
        myafg.afgClear = mock.MagicMock()
        myafg.afgWrite = mock.MagicMock()

        myafg.afgResetTrigger()

        myafg.afgWrite.assert_called_once_with("INIT:CONT ON")

    def test_afgSetSine(self, mock_telnet, mock_Midas, mock_CF, mock_time):
        myafg = afgcontrol.afg()
        myafg.afgWrite = mock.MagicMock()

        myafg.afgSetSine()

        myafg.afgWrite.assert_called_once_with("FUNC SIN")

    def test_afgSetModeList(self, mock_telnet, mock_Midas, mock_CF,
                            mock_time):
        myafg = afgcontrol.afg()
        myafg.afgWrite = mock.MagicMock()

        myafg.afgSetModeList()

        myafg.afgWrite.assert_called_once_with("FREQ:MODE LIST")

    def test_afgSetOutputLoad(self, mock_telnet, mock_Midas, mock_CF,
                              mock_time):
        myafg = afgcontrol.afg()
        myafg.afgWrite = mock.MagicMock()

        myafg.afgSetOutputLoad()
        myafg.afgWrite.assert_called_once_with("OUTP:LOAD " + "INF")

        myafg.afgWrite.reset_mock()

        myafg.afgSetOutputLoad("50")
        myafg.afgWrite.assert_called_once_with("OUTP:LOAD " + "50")

    def test_afgSetTrigger(self, mock_telnet, mock_Midas, mock_CF,
                           mock_time):
        myafg = afgcontrol.afg()
        myafg.afgWrite = mock.MagicMock()

        myafg.afgSetTigger()
        myafg.afgWrite.assert_called_once_with("TRIG:SOUR EXT")

    def test_afgOn(self, mock_telnet, mock_Midas, mock_CF, mock_time):
        myafg = afgcontrol.afg()
        myafg.afgWrite = mock.MagicMock()

        myafg.afgOn()

        myafg.afgWrite.assert_called_once_with("OUTP ON")
        self.assertEqual(mock_Midas.varset.call_count, 1)

    def test_afgOff(self, mock_telnet, mock_Midas, mock_CF, mock_time):
        myafg = afgcontrol.afg()
        myafg.afgWrite = mock.MagicMock()

        myafg.afgOff()

        myafg.afgWrite.assert_called_once_with("OUTP OFF")
        self.assertEqual(mock_Midas.varset.call_count, 1)

    def test_afgTurnOnOff(self, mock_telnet, mock_Midas, mock_CF, mock_time):
        myafg = afgcontrol.afg()
        myafg.afgOn = mock.MagicMock()
        myafg.afgOff = mock.MagicMock()

        myafg.afgTurnOnOff(True)

        myafg.afgOn.assert_called_once_with()
        myafg.afgOff.assert_not_called()
        self.assertEqual(mock_Midas.sendmessage.call_count, 1)
        mock_Midas.sendmessage.assert_called_once_with(myafg.afgName,
                                                       "AFG is on")

        myafg.afgOn.reset_mock()
        mock_Midas.reset_mock()

        myafg.afgTurnOnOff(False)

        myafg.afgOn.assert_not_called()
        myafg.afgOff.assert_called_once_with()
        self.assertEqual(mock_Midas.sendmessage.call_count, 1)
        mock_Midas.sendmessage.assert_called_once_with(myafg.afgName,
                                                       "AFG is off")

    def test_afgStartMenuOnOff(self, mock_telnet, mock_Midas, mock_CF,
                               mock_time):
        mock_Midas.varget.return_value = 'y'
        myafg = afgcontrol.afg()
        myafg.afgTurnOnOff = mock.MagicMock()

        myafg.afgStartMenuOnOff()

        myafg.afgTurnOnOff.assert_called_once_with(True)

        myafg.afgTurnOnOff.reset_mock()

        mock_Midas.varget.return_value = 'n'

        myafg.afgStartMenuOnOff()

        myafg.afgTurnOnOff.assert_called_once_with(False)

    def test_afgOnOffOffOn(self, mock_telnet, mock_Midas, mock_CF, mock_time):
        myafg = afgcontrol.afg()
        myafg.afgWrite = mock.MagicMock()
        myafg.afgWrite.return_value = ['0']
        myafg.afgTurnOnOff = mock.MagicMock()

        myafg.afgOnOffOffOn()

        myafg.afgTurnOnOff.assert_called_once_with(True)

        myafg.afgWrite.return_value = ['1']
        myafg.afgTurnOnOff.reset_mock()

        myafg.afgOnOffOffOn()

        myafg.afgTurnOnOff.assert_called_once_with(False)

    def test_afgSetFreqList(self, mock_telnet, mock_Midas, mock_CF, mock_time):
        myafg = afgcontrol.afg()
        myafg.afgWrite = mock.MagicMock()
        myafg.afgClear = mock.MagicMock()
        myafg.afgSetSine = mock.MagicMock()
        myafg.afgSetModeList = mock.MagicMock()
        myafg.afgSetRFAmp = mock.MagicMock()
        myafg.genFreqList = mock.MagicMock(return_value=["1000000",
                                                         "1000001",
                                                         "1000002"])
        myafg.freqListMessage = mock.MagicMock()
        myafg.afgResetTrigger = mock.MagicMock()

        myafg.afgSetFreqList()
        expected = "LIST:FREQ 1000000,1000001,1000002"

        myafg.afgWrite.assert_called_once_with(expected)
        myafg.afgClear.assert_called_once_with()
        myafg.afgSetSine.assert_called_once_with()
        myafg.afgSetModeList.assert_called_once_with()
        myafg.afgSetRFAmp.assert_called_once_with()
        myafg.genFreqList.assert_called_once_with()
        myafg.freqListMessage.assert_called_once_with()
        myafg.afgResetTrigger.assert_called_once_with()

    def test_afgSetRFAmp(self, mock_telnet, mock_Midas, mock_CF, mock_time):
        myafg = afgcontrol.afg()
        myafg.calcRFAmplitude = mock.MagicMock(return_value=1.0)
        myafg.afgWrite = mock.MagicMock()

        myafg.afgSetRFAmp()
        expected = "1.0"

        myafg.calcRFAmplitude.assert_called_once_with()
        myafg.afgWrite.assert_called_once_with("VOLT " + expected)

    def test_getFrequencyCentre(self, mock_telnet, mock_Midas, mock_CF,
                                mock_time):
        mock_Midas.varget.side_effect = ["1000000", "1K39", "1"]
        myafg = afgcontrol.afg()

        myafg.getFrequencyCentre()

        self.assertEqual(mock_Midas.varget.call_count, 3)
        self.assertEqual(myafg.FreqC, [1000000.0])
        self.assertEqual(myafg.Species, ["1K39 1"])
        self.assertEqual(myafg.Charge, ["1"])

        mock_Midas.varget.reset_mock()
        mock_Midas.varget.side_effect = ["FrEQc", "1K39", "1"]
        mock_CF.calcFreq().cyclotron_frequencies = mock.MagicMock(
            return_value=[1000000.0, "otherstuff", "whatever"])

        myafg.getFrequencyCentre()

        self.assertEqual(mock_Midas.varget.call_count, 3)
        self.assertEqual(myafg.FreqC, [1000000.0])
        self.assertEqual(myafg.Species, ["1K39 1"])
        self.assertEqual(myafg.Charge, ["1"])
        mock_CF.calcFreq().cyclotron_frequencies\
            .assert_called_once_with("1K39 1")

        mock_Midas.varget.reset_mock()
        mock_CF.calcFreq().cyclotron_frequencies.reset_mock()
        mock_Midas.varget.side_effect = ["FreqC ; 2000", "4C12:10H1  ;1U238",
                                         "1; 92"]
        mock_CF.calcFreq().cyclotron_frequencies = mock.MagicMock(
            return_value=[1000.0, "something", "the other"])
        myafg.getFrequencyCentre()

        self.assertEqual(mock_Midas.varget.call_count, 3)
        self.assertEqual(myafg.FreqC, [1000.0, 2000.0])
        self.assertEqual(myafg.Species, ["4C12:10H1 1", "1U238 92"])
        self.assertEqual(myafg.Charge, ["1", "92"])
        mock_CF.calcFreq().cyclotron_frequencies\
            .assert_called_once_with("4C12:10H1 1")

        mock_Midas.varget.reset_mock()
        mock_CF.calcFreq().cyclotron_frequencies.reset_mock()
        mock_Midas.varget.side_effect = ["2000", "4C12:10H1  ;1U238",
                                         "1; 92"]
        myafg.getFrequencyCentre()

        self.assertEqual(mock_Midas.varget.call_count, 3)
        self.assertEqual(myafg.FreqC, [2000.0, 2000.0])
        self.assertEqual(myafg.Species, ["4C12:10H1 1", "1U238 92"])
        self.assertEqual(myafg.Charge, ["1", "92"])
        mock_CF.calcFreq().cyclotron_frequencies\
            .assert_not_called()

        mock_Midas.varget.reset_mock()
        mock_CF.calcFreq().cyclotron_frequencies.reset_mock()
        mock_Midas.varget.side_effect = ["2000", "4C12:10H1  ;1U238",
                                         ""]
        # Assert exception is raised if one of the ODB variables is empty
        self.assertRaises(Exception, myafg.getFrequencyCentre)

    def test_getFrequencyModulation(self, mock_telnet, mock_Midas, mock_CF,
                                    mock_time):
        mock_Midas.varget.return_value = "10"
        myafg = afgcontrol.afg()

        myafg.getFrequencyModulation()

        self.assertEqual(mock_Midas.varget.call_count, 1)
        self.assertEqual(myafg.FreqMod, [10.0])

        mock_Midas.varget.reset_mock()
        mock_Midas.varget.return_value = "   "

        myafg.getFrequencyModulation()

        self.assertEqual(mock_Midas.varget.call_count, 1)
        self.assertEqual(myafg.FreqMod, [0.0])

        mock_Midas.varget.reset_mock()
        mock_Midas.varget.return_value = "1; 2 ;      3     "

        myafg.getFrequencyModulation()

        self.assertEqual(mock_Midas.varget.call_count, 1)
        self.assertEqual(myafg.FreqMod, [1.0, 2.0, 3.0])

    def test_getNumberOfPoints(self, mock_telnet, mock_Midas, mock_CF,
                               mock_time):
        mock_Midas.varget.return_value = "41"
        myafg = afgcontrol.afg()

        myafg.getNumberOfPoints()

        self.assertEqual(mock_Midas.varget.call_count, 1)
        self.assertEqual(myafg.NumberPoints, 41)

    def test_genFreqList(self, mock_telnet, mock_Midas, mock_CF,
                         mock_time):
        myafg = afgcontrol.afg()
        myafg.getFrequencyCentre = mock.MagicMock()
        myafg.getFrequencyModulation = mock.MagicMock()
        myafg.getNumberOfPoints = mock.MagicMock()

        # Check with a single frequency
        myafg.FreqC, myafg.FreqMod, myafg.NumberPoints = (
            [1000000.0], [20.0], 41)

        myafg.genFreqList()

        self.assertEqual(mock_Midas.varset.call_count, 3)
        self.assertEqual(len(myafg.freqlist), 41)
        self.assertEqual(myafg.freqlist[0], "0.99998E06")
        self.assertEqual(myafg.freqlist[-1], "1.00002E06")

        # Check with two frequencies
        mock_Midas.reset_mock()
        myafg.FreqC, myafg.FreqMod, myafg.NumberPoints = (
            [1000000.0, 2000000.0], [20.0, 10.0], 41)

        myafg.genFreqList()
        self.assertEqual(mock_Midas.varset.call_count, 3)
        self.assertEqual(len(myafg.freqlist), 41)
        self.assertEqual(myafg.freqlist[0], "0.99998E06")
        self.assertEqual(myafg.freqlist[-1], "2.00001E06")

        # another check with two frequencies
        mock_Midas.reset_mock()
        myafg.FreqC, myafg.FreqMod, myafg.NumberPoints = (
            [1000000.0, 1000000.0], [20.0, 20.0], 40)

        myafg.genFreqList()
        self.assertEqual(mock_Midas.varset.call_count, 3)
        self.assertEqual(len(myafg.freqlist), 40)
        self.assertEqual(myafg.freqlist[0], "0.99998E06")
        self.assertEqual(myafg.freqlist[-1], "1.00002E06")
        self.assertEqual(myafg.freqlist[:20], myafg.freqlist[20:])

        # Check with only one Frequency Modulation
        mock_Midas.reset_mock()
        myafg.FreqC, myafg.FreqMod, myafg.NumberPoints = (
            [1000000.0, 1000000.0], [20.0], 40)

        myafg.genFreqList()
        self.assertEqual(mock_Midas.varset.call_count, 3)
        self.assertEqual(len(myafg.freqlist), 40)
        self.assertEqual(myafg.freqlist[0], "0.99998E06")
        self.assertEqual(myafg.freqlist[-1], "1.00002E06")
        self.assertEqual(myafg.freqlist[:20], myafg.freqlist[20:])

        # Check with a small frequency modulation
        mock_Midas.reset_mock()
        myafg.FreqC, myafg.FreqMod, myafg.NumberPoints = (
            [1000000.0], [0.002], 41)

        myafg.genFreqList()
        self.assertEqual(mock_Midas.varset.call_count, 3)
        self.assertEqual(len(myafg.freqlist), 41)
        self.assertEqual(myafg.freqlist[0], "0.999999998E06")
        self.assertEqual(myafg.freqlist[1], "0.9999999981E06")
        self.assertEqual(myafg.freqlist[-1], "1.000000002E06")

        # Check that returned list is correct
        mock_Midas.reset_mock()
        myafg.FreqC, myafg.FreqMod, myafg.NumberPoints = (
            [1000000.0], [1.0], 3)

        result = myafg.genFreqList()
        expected = ["0.999999E06", "1.0E06", "1.000001E06"]
        self.assertEqual(mock_Midas.varset.call_count, 3)
        self.assertEqual(len(myafg.freqlist), 3)
        self.assertEqual(result, expected)

    def test_freqListMessage(self, mock_telnet, mock_Midas, mock_CF,
                             mock_time):
        myafg = afgcontrol.afg()
        myafg.host = "mpetquad"
        myafg.RFAmplitude = 1.0
        myafg.FreqC = [1000000.0]
        myafg.FreqMod = [1.0]

        result = myafg.freqListMessage()

        mock_Midas.sendmessage.assert_called_once_with("FreqList", result)
        mock_Midas.sendmessage.reset_mock()

        myafg.RFAmplitude = 1.0
        myafg.FreqC = [1000000.0, 2000000.0]
        myafg.FreqMod = [1.0, 2.0]

        result = myafg.freqListMessage()

        mock_Midas.sendmessage.assert_called_once_with("FreqList", result)

    def test_calcRFAmplitude(self, mock_telnet, mock_Midas, mock_CF,
                             mock_time):
        myafg = afgcontrol.afg()

        # do a normal call, with automated RF calibration
        myafg.getExcitationTime = mock.MagicMock(return_value=0.100)
        mock_Midas.varget.side_effect = ["1", "0.1", "n"]

        result = myafg.calcRFAmplitude()

        self.assertEqual(result, 1 * 0.1 / 0.1)
        self.assertEqual(mock_Midas.varset.call_count, 1)

        # do a call with user override of RF amplitude
        mock_Midas.reset_mock()
        mock_Midas.varget.side_effect = ["1", "0.1", "y", "0.5"]

        result = myafg.calcRFAmplitude()

        self.assertEqual(result, 0.5)
        self.assertEqual(mock_Midas.varset.call_count, 1)

        # do a call where RF amp < RFmin
        mock_Midas.reset_mock()
        mock_Midas.varget.side_effect = ["1", "0.1", "y", "0.00001"]

        result = myafg.calcRFAmplitude()

        self.assertEqual(result, myafg.minRFAmp)
        self.assertEqual(mock_Midas.varset.call_count, 1)

        # do a call where RF amp  RFmaz
        mock_Midas.reset_mock()
        mock_Midas.varget.side_effect = ["1", "0.1", "y", "100"]

        result = myafg.calcRFAmplitude()

        self.assertEqual(result, myafg.maxRFAmp)
        self.assertEqual(mock_Midas.varset.call_count, 1)

    def test_getExcitationTime(self, mock_telnet, mock_Midas, mock_CF,
                               mock_time):
        myafg = afgcontrol.afg()
        # Find one QUAD var in ODB, and raise exception
        # simulates normal quad excitation
        mock_Midas.varget.side_effect = ["0.1", Exception()]

        result = myafg.getExcitationTime()

        self.assertEqual(result, 0.1)
        self.assertEqual(mock_Midas.varget.call_count, 2)

        # Find two QUAD var in ODB, and the raise exception
        # simulations ramsey excitation
        mock_Midas.varget.reset_mock()
        mock_Midas.varget.side_effect = ["0.1", "0.1", Exception()]

        result = myafg.getExcitationTime()

        self.assertEqual(result, 0.2)
        self.assertEqual(mock_Midas.varget.call_count, 3)
