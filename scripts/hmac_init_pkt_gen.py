import sys,os,hmac,hashlib,base64,crc16pure
from intelhex import bin2hex
from intelhex import hex2bin

class InitPktCfg:
    def __init__(self, InitFile):
        self.DeviceType         = 0x0000
        self.DeviceRevision     = 0x0000
        self.ApplicationVersion = 0x00000000
        self.SoftDeviceVersions = []
        self.CRC                = 0x0000
        
        self.ParseInitTxt(InitFile)
    
    def ParseInitTxt(self, InitFile):
        for line in InitFile:
            if line.find("//") != -1:
                continue
            if line.find("Device type") != -1:
                self.DeviceType = int(line.split("=")[1].strip(),16)
                # print hex(self.DeviceType)
                continue
            if line.find("Device revision") != -1:
                self.DeviceRevision = int(line.split("=")[1].strip(),16)
                # print hex(self.DeviceRevision)
                continue
            if line.find("Application version") != -1:
                self.ApplicationVersion = int(line.split("=")[1].strip(),16)
                # print hex(self.ApplicationVersion)
                continue
            if line.find("Softdevice version") != -1:
                self.SoftDeviceVersions.append(int(line.split("=")[1].strip(),16))
                # print hex(self.SoftDeviceVersions[len(self.SoftDeviceVersions)-1])
                continue
                
    def GenerateCRC(self, image):
        self.CRC = crc16pure.crc16xmodem(image, crc=0xFFFF)
        
    def GenerateInitPkt(self):
        pkt = ""
        pkt += chr(self.DeviceType & 0xFF) + chr((self.DeviceType >> 8)& 0xFF) 
        pkt += chr(self.DeviceRevision & 0xFF) + chr((self.DeviceRevision >> 8)& 0xFF) 
        pkt += chr((self.ApplicationVersion >> 16) & 0xFF) + chr((self.ApplicationVersion >> 24) & 0xFF)
        pkt += chr(self.ApplicationVersion & 0xFF) + chr((self.ApplicationVersion >> 8) & 0xFF)
        pkt += chr(len(self.SoftDeviceVersions)) + chr(0)
        for sd in self.SoftDeviceVersions:
            pkt += chr(sd & 0xFF) + chr((sd >> 8) & 0xFF)
        # CRC is replaced by HMAC
        # pkt += chr(self.CRC & 0xFF) + chr((self.CRC >> 8) & 0xFF)
        
        return pkt
        
    def GenerateHMAC(self, key, msg, imageName):
        print "len(msg) = " + str(len(msg))
        print "len(key) = " + str(len(key))
        
        dig = hmac.new(key, msg=msg, digestmod=hashlib.sha256).digest()
        # dig64 = base64.b64encode(dig).decode()
        
        human_readable = ""
        for x in dig:
            human_readable += "%02x" % (ord(x),)
            
        print human_readable + " *" + imageName
        
        return dig
            
    

if len(sys.argv) < 6:
    print "usage: python " + sys.argv[0] + " image.hex init_data.txt key.txt init_pkt.dat key.hex [Offset]"
    exit(1)
    
if len(sys.argv) >= 7:
    offset = int(sys.argv[6])
    print "Offset = " + str(offset)
else:
    offset = 0
    print "\r\nOffset is currently 0. Note that for SoftDevice updates offset should equal size of the Master Boot Record\r\n"

fcfg  = open(sys.argv[2], "r")
fkey  = open(sys.argv[3], "r")
fout  = open(sys.argv[4], "wb")
    
if sys.argv[3].find(".h") != -1:
    key = fkey.read().split("\"")[1]
else:
    key = fkey.read().strip()
    
fkey.close()

if len(key) > 64:
    print "ERROR: Key must be 64 bytes or shorter"
    exit(1)
    
# Generate .bin file used for HMAC
hex2bin(sys.argv[1], sys.argv[1].replace("hex","bin"))
fin = open(sys.argv[1].replace("hex","bin"), "rb")

# Generate init packet
msg = fin.read()[offset::]
cfg = InitPktCfg(fcfg)
# CRC is replaced by HMAC
# cfg.GenerateCRC(msg)
fout.write(cfg.GenerateInitPkt())
fout.write(cfg.GenerateHMAC(key,msg,sys.argv[1]))
fout.close()
fcfg.close()
fin.close()

# Generate key hex file
fout = open(sys.argv[5].replace("hex","bin"), "wb")
# for c in key:
    # fout.write(ord(c))
fout.write(key)
fout.close()

bin2hex(sys.argv[5].replace("hex","bin"), sys.argv[5], 0x100010E0)