# License: Creative Commons Attribution-NonCommercial-NoDerivs 3.0 Unported (CC BY-NC-ND 3.0)

import canopen
import time
import threading
#import Queue
import logging
import random
import json
import numpy as np

respDict = {}
emit_lock = threading.Lock()

uvrs = []
channel = None

cobReadyEvent = threading.Event()
cob_id = 0
sdos = {}

# if no collision detected during canbus scan run id 44.
from_node_id = 44
# dummy eds file, any eds will do
edsfile = 'dummy_eds.eds'

def emit(k, v):
    with emit_lock:
        respDict[k] = v

def druckeDict():
    exchange = "daten"

    with emit_lock:
        print(respDict)

def pruefeUVR(cob_id):
    ret = 'unknown' 

    if cob_id != 0:
        node = network.add_node(cob_id, edsfile)

        try:
            vendor = node.sdo[0x1018][0x01]
            product = node.sdo[0x1018][0x02]

            if vendor.raw == 0xCB and product.raw == 0x100B:
                ret = "uvr1611"

            if vendor.raw == 0xCB and product.raw == 0x01:
                ret = "uvr16x2??"

        except (canopen.SdoCommunicationError, canopen.SdoAbortedError) as e:
            print(e)

        if ret == "uvr16x2??":
            try:
                datum = node.sdo.upload(0x2497,0x01)
                #print datum

                ret = "uvr16x2"
            except (canopen.SdoCommunicationError, canopen.SdoAbortedError) as e:
                ret = "unknown"          

    return ret

def prettyprint(bstring):
    o = [ord(b) for b in bstring]
    print(o)

def prettyprint_bitarray(u):
    bin(ord(u))

def inKommaZahl_UVR16x2(string_arr):
    arr = [ord(s) for s in string_arr]
    print(arr)

    einheiten = ("", "C", "W/qm", "l/h", "Sek", "Min", "l/Imp", "K", "%", "kW", "kWh", "MWh", "V")
    t = 0
    einheit = 'undef'

    if len(arr) >= 6:
        if arr[5] == 0:

            t = (0x0f & arr[3]) * 256 + (arr[2] & 0xff)
            t = float(t) / 10.

            if arr[1] < len(einheiten):
                einheit = einheiten[arr[1]]
        if arr[5] == 255:
            t = (256 - arr[3]) * 256 - arr[2]
            t = float(t) / 10.
            t = -t

            if arr[1] < len(einheiten):
                einheit = einheiten[arr[1]]

    return (t, einheit)

def inKommaZahl(string_arr):
    UVR1611 = 0x80
    einheiten = ("nan", "C", "W/qm", "l/h", "5", "6", "7", "8", "%")
    arr = [s for s in string_arr]    

    if len(arr) >= 6:
        t = (0x0f & arr[1]) * 256 + (arr[0] & 0xff)
        
        if arr[1] & UVR1611: # soll es hier nicht arr[0] heissen?
            t = t ^ 0xfff;
            t = -t -1;

        # TODO: hier scheint noch nicht alles gemacht
        if arr[4] == 65:
            t = t / 10.
        else:
            t = float(t)

    return (t, einheiten[arr[5]])

def sdo_schluessel(can_id, object_id, subindex_id):
    return str(can_id) + '_' + str(object_id) + '_' + str(subindex_id)

def sdo_schluessel_zurueck(s):
    return s.split('_')

def UVR16x2A_req(can_id):
    index = 8400
    for i in range(16):
        sdos[sdo_schluessel(can_id, index, i)] = None # Ausgaenge

def UVR16x2A_auswertung(can_id):
    index = 8400
    for i in range(16):
        barray = sdos[sdo_schluessel(can_id, index, i)]        
        prettyprint(barray)

def UVR16x2EBez_req(can_id):
    index = 8272
    for i in range(16):
        sdos[sdo_schluessel(can_id, index, i)] = None # Wert
        sdos[sdo_schluessel(can_id, 8207, i)] = None # Bezeichnung

