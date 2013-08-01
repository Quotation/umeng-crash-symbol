import sys, os, re, glob, subprocess, biplist
import tornado.ioloop, tornado.web, tornado.template
from tornado.web import asynchronous


serverroot = os.path.abspath(os.path.dirname(__file__))
symbolsdir = os.path.join(serverroot, "symbols")
templateLoader = tornado.template.Loader(serverroot)
serverhost = 'localhost'
serverport = '80'

# dSYM UDID => (dir, app bundle, dSYM)
symbolVersions = {}


def loadVersions():
    for dir in os.walk(symbolsdir).next()[1]:
        dir = os.path.join(symbolsdir, dir)
        os.chdir(dir)
        apps = glob.glob('*.app')
        dsyms = glob.glob('*.dSYM')
        if not apps or not dsyms:
            print "Error: invalid version", dir
            continue
        dsym = os.path.join(dir, dsyms[0])
        udid = getDsymUDID(dsym)
        if not udid:
            print "Error: invalid dSYM", dsym
            continue
        symbolVersions[udid] = (dir, apps[0], dsyms[0])
    #print symbolVersions

def getDsymUDID(dsym):
    # mdls output format:
    # (
    #   "15BF90AE-951A-3DE7-B5E8-311E3D14C320"
    # )
    udid = subprocess.check_output("mdls -name com_apple_xcode_dsym_uuids -raw \"" + dsym + "\"", shell=True)
    return re.findall(r'".+?"', udid)[0][1:-1]

def getAppExecutable(app):
    plist = biplist.readPlist(os.path.join(app, "Info.plist"))
    return plist["CFBundleExecutable"]

def getSymbol(dsymUDID, address, slide, baseAddr, arch):
    if dsymUDID not in symbolVersions:
        return None
    dir, app, _ = symbolVersions[dsymUDID]
    executable = getAppExecutable(app)
    realAddr = hex(int(address, 16) + int(slide, 16) - int(baseAddr, 16))
    os.chdir(dir)
    cmd = "atos -arch %s -o '%s'/'%s' %s" % (arch, app.decode("utf-8"), executable, realAddr)
    output = subprocess.check_output(cmd, shell=True)
    output = re.sub(r"\(in .+?\)\s", "", output).strip()
    return output

# crash log format:
# *** -[NSDictionary initWithDictionary:copyItems:]: dictionary argument is not an NSDictionary
# (null)
# (
#     0   CoreFoundation                      0x328632bb  + 186
#     1   libobjc.A.dylib                     0x3a70e97f objc_exception_throw + 30
#     2   CoreFoundation                      0x327efff5  + 212
#     3   CoreFoundation                      0x327eff0b  + 42
#     4   ????????????                        0x0009ff8f ???????????? + 233359
#     5   ????????????                        0x0009fefb ???????????? + 233211
#     29  libsystem_c.dylib                   0x3ab651d8 thread_start + 8
# )
# 
# dSYM UUID: 15BF90AE-951A-3DE7-B5E8-311E3D14C320
# CPU Type: armv7
# Slide Address: 0x00001000
# Binary Image: ????
# Base Address: 0x00067000
#
# - or like this -
#
# 	5   AppBinaryImage                        0x4d1841 _ZN6GBIter7AdvanceEjPb + 36
#	6   AppBinaryImage                        0x2bb1d1 _ZNSt6vectorIcSaIcEE13_M_assign + 1648

def convertUmengCrashReport(report):
    dsymUDID = re.search(r"dSYM UUID:\s*(.+)\s*", report).group(1)
    arch = re.search(r"CPU Type:\s*(.+)\s*", report).group(1)
    slide = re.search(r"Slide Address:\s*(.+)\s*", report).group(1)
    baseAddr = re.search(r"Base Address:\s*(.+)\s*", report).group(1)
    imageName = re.search(r"Binary Image:\s*(.+)\s*", report).group(1)
    
    def replaceUnknownSymbol_Question(match):
        addr = match.group(2)
        return match.group(1) + getSymbol(dsymUDID, addr, slide, baseAddr, arch)
    
    def replaceUnknownSymbol_Normal(match):
        addr = match.group(2)
        return match.group(1) + getSymbol(dsymUDID, addr, '0', '0', arch)
    
    report = re.sub(r"((0x.+)\s+)(\?+|_mh_execute_header).*", replaceUnknownSymbol_Question, report)
    report = re.sub(r"(" + imageName + r"\s+(0x.+?)\s+).*", replaceUnknownSymbol_Normal, report)
    return report


class MainHandler(tornado.web.RequestHandler):
    @asynchronous
    def get(self):
        self.finish(templateLoader.load("index.html").generate(host=serverhost, port=serverport))

class ConvertHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
    
    @asynchronous        
    def post(self):
        report = self.get_argument("crashreport")
        self.finish(convertUmengCrashReport(report))

application = tornado.web.Application([
    (r"/",                  MainHandler),
    (r"/convert",           ConvertHandler),
], gzip=True)


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        serverhost = sys.argv[1]
    if len(sys.argv) >= 3:
        serverport = sys.argv[2]
    
    loadVersions()
    if not symbolVersions:
        print "No symbols found at", symbolsdir
        exit(1)
    
    application.listen(serverport)
    print "Server started -", "http://%s:%s"%(serverhost, serverport)
    tornado.ioloop.IOLoop.instance().start()
