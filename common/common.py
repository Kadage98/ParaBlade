flag=1

try:
    from slackclient import SlackClient
except:
    flag=0

from optparse import OptionParser
import os, errno, sys, subprocess
import numpy as np
global options
import matplotlib as mpl
import matplotlib.pyplot as plt

def symlink_force(target, link_name):
    try:
        os.symlink(target, link_name)
    except FileExistsError:
        os.remove(link_name)
        os.symlink(target, link_name)

def ParseInfo():
    parser=OptionParser()
    parser.add_option("-f", "--file", dest="filename",help="SU2 config FILE name")
    parser.add_option("-n", "--partitions", dest="partitions", default=1,help="number of partitions")
    parser.add_option("-o", "--option", dest="solve", default=0,help="0:Shape Optimisation 1:FD 2:ADJ 3:VALIDATION")
    parser.add_option("-c", "--cascade", dest="cascade", default='NONE',help="STATOR \n ROTOR \n STAGE")
    parser.add_option("-z", "--zones", dest="zones", default=1,help="number of zones")
    (options,args)=parser.parse_args()
    options.partitions  = int( options.partitions)
    options.solve  = int( options.solve)
    options.zones  = int( options.zones)
    #print("\tParsed Info:\n\t\tConfig File:\t%s\n\t\tPartition:\t%i\n\t\tOptions:\t %f"%(options.filename,1.0,1))
    print("\n\n\n|*****************************************************************************************")
    print("\tParsed Info:\n\t\tConfig File\t:%s\n\t\tPartition\t:%i\n\t\tOptions\t\t:%i\n\t\tNZONE\t\t:%i\n\t\tCASCADE\t\t:%s "%(options.filename,options.partitions,options.solve,options.zones,options.cascade))
    print("|*****************************************************************************************\n\n\n")
    return options


def SendSlackNotification(T):
    if flag==1:
        slack_token = os.environ["SLACK_API_TOKEN"]
        sc = SlackClient(slack_token)
        sc.api_call("chat.postMessage",channel="#python",text=T)
    else:
        print("Slack client not found !!!!! \n <No slack notifications> \n Do pip3 install slackclient")

def run_command( Command ):
    """ runs os command with subprocess
        checks for errors from command
    """
    
    sys.stdout.flush()
    
    proc = subprocess.Popen( Command, shell=True    ,
                             stdout=sys.stdout      , 
                             stderr=subprocess.PIPE  )
    return_code = proc.wait()
    message = str(proc.stderr.read())
    if return_code < 0:
        message = "SU2 process was terminated by signal '%s'\n%s" % (-return_code,message)
        raise (SystemExit , message)
    elif return_code > 0:
        message = "Path = %s\nCommand = %s\nSU2 process returned error '%s'\n%s" % (os.path.abspath(','),Command,return_code,message)
        if return_code in return_code_map.keys():
            exception = return_code_map[return_code]
        else:
            exception = RuntimeError
        raise (exception , message)
    else:
        sys.stdout.write(message)
            
    return return_code

#---------------------------------------------------------------------------------------------#
#
# Prints the progress bar on the screen [shows the percentage calcualtion left]

def file_length(fname):
    """
    Calculates length (lines) of a data file, including headers
    :param fname: file name
    :return: file length (number of lines)
    """
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
    return i + 1

def file_endread(fname):
    """
    Calculates the end line to be read of a sensitivity .dat file from SU2
    :param fname: file name
    :return: stop line
    """
    ii = 0
    for line in open(fname):
        if (ii == 0 or ii == 1 or ii == 2):
            # Skip header
            ii += 1
            pass
        else:
            parts = line.strip('\t').split()
            if ii == 3:
                len_line_ref = len(parts)
            len_line = len(parts)
            if len_line != len_line_ref:
                end_sens = ii
                break
            else:
                ii += 1
    return end_sens

def ReadHistory(fname,NZONE=1):
    """
    Function that reads history.dat and collects converged values
    """
    if NZONE == 1 or NZONE == 2:
        # TODO: this is a quick fix for multizone
        # Read history.dat
        History = np.loadtxt(fname + '.dat', skiprows=3, delimiter=',')

        # Read converged values
        conv_values = History[-1][1:]

    else:
        # Create a zero numpy matrix
        conv_values_temp = np.zeros((15, NZONE))

        # Loop over zones
        for i in range(NZONE):
            History = np.loadtxt(fname + '_' + str(i) + '.dat', skiprows=3, delimiter=',')
            conv_values_temp[:,i] = History[-1][1:16]

        # Add zone values
        conv_values = conv_values_temp.sum(axis=1)/NZONE

    # Return values
    return conv_values