def UVR16x2EBez_auswertung(can_id):
    for i in range(16):
        wert_barray = sdos[sdo_schluessel(can_id, 8272, i)]
        (wert, einheit) =  inKommaZahl_UVR16x2(wert_barray)
        
        bezeichner_barray = sdos[sdo_schluessel(can_id, 8207, i)]
        ba = bytearray(bezeichner_barray)
        bez_str = ba.decode('utf-8')

        if einheit != 'undef':
            print(wert)
            print("Bezeichner (len: %d): %s" % (len(bez_str) , bez_str))

def UVR16x2zeit_req(can_id):
    sdos[sdo_schluessel(can_id, 9367, 1)] = None #Zeit
    sdos[sdo_schluessel(can_id, 9370, 2)] = None #Datum

def UVR16x2zeit_auswertung(can_id):
    b = sdos[sdo_schluessel(can_id, 9367, 1)]
    min = (ord(b[2]) + ord(b[3])*256)
    b = sdos[sdo_schluessel(can_id, 9370, 2)]

    zeitstempel = '%02d:%02d %02d-%02d-%d' %(min/60, min%60,ord(b[2]),ord(b[3]),ord(b[4])+256*ord(b[5]))

    print(zeitstempel)

    emit('datum', zeitstempel)

    return 1

def UVR1611zeit_req(can_id):
    sdos[sdo_schluessel(can_id, 0x2014,0x01)] = None
    sdos[sdo_schluessel(can_id, 0x2015,0x01)] = None
    sdos[sdo_schluessel(can_id, 0x2016,0x01)] = None
    sdos[sdo_schluessel(can_id, 0x2012,0x01)] = None
    sdos[sdo_schluessel(can_id, 0x2011,0x01)] = None

def UVR1611zeit_auswertung(can_id):
    global sdos
    try:
        tag = sdos[sdo_schluessel(can_id, 0x2014, 0x01)]
        monat = sdos[sdo_schluessel(can_id,0x2015,0x01)]
        jahr = sdos[sdo_schluessel(can_id,0x2016,0x01)]

        stunden = sdos[sdo_schluessel(can_id,0x2012,0x01)]
        minuten = sdos[sdo_schluessel(can_id,0x2011,0x01)]

        print(tag)
        print(type(tag))

        zeitstempel = '%02d:%02d %02d-%02d-%d' %(stunden[0], minuten[0], tag[0], monat[0], 2000+jahr[0])
        print(zeitstempel)

        emit('datum', zeitstempel)
        
    except Exception as e:
        print(e)

def UVR1611leseA_req(can_id):
    sdos[sdo_schluessel(can_id, 0x20d1,0x01)] = None
    sdos[sdo_schluessel(can_id, 0x20d0,0x01)] = None

def UVR1611leseA_auswertung(can_id):
    try:
        ausg_rahmen1 = sdos[sdo_schluessel(can_id, 0x20d1, 0x01)] # Bit Maske der Ausgaenge
        aktiv = sdos[sdo_schluessel(can_id, 0x20d0, 0x01)]  # Bit Maske ob Ausgang aktiv is oder deaktiviert/ungenutzt        

        a8_1 = ausg_rahmen1[0] 
        a16_9 = ausg_rahmen1[1] 
        aktiv8_1 = aktiv[0]
        aktiv16_9 = aktiv[1] 

        print("A8-A1: %s A16-A9: %s" % ('{:08b}'.format(a8_1), '{:08b}'.format(a16_9)))
        print("aktiv8-1: %s aktiv16-9: %s" % ('{:08b}'.format(aktiv8_1), '{:08b}'.format(aktiv16_9)))

        can_id = can_id & 255

        emit(str(can_id) + "_a8-a1", '{:08b}'.format(a8_1))
        emit(str(can_id) + "_a16-a9", '{:08b}'.format(a16_9))

    except Exception as e:
        print(e)

def UVR1611leseE_req(can_id):
    idx = [(0x208d, 0x01+i) for i in range(16)] + [(0x220b, 0x11+i) for i in range(16)]
    
    for (index, subindex) in idx:
        sdos[sdo_schluessel(can_id, index, subindex)] = None        

def UVR1611leseE_auswertung(can_id):
    z = 0
    idx = [(0x208d, 0x01+i) for i in range(16)] + [(0x220b, 0x11+i) for i in range(16)]

    for (index,subindex) in idx:
        z = z + 1
        try:
            e = sdos[sdo_schluessel(can_id, index, subindex)]                                                                                              

            if(e[6] & 0x40):
                (wert, einheit) = inKommaZahl(e)
            
                if einheit != "nan": 
                    can_id = can_id & 255
                    k = str(can_id) + "_e_" + str(z)
                
                    emit(k, wert) 
        # if(ord(e[6]) & 0x10) --> es handelt sich um eine String Ausgabe
        # TODO
        except Exception as e:
            print(e)

