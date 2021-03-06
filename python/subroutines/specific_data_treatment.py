# function of some specific data treatment

#%% estimate cloud flag based on LWC
def lwc2cflag(lwc,lwcunit):
    if lwcunit=='kg/m3':
        lwc=lwc*0.001
        lwcunit='g/m3'
    elif lwcunit=='g m-3':
        lwcunit='g/m3'
    if lwcunit!='g/m3' and lwcunit!='gram/m3':
        print('unit of LWC should be gram/m3. check: '+lwcunit)
        error
        
    import numpy as np
    cldflag = 0*np.array(lwc)
    
    # set threshold of LWC to identify cloud
    cldflag[lwc>0.02]=1
    return(cldflag)

#%% set model masks if the difference of Ps is too large
def mask_model_ps(timem,psm,legnum,campaign,shipmetpath):
    
    import sys
    sys.path.insert(1,'../subroutines/')
    
    import numpy as np
    import glob
    from read_ship import read_marmet
    from read_ARMdata import read_met
    from time_format_change import yyyymmdd2cday,  cday2mmdd
    
    if campaign=='MAGIC':
        filenameo = shipmetpath+'marmet'+legnum+'.txt'
        (shipdata,shipvarlist) = read_marmet(filenameo)
        year=[a[1] for a in shipdata]
        month=[a[2] for a in shipdata]
        day=[a[3] for a in shipdata]
        hh=[int(a[4]) for a in shipdata]
        mm=[int(a[5]) for a in shipdata]
        ss=[int(a[6]) for a in shipdata]
        yyyymmdd = [year[i]+month[i]+day[i] for i in range(len(year))]   # yyyymmdd
        # get time in calendar day
        time = np.array(hh)/24. + np.array(mm)/1440. + np.array(ss)/86400. 
        time = np.array([time[i] + yyyymmdd2cday(yyyymmdd[i],'noleap') for i in range(len(time))])
        if time[-1]<time[0]:
            time[time<=time[-1]]=time[time<=time[-1]]+365
        # get variables
        ps=np.array([float(a[shipvarlist.index('bp')]) for a in shipdata])    
        ps[ps==-999]=np.nan

    elif campaign=='MARCUS':
        if legnum=='1':
            startdate='2017-10-30'
            enddate='2017-12-02'
        elif legnum=='2':
            startdate='2017-12-13'
            enddate='2018-01-11'
        elif legnum=='3':
            startdate='2018-01-16'
            enddate='2018-03-04'
        elif legnum=='4':
            startdate='2018-03-09'
            enddate='2018-03-22'
        cday1=yyyymmdd2cday(startdate,'noleap')
        cday2=yyyymmdd2cday(enddate,'noleap')
        if startdate[0:4]!=enddate[0:4]:
            cday2=cday2+365  # cover two years
        time=np.empty(0)
        ps=np.empty(0)
        for cc in range(cday1,cday2+1):
            if cc<=365:
                yyyymmdd=startdate[0:4]+cday2mmdd(cc)
            else:
                yyyymmdd=enddate[0:4]+cday2mmdd(cc-365)
            lst0 = glob.glob(shipmetpath+'maraadmetX1.b1.'+yyyymmdd+'*')
            (time0,ps0,timeunit,psunit,ps_long_name)=read_met(lst0[0],'atmospheric_pressure')
            time = np.hstack((time, time0/86400. + cc))
            ps = np.hstack((ps,ps0))
        ps[ps<=-999]=np.nan

    if len(timem)!=len(time):
        print('ERROR: model and obs have inconsistent size. check!')
        error
        
    datamask = (ps-psm)>10
    return(datamask)