def printProgress (iteration, total, prefix = '', suffix = '', decimals = 2, barLength = 100):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
    """
    filledLength    = int(round(barLength * iteration / float(total)))
    percents        = round(100.00 * (iteration / float(total)), decimals)
    if percents>100.0: percents=100.0
    bar             = '#' * filledLength + '-' * (barLength - filledLength)
    sys.stdout.write('\r%s [%s] %s%s %s' % (prefix, bar, percents, '%', suffix)),
    sys.stdout.flush()
    if iteration == total:
        print("\n")


def PrintBanner():
    print("###############################################################################################")
    print("#                    ____                 ____  _           _                                 #")
    print("#                   |  _ \ __ _ _ __ __ _| __ )| | __ _  __| | ___                            #")
    print("#                   | |_) / _` | '__/ _` |  _ \| |/ _` |/ _` |/ _ \                           #")
    print("#                   |  __/ (_| | | | (_| | |_) | | (_| | (_| |  __/                           #")
    print("#                   |_|   \__,_|_|  \__,_|____/|_|\__,_|\__,_|\___|                           #")
    print("#                                                                                             #")
    print("###############################################################################################")
    print('\n')



# Sort 2D lists according to the idx coordinate
def sort_2d_list(sub_li,idx=0):
       return(sorted(sub_li, key = lambda x: x[idx])) 
   
 # DBG plots ################# REMOVE WHEN WORKING!!!
def plot2fun(curve1,l1,curve2,l2):
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111)
    fontsize = 10
    ax.set_xlabel('$x$ - axis', fontsize=fontsize, color='k', labelpad=12)
    ax.set_ylabel('$y$ - axis', fontsize=fontsize, color='k', labelpad=12)
    ax.xaxis.set_major_formatter(mpl.ticker.FormatStrFormatter('%.2f'))
    ax.yaxis.set_major_formatter(mpl.ticker.FormatStrFormatter('%.2f'))
    for t in ax.xaxis.get_major_ticks(): t.label.set_fontsize(fontsize)
    for t in ax.yaxis.get_major_ticks(): t.label.set_fontsize(fontsize)
        
    line, = ax.plot(curve1[0], curve1[1])
    line.set_linewidth(1.25)
    line.set_linestyle("-")
    line.set_color("r")
    line.set_label(l1)
            
    line, = ax.plot(curve2[0], curve2[1])
    line.set_linewidth(1.25)
    line.set_linestyle("-")
    line.set_color("b")
    line.set_label(l2)            
            
    ax.legend()
            
    fig = plt.show()
            
#######
def plotfun(curve1,l1):
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111)
    fontsize = 10
    ax.set_xlabel('$x$ - axis', fontsize=fontsize, color='k', labelpad=12)
    ax.set_ylabel('$y$ - axis', fontsize=fontsize, color='k', labelpad=12)
    ax.xaxis.set_major_formatter(mpl.ticker.FormatStrFormatter('%.2f'))
    ax.yaxis.set_major_formatter(mpl.ticker.FormatStrFormatter('%.2f'))
    for t in ax.xaxis.get_major_ticks(): t.label.set_fontsize(fontsize)
    for t in ax.yaxis.get_major_ticks(): t.label.set_fontsize(fontsize)
        
    line, = ax.plot(curve1[0], curve1[1])
    line.set_linewidth(1.25)
    line.set_linestyle("-")
    line.set_color("r")
    line.set_label(l1)                      
            
    ax.legend()
            
    fig = plt.show()
###   
def plotfun_xy(x,y,l1):
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111)
    fontsize = 10
    ax.set_xlabel('$x$ - axis', fontsize=fontsize, color='k', labelpad=12)
    ax.set_ylabel('$y$ - axis', fontsize=fontsize, color='k', labelpad=12)
    ax.xaxis.set_major_formatter(mpl.ticker.FormatStrFormatter('%.2f'))
    ax.yaxis.set_major_formatter(mpl.ticker.FormatStrFormatter('%.2f'))
    for t in ax.xaxis.get_major_ticks(): t.label.set_fontsize(fontsize)
    for t in ax.yaxis.get_major_ticks(): t.label.set_fontsize(fontsize)
        
    line, = ax.plot(x, y)
    line.set_linewidth(1.25)
    line.set_linestyle("-")
    line.set_color("r")
    line.set_label(l1)                      
            
    ax.legend()
            
    fig = plt.show()
###     
def plot3fun(curve1,l1,curve2,l2,curve3,l3):
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111)
    fontsize = 10
    ax.set_xlabel('$x$ - axis', fontsize=fontsize, color='k', labelpad=12)
    ax.set_ylabel('$y$ - axis', fontsize=fontsize, color='k', labelpad=12)
    ax.xaxis.set_major_formatter(mpl.ticker.FormatStrFormatter('%.2f'))
    ax.yaxis.set_major_formatter(mpl.ticker.FormatStrFormatter('%.2f'))
    for t in ax.xaxis.get_major_ticks(): t.label.set_fontsize(fontsize)
    for t in ax.yaxis.get_major_ticks(): t.label.set_fontsize(fontsize)
        
    line, = ax.plot(curve1[0], curve1[1])
    line.set_linewidth(1.25)
    line.set_linestyle("-")
    line.set_color("r")
    line.set_label(l1)
            
    line, = ax.plot(curve2[0], curve2[1])
    line.set_linewidth(1.25)
    line.set_linestyle("-")
    line.set_color("b")
    line.set_label(l2)
            
    line, = ax.plot(curve3[0], curve3[1])
    line.set_linewidth(1.25)
    line.set_linestyle("-")
    line.set_color("k")
    line.set_marker("o")
    line.set_label(l3)
            
    ax.legend()
            
    fig = plt.show()
            
#######  