def create_cobid(to_node_id):
    global cobReadyEvent
    # define a function spawning a thread and handing in the call paramenteres can_id, data, timestamp
    def handler(c, d, t):
        global cobReadyEvent
        global cob_id
        cob_id = d[4]
        cobReadyEvent.set()

    network.subscribe(0x400| to_node_id, handler)
    cob_pdo(to_node_id, create=True)

def destroy_cobid(to_node_id):
    global cobReadyEvent
    global cob_id

    cobReadyEvent.clear()
    cob_id = 0
    network.unsubscribe(0x400| to_node_id)
    cob_pdo(to_node_id, create=False) # Means to destroy the cob-id

def cob_pdo(to_node_id, create=True):
    global from_node_id

    # request from 44 to 1
    #  can0  42C   [8]  81 00 1F 00 01 2C 80 12
    # response back
    #  can0  401   [8]  AC 80 12 01 6C 06 00 00

    payload = bytearray(8) # full of zeros
    payload[0] = 0x80 | (to_node_id & 0x7F)
    payload[1] = 0x00 if create else 0x01 #AKTIVIERUNG 0x00 if create is True else DEAKTIVIERUNG 0x01
    payload[2] = 0x1f
    payload[3] = 0x00
    payload[4] = 0x00 | (to_node_id & 0x7F)  # server node id
    payload[5] = 0x00 | (from_node_id & 0x7F)  # client node id
    payload[6] = 0x80
    payload[7] = 0x12

    network.send_message((0x400 | from_node_id), payload)

def sdo_batch_ausfuehrung(keybatch):
    global cob_id
    global sdos

    (can_id,_,_) = sdo_schluessel_zurueck(keybatch[0])
    can_id = int(can_id)

    create_cobid(can_id)
    ret = True
    sleeptime = 0.0015

    event_is_set = cobReadyEvent.wait(3)

    if event_is_set and cob_id != 0:
        node = network.add_node(cob_id, edsfile)

        for k in keybatch:
            (_, object_id, subindex_id) = sdo_schluessel_zurueck(k)

            try:
                req = node.sdo.upload(int(object_id),int(subindex_id))
                sdos[k] = req

            except (canopen.SdoCommunicationError, canopen.SdoAbortedError) as e:
                print(' sdo fehler bei object: %s' % k)
                ret = False
                break

    else:
        print('sdo_batch_ausfuehrung zeitueberschreitung')
        ret = False

    destroy_cobid(can_id)

    return ret

def erzeugeBatches(keys):
    global uvrs
    batchlaenge = 7
    
    batches = []
    ret = []

    for (t,n) in uvrs:

        ks = []
        elemente = 0
        for k in keys:
            (can_id, _, _) = sdo_schluessel_zurueck(k)

            if int(can_id) == n:
                ks.append(k)
                elemente = elemente + 1

            if elemente == batchlaenge:
                batches.append(np.asarray(ks))
                
                ks = []
                elemente = 0

        if len(ks) > 0:
            batches.append(np.asarray(ks))
            ks = []
            elemente = 0

    ret = np.asarray(batches) #append(batches, np.array_split(ks, n_batches))
    return ret

        
############

def sendToVolkszaehler(host, channelId, value, description):
    try:
        resp = post("http://%s/middleware/data/%s.json" %(host, channelId), data={"value" : value})
        print("%s: Response from %s: " % (description, host) + str(resp))
    except Exception as e:
        print("Send to %s failed" %(description) + "Exception:" + str(e))


network = canopen.Network()
network.connect(channel='can0', bustype='socketcan')

network.scanner.search()
time.sleep(10)

print(network.scanner.nodes)

# Mache diesen Knoten sichtbar
canlogger_id = from_node_id
node = network.add_node(canlogger_id, edsfile) 

