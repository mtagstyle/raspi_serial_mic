#! /usr/bin/env python
import serial
from aubio import notes, miditofreq
import alsaaudio
import numpy
import aubio
import struct

# constants
samplerate = 44100
win_s = 512
hop_s = win_s // 2
framesize = hop_s

class SerialSender:

    def __init__(self):
        self._serial = self.setup_serial()

    def setup_serial(self):
        # configure the serial connections (the parameters differs on the device you are connecting to)
        ser = serial.Serial()
        ser.port='/dev/ttyUSB0'
        ser.baudrate=115200
        ser.bytesize=serial.EIGHTBITS
        ser.parity=serial.PARITY_NONE
        ser.stopbits=serial.STOPBITS_ONE
        ser.open()
        return ser

    def send(self, data):
        # Serialize dat data fam: 2 bytes little endian
        serialized_data = struct.pack("<BHB",0x45, data, 0x60)

        self._serial.write(serialized_data)   # Serialized Data

class RealTimeNoteAnalyzer:

    def __init__(self):
        self._mic           = self.setup_mic()
        self._note_analyzer = self.setup_analyzer()
        self._serial_proxy  = SerialSender()

    def setup_mic(self):
        recorder = alsaaudio.PCM(type=alsaaudio.PCM_CAPTURE)
        recorder.setperiodsize(framesize)
        recorder.setrate(samplerate)
        recorder.setformat(alsaaudio.PCM_FORMAT_FLOAT_LE)
        recorder.setchannels(1)

        return recorder

    def setup_analyzer(self):
        note_analyzer = notes(method="default", buf_size=win_s, hop_size=hop_s, samplerate=samplerate)
        note_analyzer.set_silence(-50)
        return note_analyzer

    def run_analysis(self):
        print("Starting to listen, press Ctrl+C to stop")
        while True:
            try:
                # read data from audio input
                _, data = self._mic.read()
                # convert data to aubio float samples
                samples = numpy.fromstring(data, dtype=aubio.float_type)
                # get the note from the sample data
                new_note = self._note_analyzer(samples)

                if (new_note[0] != 0):
                    #note_str = ' '.join(["%.2f" % i for i in new_note])
                    print str(new_note)
                    frequency = int(miditofreq(new_note[0]))
                    print "To frequency: {0}".format(frequency)
                    self._serial_proxy.send(frequency)

            except KeyboardInterrupt:
                print("Ctrl+C pressed, exiting")
                break

def main():
    analyzer = RealTimeNoteAnalyzer()
    analyzer.run_analysis()

if __name__ == "__main__":
    main()