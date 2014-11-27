from __future__ import division

import os
import subprocess
import sys
import logging
import argparse
import re
import string
import xlwt
from subprocess import check_output
from itertools import groupby

if __name__ == '__main__':
    
    print("\n\n ************** WiFi Analysis **************** \n")

    frame_no   = re.compile(r'Frame', re.VERBOSE)
    downlink   = re.compile(r'^.*DS\s*status:\s*Frame\s*from\s*DS\s*to\s*a\s*STA\s*via\s*AP\(To\s*DS:\s*0\s*From\s*DS:\s*1\).*',re.VERBOSE)
    uplink     = re.compile(r'^.*DS\s*status:\s*Frame\s*from\s*STA\s*to\s*DS\s*via\s*an\s*AP\s*\(To\s*DS:\s*1\s*From\s*DS:\s*0\).*',re.VERBOSE)
    ds_one_one = re.compile(r'^.*To\s*DS:\s*1\s*From\s*DS:\s*1.*',re.VERBOSE)
    ds_zero_zero = re.compile(r'^.*To\s*DS:\s*0\s*From\s*DS:\s*0.*',re.VERBOSE)
    wds        = re.compile(r'^.*DS\s*status:\s*WDS\s*\(AP\s*to\s*AP\)\s*or\s*Mesh\s*\(MP\s*to\s*MP\)\s*Frame\s*\(To\s*DS:\s*1\s*From\s*DS:\s*1\).*',re.VERBOSE)
    rec_addr   = re.compile(r'.*Receiver\s*address:.*',re.VERBOSE)
    des_addr   = re.compile(r'.*Destination\s*address:.*',re.VERBOSE)
    tra_addr   = re.compile(r'.*Transmitter\s*address:.*',re.VERBOSE)
    bss_id     = re.compile(r'^\s*BSS\s*Id:',re.VERBOSE)
    src_addr   = re.compile(r'.*Source\s*address:.*',re.VERBOSE)
    type       = re.compile(r'.*Type:.*', re.VERBOSE)
    type_data  = re.compile(r'.*Type:\s*Data\s*frame.*', re.VERBOSE)
    frame_len  = re.compile(r'.*Frame\s*Length:.*',re.VERBOSE)
    duration   = re.compile(r'.*Duration:.*',re.VERBOSE)
   
    data       = re.compile(r'.*Type/Subtype:\s*Data.*',re.VERBOSE)
    data_frame = re.compile(r'.*Type/Subtype:\s*QoS\s*Data.*',re.VERBOSE)
    data_null  = re.compile(r'.*Type/Subtype:\s*QoS\s*Null\s*function.*',re.VERBOSE)
    
    subtype_arq = re.compile(r'.*Type/Subtype:\s*Association\s*Request.*', re.VERBOSE)
    subtype_ars = re.compile(r'.*Type/Subtype:\s*Association\s*Response.*', re.VERBOSE)
    subtype_rrq = re.compile(r'.*Type/Subtype:\s*Reassociation\s*Request.*', re.VERBOSE)
    subtype_rrs = re.compile(r'.*Type/Subtype:\s*Reassociation\s*Response.*', re.VERBOSE)
    subtype_prq = re.compile(r'.*Type/Subtype:\s*Probe\s*Request.*', re.VERBOSE)
    subtype_prs = re.compile(r'.*Type/Subtype:\s*Probe\s*Response.*', re.VERBOSE)
    
    subtype_rts = re.compile(r'.*Type/Subtype:\s*Request-to-send.*', re.VERBOSE)
    subtype_cts = re.compile(r'.*Type/Subtype:\s*Clear-to-send.*',re.VERBOSE)
    
    subtype_ack = re.compile(r'.*Type/Subtype:\s*Acknowledgement.*', re.VERBOSE)
    subtype_aut = re.compile(r'.*Type/Subtype:\s*Authentication.*', re.VERBOSE)
    subtype_bea = re.compile(r'.*Type/Subtype:\s*Beacon.*', re.VERBOSE)
    
    retrans = re.compile(r'.*Retry:\s*Frame\s*is\s*being\s*retransmitted.*',re.VERBOSE)
    
    trace_file   = open('./sac.txt', 'r')
    lines        = trace_file.readlines()
    
    #update excel sheet for plotting histogram
    book = xlwt.Workbook()
    sheet1 = book.add_sheet("Hw3_sac")
    sheet1.write(0, 0, "Frame Length")
    sheet1.write(0, 1, "Duration")
    
    
    frame_item = 0
    found_downlink = 0
    found_uplink = 0
    found_wds = 0
    add_src_as_client = 0
    add_des_as_client = 0
    found_aut_type = 0
    aps_list = []
    client_list = []
    client1_dict = dict()
    client_arp = 0
    aps_dict = dict()
    cl_dict = dict()
    row = 0
    count = 0
    cts = 0
    rts = 0
    frame_9 = 0
    up_count = 0
    dl_count = 0
    data_count = 0
    data_nullc = 0
    found_ds_one_one = 0
    found_ds_zero_zero = 0

    for line in lines:
        #if(frame_item == 5000):
            #break
        if frame_no.match(line):
            frame_item += 1
            #reset vars for new frame
            found_downlink    = 0
            found_uplink      = 0
            found_wds         = 0
            add_src_as_client = 0
            add_des_as_client = 0
            found_aut_type    = 0
            aut_dest_found    = 0
            aut_src_found     = 0
            frame_digits      = 0
            dur_digit         = 0
            data_flag         = 0
            found_ds_one_one  = 0
            continue
        
        elif (data_frame.match(line) or data.match(line)):
            data_flag = 1
            data_count +=1
            continue
        
        elif data_null.match(line):
            data_nullc +=1
            continue

        elif frame_len.match(line):
            frame_bit_list = line.split('(')
            frame_string = frame_bit_list[1]
            frame_num    = frame_string.split(' ')
            frame_digits = int(frame_num[0])
            row += 1
            col = 0
            sheet1.write(row,col,frame_num[0])
            col +=1
            continue

        elif duration.match(line):
            dur_sec = line.split(':')
            dur_string = dur_sec[1]
            dur_num = dur_string.split('m')
            #dur_num[0] = dur_num[0].strip()
            dur_digit = int(dur_num[0])
            sheet1.write(row,col,dur_num[0])
            col += 1
            continue
    
        #ques 5
        elif (retrans.match(line) and (data_flag == 1)):
            count += 1
            continue
        
        elif subtype_cts.match(line):
            cts += 1
            continue
        
        elif subtype_rts.match(line):
            rts += 1
            continue
        
        elif (subtype_arq.match(line) or subtype_rrq.match(line) or subtype_prq.match(line)):
            add_src_as_client = 1
            frame_9 += 1
            continue
        
        
        elif (subtype_ars.match(line) or subtype_rrs.match(line) or subtype_prs.match(line)):
            add_des_as_client = 1
            frame_9 += 1
            continue
        
        elif (subtype_aut.match(line)):
            found_aut_type = 1
            frame_9 += 1
            continue

        elif (subtype_ack.match(line) or subtype_bea.match(line) ):
            frame_9 += 1
            continue
        
        elif downlink.match(line):
            found_downlink = 1
            if(data_flag == 1):
                dl_count += 1
            continue
        
        elif uplink.match(line):
            found_uplink = 1
            if(data_flag == 1):
                up_count += 1
            continue

        elif ds_one_one.match(line):
            found_ds_one_one = 1
            continue

        elif ds_zero_zero.match(line):
            found_ds_zero_zero = 1
            continue
        
       

        elif rec_addr.match(line):
            clients = line.split('(')
            client = clients[1]
            client = client.replace(')', '')
            if(found_ds_one_one == 1):
                #print("DS Zero_Zero added client :%s", client)
                client.strip()
                aps_list.append(client)
                if client not in aps_dict:
                    #print("Adding new ap_val %s" %client)
                    aps_dict[client] = frame_digits
                else:
                    temp_frame_dig   = aps_dict[client]
                    aps_dict[client] = temp_frame_dig + frame_digits
            continue
    
        elif des_addr.match(line):
            clients = line.split('(')
            client = clients[1]
            client = client.replace(')', '')
            if((found_downlink == 1) or (add_des_as_client == 1)):
                client_list.append(client)
            if(found_aut_type == 1):
                aut_dest_found = client                    
            continue
    
        elif  src_addr.match(line):
            clients = line.split('(')
            client = clients[1]
            client = client.replace(')', '')
            if((found_uplink == 1) or (add_src_as_client == 1)):
                client_list.append(client)
            if(found_aut_type == 1):
                aut_src_found = client
            
            if(found_ds_one_one == 1):
                #print("DS ONE_ONE added client :%s", client)
                client.strip()
                aps_list.append(client)
                if client not in aps_dict:
                    #print("Adding new ap_val %s" %client)
                    aps_dict[client] = frame_digits
                else:
                    temp_frame_dig   = aps_dict[client]
                    aps_dict[client] = temp_frame_dig + frame_digits

            #question 7
            if(add_src_as_client == 1): 
                if client not in client1_dict:
                    client.strip()
                    client_str = str(client)
                    #print("Adding new client %s" %client)
                    client1_dict[client_str] = 1
                else:
                    client.strip()
                    client_str = str(client)
                    client1_dict[client_str] += 1    
            continue

        elif bss_id.match(line):
            ap_vals = line.split('(')
            ap_val = ap_vals[1]
            ap_val.strip()
            ap_val = ap_val.replace(')', '')
            
            if(found_aut_type == 1):
                if(aut_dest_found==ap_val):
                    if(aut_src_found == 0):
                        print("ERROR ERROR aut_dest_found=%s bss=%s but aut_src_found=0" %(aut_dest_found, ap_val))
                    client_list.append(aut_src_found)
            
                elif(aut_src_found == ap_val):
                    if(aut_dest_found == 0):
                        print("ERROR ERROR aut_src_found=%s bss=%s but aut_dest_found=0" %(aut_src_found, ap_val))
                    client_list.append(aut_dest_found)

            if((found_downlink == 1) or (found_uplink == 1)):
                aps_list.append(ap_val)
                if ap_val not in aps_dict:
                    #print("Adding new ap_val %s" %ap_val)
                    aps_dict[ap_val] = frame_digits
                else:
                    temp_frame_dig   = aps_dict[ap_val]
                    aps_dict[ap_val] = temp_frame_dig + frame_digits

            continue
    
    #end of for
    #question 4
    book.save("Hw3_4.xls")

    aps_set = set(aps_list)
    client_set = set(client_list)

    if(len(aps_set) != len(aps_dict)):
        print("ERROR! length of aps_set != length of aps_dict")

    #print("\n Printing unique APs .. ")
    numaps = 0
    max_bits = 0
    ap_mac_addr = ''
    for set_item in aps_set:
        if(aps_dict[set_item] > max_bits):
            ap_mac_addr = set_item
            max_bits = aps_dict[set_item]
        
        numaps += 1
        #print("%s total_frames=%d" %(set_item, aps_dict[set_item]))
    print("\n1. Number of unique APs : %d" %numaps)

    numcl = 0
    #print("\n Printing Clients .. ")
    for set_item in client_set:
        numcl +=1
        #print("%s" %set_item)
    print("\n2. Number of unique Clients : %d" %numcl)

    print("\n3. AP with MAC ID: %s   transferred max bits=%d" %(ap_mac_addr, max_bits))

    data_total = int(data_count) - int(data_nullc)

    print("\n5.a Data frame count: %s" %data_total)
    fraction = int(count)/int(data_total)
    
    print("\n5.b Number of data frames retransmitted: %s, Fraction: %s" %(count,fraction))
    
    no_cts_rts = int(cts)+int(rts)
    fra_cts = no_cts_rts/int(data_total)
    
    print("\n6. Number of data frames which used CTS/RTS: %s, Fraction: %s" %(no_cts_rts,fra_cts))

    #7 Multiple clients can have same max items
    max_assoc_items = 0
    client_mac_addr_list = []
    for client in client1_dict:
        #print("client : %s max_assoc_items=%d \n" %(client, client1_dict[client]))    
        if(client1_dict[client] > max_assoc_items):
            #found new max, empty previous clients
            client_mac_addr_list[:] = []
            client_mac_addr_list.append(client)
            max_assoc_items = client1_dict[client]
        elif(client1_dict[client] == max_assoc_items):
            #another client with same max
            client_mac_addr_list.append(client)
     
    for client in client_mac_addr_list:    
        print("\n7. Client_max  %d  client is %s" %(max_assoc_items, client))

    print("\n8. Data frames exchanged between client and APs downlink: %s , uplink:%s" %(dl_count,up_count))

    per = (int(frame_9)/500)
    print("\n9. Percent of frames that are bea/aut/ack/ass/reass/prob: %s percent" %per)

    exitCode = 0
    print("\n\n.. Exit Program.\n\n")
    sys.exit(exitCode)