for n in network.scanner.nodes:
    j = 0

    while j < 1:
        create_cobid(n)

        event_is_set = cobReadyEvent.wait(3)

        if event_is_set:
            ret = pruefeUVR(cob_id)
            if ret == 'uvr1611':
                uvrs.append(("uvr1611", n & 255))
            if ret == 'uvr16x2':
                uvrs.append(("uvr16x2", n & 255))
            j = 3
        else:
            print('zeitueberschreitung bei %d' % (n & 255))

        j = j + 1

        destroy_cobid(n)

print(uvrs)

endegut_ok = 0
endegut_failed = 0
batches_ok = 0
batches_failed = 0


print('Abfrage der Werte')
sdos = {}

# Schritt 1: Erzeuge komplette sdos
# Split in Batches nach Knoten Nr
# Abarbeitung der batches
# Auswertung

for (typ, can_id) in uvrs:
    if typ == "uvr16x2":
        UVR16x2zeit_req(can_id)
        UVR16x2EBez_req(can_id)
        UVR16x2A_req(can_id)
        #machenichts = "nichts"

    if typ == 'uvr1611':

        UVR1611zeit_req(can_id)
        UVR1611leseA_req(can_id)
        UVR1611leseE_req(can_id)

# Annahme fuer unteren Code ist, dass alle sdos komplett erzeugt sind. die erzeugung der batches muss ruecksicht auf den knoten nehmen

batches = erzeugeBatches(sdos.keys())
#print batches

n_batches = len(batches)
success = np.full(n_batches, 3, np.int)

endegut = False            

while np.max(success) != 0:
    j = np.argmax(success)

    print("running batch:")
    print(batches[j])

    r = sdo_batch_ausfuehrung(batches[j])

    if r == False:
        success[j] = success[j] - 1
        endegut = False
        batches_failed = batches_failed + 1
    if r == True:
        success[j] = 0
        endegut = True
        batches_ok = batches_ok +1

if endegut:
    endegut_ok = endegut_ok + 1
else:
    endegut_failed= endegut_failed

print("batches ok: %d batches failed: %d endegut ok: %d endegut failed: %d" % (batches_ok, batches_failed, endegut_ok, endegut_failed))

#Auswertung
for (typ, can_id) in uvrs:
    if typ == "uvr1611":
        UVR1611zeit_auswertung(can_id)
        UVR1611leseA_auswertung(can_id)
        UVR1611leseE_auswertung(can_id)

    if typ == "uvr16x2":
        UVR16x2zeit_auswertung(can_id)
        UVR16x2EBez_auswertung(can_id)
        UVR16x2A_auswertung(can_id)

druckeDict()

#c21181a0-b949-11ee-b489-59a0a74a8f11 (Speicher oben)
#7e64c0a0-b94c-11ee-aeb9-8f2a2d346cf6 (Speicher unten)
#f3ac31e0-bd12-11ee-8cb3-f9680ed6e792 (Boiler oben)
#636935b0-bd13-11ee-8954-c1dccdf507a6 (Boiler unten)
#9fcaaed0-bd13-11ee-bb45-1b1ef5c56e91 (Solar VL1)
#b74461f0-bd13-11ee-a151-2523bad0830c (Kollektor)


#b7b874c0-78a6-11ef-a67d-a32414cb239c (Speicher oben)



print("Speicher oben: %.1f" % (respDict["1_e_7"]) )
print("Speicher unten: %.1f" % (respDict["1_e_5"]))


from requests import post

#Speicher oben
sendToVolkszaehler("energielogger", "c21181a0-b949-11ee-b489-59a0a74a8f11", respDict["1_e_7"], "Speicher oben")
sendToVolkszaehler("localhost", "ebcc4b00-8ede-11ef-b2c3-531115468bd5", respDict["1_e_7"], "Speicher oben")

# Speicher unten
sendToVolkszaehler("energielogger", "7e64c0a0-b94c-11ee-aeb9-8f2a2d346cf6", respDict["1_e_5"], "Speicher unten")
sendToVolkszaehler("localhost", "865a7b60-8edf-11ef-ab34-a74ff0f857ff", respDict["1_e_5"], "Speicher unten")
# resp = post("http://energielogger/middleware/data/7e64c0a0-b94c-11ee-aeb9-8f2a2d346cf6.json", data={"value" : respDict["1_e_5"] })
# print("Speicher unten: Response from energielogger: " + str(resp))
#
# resp = post("http://schalleberg/middleware/data/865a7b60-8edf-11ef-ab34-a74ff0f857ff.json", data={"value" : respDict["1_e_5"] })
# print("Speicher unten: Response from schalleberg: " + str(resp))

