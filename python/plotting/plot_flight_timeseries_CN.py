# plot aircraft track data
# timeseries of aerosol number concentration (CN)
# compare models and CPC measurements


import sys
sys.path.insert(1,'../subroutines/')

import matplotlib
# matplotlib.use('AGG') # plot without needing X-display setting
import matplotlib.pyplot as plt
import numpy as np
import glob
from read_aircraft import read_cpc
from read_netcdf import read_merged_size,read_extractflight

#%% settings

from settings import campaign, cpcpath,merged_size_path, Model_List, color_model, \
    IOP, E3SM_aircraft_path, figpath_aircraft_timeseries

import os
if not os.path.exists(figpath_aircraft_timeseries):
    os.makedirs(figpath_aircraft_timeseries)
   

#%% find files for flight information
lst = glob.glob(merged_size_path+'merged_bin_*'+campaign+'*.nc')
lst.sort()


if len(lst)==0:
    print('ERROR: cannot find any file at '+merged_size_path)
    error
  
# choose files for specific IOP
if campaign=='HISCALE':
    if IOP=='IOP1':
        lst=lst[0:17]
    elif IOP=='IOP2':
        lst=lst[17:]
    elif IOP[0:4]=='2016':
        a=lst[0].split('_'+campaign+'_')
        lst = glob.glob(a[0]+'*'+IOP+'*')
        lst.sort()
elif campaign=='ACEENA':
    if IOP=='IOP1':
        lst=lst[0:20]
    elif IOP=='IOP2':
        lst=lst[20:]
    elif IOP[0:4]=='2017' or IOP[0:4]=='2018':
        a=lst[0].split('_'+campaign+'_')
        lst = glob.glob(a[0]+'*'+IOP+'*')
        lst.sort()
else:
    print('ERROR: campaign name is not recognized: '+campaign)
    error
    
# for each flight
for filename in lst:
    
    # get date info:        
    date=filename[-12:-3]
    if date[-1]=='a':
        flightidx=1
    else:
        flightidx=2

    #% read in flight information
    (time,size,cvi,timeunit,cunit,long_name)=read_merged_size(filename,'CVI_inlet')
    (time,size,cflag,timeunit,cunit,long_name)=read_merged_size(filename,'cld_flag')
    (time,size,height,timeunit,zunit,long_name)=read_merged_size(filename,'height')
    time=np.ma.compressed(time)
    
    
    #%% read in CPC measurements
    
    if campaign=='HISCALE':
        filename_c=glob.glob(cpcpath+'CPC_G1_'+date[0:8]+'*R2_HiScale001s.ict.txt')
    elif campaign=='ACEENA':
        filename_c=glob.glob(cpcpath+'CPC_G1_'+date[0:8]+'*R2_ACEENA001s.ict')    
    filename_c.sort()
    # read in data
    if len(filename_c)==1 or len(filename_c)==2: # some days have two flights
        (cpc,cpclist)=read_cpc(filename_c[flightidx-1])
        if np.logical_and(campaign=='ACEENA', date=='20180216a'):
            cpc=np.insert(cpc,1404,(cpc[:,1403]+cpc[:,1404])/2,axis=1)
        time_cpc = cpc[0,:]
        cpc10 = cpc[1,:]
        cpc3 = cpc[2,:]
    elif len(filename_c)==0:
        time_cpc=time
        cpc10=np.nan*np.empty([len(time)])
        cpc3=np.nan*np.empty([len(time)])
    else:
        print('find too many files, check: ')
        print(filename_c)
        error
    
    # some quality checks
    cpc3[cpc3<20]=np.nan
    cpc10[cpc10<10]=np.nan
    
    #%% read in Models
    nmodels=len(Model_List)
    cpc10_m = []
    cpc3_m = []
    for mm in range(nmodels):
        filename_m = E3SM_aircraft_path+'Aircraft_CNsize_'+campaign+'_'+Model_List[mm]+'_'+date+'.nc'
    
        (timem,heightm,cpc_m,timeunitm,ncn_unit,ncn_longname)=read_extractflight(filename_m,'NCN')
        (timem,heightm,cpcu_m,timeunitm,ncnu_unit,ncnu_longname)=read_extractflight(filename_m,'NUCN')
        # if len(cpc_m)!=cpc.shape[1]:
        #     print('CPC and MAM have different dimensions! check')
        #     print(cpc.shape,cpc_m.shape)
        #     errors
        cpc10_m.append(cpc_m*1e-6) # #/m3 to #/cm3
        cpc3_m.append(cpcu_m*1e-6) # #/m3 to #/cm3
    
    timem2 = timem/3600
          
    #%% make plot
        
    figname = figpath_aircraft_timeseries+'timeseries_CN_'+campaign+'_'+date+'.png'
    print('plotting figures to '+figname)
    
    fig,(ax1,ax2) = plt.subplots(2,1,figsize=(8,4))   # figsize in inches
    plt.tight_layout(pad=0.4, w_pad=0.5, h_pad=1.5)   #pad=0.4, w_pad=0.5, h_pad=1.0
    
    ax1.plot(time_cpc/3600,cpc10,color='k',linewidth=1,label='CPC(>10nm)')
    for mm in range(nmodels):
        ax1.plot(timem2, cpc10_m[mm],color=color_model[mm],linewidth=1, label=Model_List[mm])
    ax1.set_yscale('log')
    ax1.tick_params(color='k',labelsize=12)
    ylim1 = ax1.get_ylim()
    
    ax2.plot(time_cpc/3600,cpc3,color='k',linewidth=1,label='CPC(>3nm)')
    for mm in range(nmodels):
        ax2.plot(timem2, cpc3_m[mm],color=color_model[mm],linewidth=1, label=Model_List[mm])
    ax2.set_yscale('log')
    ax2.tick_params(color='k',labelsize=12)
    ylim2 = ax2.get_ylim()
    
    # set ylimit consistent in subplots
    ax1.set_ylim([ylim1[0], ylim2[1]])
    ax2.set_ylim([ylim1[0], ylim2[1]])
    
    ax1.legend(loc='center right', shadow=False, fontsize='large',bbox_to_anchor=(1.25, .5))
    ax2.legend(loc='center right', shadow=False, fontsize='large',bbox_to_anchor=(1.25, .5))
    
    ax2.set_xlabel('time (hour UTC) '+date,fontsize=14)
    ax1.set_title('Aerosol Number Concentration (cm$^{-3}$)',fontsize=15)
    
    fig.savefig(figname,dpi=fig.dpi,bbox_inches='tight', pad_inches=1)
    plt.close()