import sys,os,hmac,hashlib,base64,crc16pure,argparse,zipfile,StringIO,struct,ctypes
from intelhex import bin2hex
from intelhex import hex2bin

class InitPktCfg:
    def __init__(self, dev_type, dev_rev, app_ver, sd_ver, key_file, image_file):
        self.DeviceType         = dev_type
        self.DeviceRevision     = dev_rev
        self.ApplicationVersion = app_ver
        self.SoftDeviceVersions = sd_ver
        self.HMAC               = ""
        self.init_pkt           = ""
        
        # Generate bin file
        bin_file = StringIO.StringIO()
        hex2bin(image_file, bin_file)
        
        fkey      = open(key_file, "r")
        self.key  = fkey.read().strip()
        self.msg  = bin_file.getvalue()
        
        if len(self.key) < 32:
            print "ERROR: Expected key length 32, but got key length " + str(len(self.key))
            exit(1)
        
        self.HMAC      = self.GenerateHMAC(self.key, self.msg, image_file.replace("hex","bin"))
        self.init_pkt += self.GenerateInitPkt()
        self.init_pkt += self.HMAC
        
        fkey.close()
        
    def GetInitPkt(self):
        return self.init_pkt
        
    def GetMsg(self):
        msg = self.msg
        self.msg = ""
        return msg
        
    def GetKey(self):
        return self.key
                
    def GenerateCRC(self, image):
        self.CRC = crc16pure.crc16xmodem(image, crc=0xFFFF)
        
    def GenerateInitPkt(self):
        pkt = ""
        pkt += struct.pack("<H", self.DeviceType)
        pkt += struct.pack("<H", self.DeviceRevision)
        pkt += struct.pack("<I", self.ApplicationVersion)
        pkt += struct.pack("<H", len(self.SoftDeviceVersions))
        for sd in self.SoftDeviceVersions:
            pkt += struct.pack("<H", sd)
        
        return pkt
        
    def GenerateHMAC(self, key, msg, imageName):
        # print "len(msg) = " + str(len(msg))
        # print "len(key) = " + str(len(key))
        
        dig = hmac.new(key, msg=msg, digestmod=hashlib.sha256).digest()
        
        human_readable = ""
        for x in dig:
            human_readable += "%02x" % (ord(x),)
            
        print human_readable + " *" + imageName
        
        return dig

def GenerateBinAndDat(args, type):
    # Generate .bin and .dat file
    if type == "application":
        init_data = InitPktCfg(int(args.dev_type), int(args.dev_revision), int(args.application_version), map(lambda x:int(x.strip(),16), args.sd_req.split(",")), args.key, args.application)
    elif type == "bootloader":
        init_data = InitPktCfg(int(args.dev_type), int(args.dev_revision), int(args.application_version), map(lambda x:int(x.strip(),16), args.sd_req.split(",")), args.key, args.bootloader)
    elif type == "softdevice":
        init_data = InitPktCfg(int(args.dev_type), int(args.dev_revision), int(args.application_version), map(lambda x:int(x.strip(),16), args.sd_req.split(",")), args.key, args.softdevice)
    else:
        print "ERROR invalid type"
        exit(1)
        
    bin = init_data.GetMsg()
    dat = init_data.GetInitPkt()
    key = init_data.GetKey()
    
    return bin,dat,key
            
parser = argparse.ArgumentParser()
# This will parse any string starting with 0x as base 16.
auto_int = lambda x: int(x, 0)
auto_float = lambda x: float(x)

parser.add_argument('--dfu-ver', required=False, type=auto_float,
                    help='DFU packet version to use')
parser.add_argument('--dev-type', required=False, type=auto_int,
                    help='Device type')
parser.add_argument('--dev-revision', required=False, type=auto_int, metavar='DEV_REV',
                    help='Device revision')
parser.add_argument('--application-version', required=False, type=auto_int, metavar='APP_VER',
                    help='Application version')
parser.add_argument('--key', required=True, type=str,
                    help='Name of key file to use for encrypting the package')
parser.add_argument('--key-output', required=False, type=str,
                    help='Name of file to use if key is to be written to .hex')
parser.add_argument('--key-address', required=False, type=str,
                    help='Memory address where the key should be placed. Defaults to 0x0003F800.')
parser.add_argument('--sd-req', required=True, type=str,
                    help="SoftDevice requirement. What SoftDevice "
                         "is required to already be present on the target device. "
                         "Should be a list of firmware IDs. Example: --sd-req 0x4F,0x5A. "
                         "Use 0xFFFE to support all SoftDevices"
                         "See: http://developer.nordicsemi.com/nRF51_SDK/nRF51_SDK_v8.x.x/doc/8.0.0/s110/html/a00093.html")
parser.add_argument('--application', required=False, type=str,
                    help='The application firmware .hex file')
parser.add_argument('--bootloader', required=False, type=str, metavar='BL',
                    help='The bootloader firmware .hex file')
parser.add_argument('--softdevice', required=False, type=str, metavar='SD',
                    help='The SoftDevice firmware .hex file')
parser.add_argument('zipfile', nargs=1, type=str,
                    help='The package filename')
args = parser.parse_args()

if args.application == None and args.bootloader == None and args.softdevice == None:
    print "Nothing to do"
    exit(1)
    
key      = ""
    
zf  = zipfile.ZipFile(args.zipfile[0], mode='w',compression=zipfile.ZIP_DEFLATED)
    
if args.application != None:
    bin, dat, key = GenerateBinAndDat(args, "application")
    zf.writestr("application.bin", bin)
    zf.writestr("application.dat", dat)
        
if args.bootloader != None:
    bin, dat, key = GenerateBinAndDat(args, "bootloader")
    zf.writestr("bootloader.bin", bin)
    zf.writestr("bootloader.dat", dat)
        
if args.softdevice != None:
    bin, dat, key = GenerateBinAndDat(args, "softdevice")
    zf.writestr("softdevice.bin", bin)
    zf.writestr("softdevice.dat", dat)

zf.close()

if args.key_output != None:
    key_address = int(args.key_address,16)
    if (key_address == None):
        key_address = 0x0003F800

    key_bin = StringIO.StringIO()
    key_bin.write(key)
    fout = open(args.key_output.replace("hex","bin"), "wb")
    fout.write(key)
    fout.close()
    bin2hex(args.key_output.replace("hex","bin"), args.key_output, key_address)