# Boiler oben
sendToVolkszaehler("energielogger", "f3ac31e0-bd12-11ee-8cb3-f9680ed6e792", respDict["1_e_6"], "Boiler oben")
sendToVolkszaehler("localhost", "ef5b6360-8edf-11ef-bb8e-1f834a780bbd", respDict["1_e_6"], "Boiler oben")
# resp = post("http://energielogger/middleware/data/f3ac31e0-bd12-11ee-8cb3-f9680ed6e792.json", data={"value" : respDict["1_e_6"] })
# print("Boiler oben: Response from energielogger: " + str(resp))
#
# resp = post("http://schalleberg/middleware/data/ef5b6360-8edf-11ef-bb8e-1f834a780bbd.json", data={"value" : respDict["1_e_6"] })
# print("Boiler oben: Response from schalleberg: " + str(resp))

# Boiler unten
sendToVolkszaehler("energielogger", "636935b0-bd13-11ee-8954-c1dccdf507a6", respDict["1_e_4"], "Boiler unten")
sendToVolkszaehler("localhost", "11747c20-8ee0-11ef-9249-dbae6e1bc1f2", respDict["1_e_4"], "Boiler unten")
# resp = post("http://energielogger/middleware/data/636935b0-bd13-11ee-8954-c1dccdf507a6.json", data={"value" : respDict["1_e_4"] })
# print("Boiler unten: Response from energielogger: " + str(resp))
#
# resp = post("http://schalleberg/middleware/data/11747c20-8ee0-11ef-9249-dbae6e1bc1f2.json", data={"value" : respDict["1_e_4"] })
# print("Boiler unten: Response from schalleberg: " + str(resp))

# Solar VL1
sendToVolkszaehler("energielogger", "9fcaaed0-bd13-11ee-bb45-1b1ef5c56e91", respDict["1_e_2"], "Solar VL1")
sendToVolkszaehler("localhost", "41b39760-8ee0-11ef-a9b9-85d3b58a066d", respDict["1_e_2"], "Solar VL1")
# resp = post("http://energielogger/middleware/data/9fcaaed0-bd13-11ee-bb45-1b1ef5c56e91.json", data={"value" : respDict["1_e_2"] })
# print("Solar VL1: Response from energielogger: " + str(resp))
#
# resp = post("http://schalleberg/middleware/data/41b39760-8ee0-11ef-a9b9-85d3b58a066d.json", data={"value" : respDict["1_e_2"] })
# print("Solar VL1: Response from schalleberg: " + str(resp))

# Kollektor
sendToVolkszaehler("energielogger", "b74461f0-bd13-11ee-a151-2523bad0830c", respDict["1_e_1"], "Kollektor")
sendToVolkszaehler("localhost", "7d7b0c20-8ee0-11ef-8016-5be3e4142b2d", respDict["1_e_1"], "Kollektor")
# resp = post("http://energielogger/middleware/data/b74461f0-bd13-11ee-a151-2523bad0830c.json", data={"value" : respDict["1_e_1"] })
# print("Kollektor: Response from energielogger: " + str(resp))
#
# resp = post("http://schalleberg/middleware/data/7d7b0c20-8ee0-11ef-8016-5be3e4142b2d.json", data={"value" : respDict["1_e_1"] })
# print("Kollektor: Response from schalleberg: " + str(resp))

# Rohrkanal 1
sendToVolkszaehler("energielogger", "41e307f0-c8f5-11ef-8bfa-e1fa657729ff", respDict["1_e_13"], "Rohrkanal 1")
#sendToVolkszaehler("localhost", "...", respDict["1_e_13"], "Kollektor")

# Rohrkanal 2
sendToVolkszaehler("energielogger", "5fef15c0-c8f5-11ef-9f73-1329595b1a2d", respDict["1_e_14"], "Rohrkanal 2")
#sendToVolkszaehler("localhost", "....", respDict["1_e_14"], "Kollektor")


print(' .... warte bis zur naechsten runde')

