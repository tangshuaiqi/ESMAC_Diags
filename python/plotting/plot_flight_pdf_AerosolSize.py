# plot mean aerosol size ditribution for aircraft track data
# average for each IOP
# compare models and aircraft measurements


import sys
sys.path.insert(1,'../subroutines/')

import matplotlib
matplotlib.use('AGG') # plot without needing X-display setting
import matplotlib.pyplot as plt
import numpy as np
import glob
from read_aircraft import read_RF_NCAR
from specific_data_treatment import lwc2cflag
# from time_format_change import yyyymmdd2cday, hhmmss2sec
from read_netcdf import read_merged_size,read_extractflight

# define function of averaging in time for faster plotting
def avg_time(time0,data0,time):
    data0[data0<0]=np.nan
    if data0.shape[0]!=len(time0):
        error
    data = np.full((len(time),data0.shape[1]),np.nan)
    dt=(time[1]-time[0])/2
    for tt in range(len(time)):
        idx = np.logical_and(time0>=time[tt]-dt,time0<=time[tt]+dt)
        data[tt,:]=np.nanmean(data0[idx,:],axis=0)
    return(data)

#%% settings

from settings import campaign,  Model_List, color_model,  \
    E3SM_aircraft_path, figpath_aircraft_statistics

if campaign=='HISCALE' or campaign=='ACEENA':
    from settings import IOP, merged_size_path
elif campaign=='CSET' or campaign=='SOCRATES':
    from settings import RFpath
else:
    print('ERROR: campaign name is not recognized: '+campaign)
    error
    
import os
if not os.path.exists(figpath_aircraft_statistics):
    os.makedirs(figpath_aircraft_statistics)
    
    
#%% find files for flight information

lst = glob.glob(E3SM_aircraft_path+'Aircraft_vars_'+campaign+'_'+Model_List[0]+'_*.nc')
lst.sort()
if len(lst)==0:
    print('ERROR: cannot find any file at '+E3SM_aircraft_path)
    error
# choose files for specific IOP
if campaign=='HISCALE':
    if IOP=='IOP1':
        lst=lst[0:17]
    elif IOP=='IOP2':
        lst=lst[17:]
    elif IOP[0:4]=='2016':
        a=lst[0].split('_'+Model_List[0]+'_')
        lst = glob.glob(a[0]+'_'+Model_List[0]+'_'+IOP+'*')
        lst.sort()
elif campaign=='ACEENA':
    if IOP=='IOP1':
        lst=lst[0:20]
    elif IOP=='IOP2':
        lst=lst[20:]
    elif IOP[0:4]=='2017' or IOP[0:4]=='2018':
        a=lst[0].split('_'+Model_List[0]+'_')
        lst = glob.glob(a[0]+'_'+Model_List[0]+'_'+IOP+'*')
        lst.sort()
        
alldates = [x.split('_')[-1].split('.')[0] for x in lst]
    
print('reading '+format(len(alldates))+' files to calculate mean aerosol pdf: ')

nmodels=len(Model_List)
pdfall_m = [np.empty((3000,0)) for mm in range(nmodels)]
size_m = np.zeros(3000)
pdf_model = [size_m for mm in range(nmodels)]
if 'pdf_obs' in locals():
    del pdf_obs

# number of valid timesteps
n_o = 0
n_m = [0 for mm in range(nmodels)]
    

# dN/dlnDp for model
dlnDp_m = np.empty((3000))
for bb in range(3000):
    dlnDp_m[bb]=np.log((bb+2)/(bb+1))

for date in alldates[:]:
    print(date)
    
    #%% read in Models
    for mm in range(nmodels):
        filename_m = E3SM_aircraft_path+'Aircraft_CNsize_'+campaign+'_'+Model_List[mm]+'_'+date+'.nc'
        (timem,heightm,datam,timeunitm,datamunit,datamlongname)=read_extractflight(filename_m,'NCNall')
        datam=datam*1e-6    # #/m3 to #/cm3
        
        # average in time for quicker plot
        time2=np.arange(300,86400,600)
        data2 = avg_time(timem,datam.T,time2)
        datam=data2.T
        timem=time2
        
        for tt in range(len(timem)):
            datam[:,tt]=datam[:,tt]/dlnDp_m
            
        pdfall_m[mm] = np.column_stack((pdfall_m[mm],datam))
        for tt in range(len(timem)):
            if ~np.isnan(datam[0,tt]):
                pdf_model[mm] = pdf_model[mm]+datam[:,tt]
                n_m[mm]=n_m[mm]+1
        
    #%% read observation        
    if campaign=='HISCALE' or campaign=='ACEENA':
        if date[-1]=='a':
            flightidx=1
        else:
            flightidx=2
            
        if campaign=='HISCALE':
            filename = merged_size_path+'merged_bin_fims_pcasp_'+campaign+'_'+date+'.nc'
        elif campaign=='ACEENA':
            filename = merged_size_path+'merged_bin_fims_pcasp_opc_'+campaign+'_'+date+'.nc'
    
        (time,size,cvi,timeunit,cunit,long_name)=read_merged_size(filename,'CVI_inlet')
        (time,size,cflag,timeunit,cunit,long_name)=read_merged_size(filename,'cld_flag')
        (time,size,legnum,timeunit,zunit,long_name)=read_merged_size(filename,'leg_number')
        (time,size,sizeh,timeunit,dataunit,long_name)=read_merged_size(filename,'size_high')
        (time,size,sizel,timeunit,dataunit,long_name)=read_merged_size(filename,'size_low')
        (time,size,merge,timeunit,dataunit,long_name)=read_merged_size(filename,'size_distribution_merged')
        time=np.ma.compressed(time)
        size=size*1000.
        merge[cflag==1,:]=np.nan
        
        
        
        # average in time for quicker plot
        time2=np.arange(300,86400,600)
        data2 = avg_time(time,merge,time2)
        merge = data2.T
        time=time2/3600.
        

    elif campaign=='CSET' or campaign=='SOCRATES':
        filename = glob.glob(RFpath+'RF*'+date+'*.PNI.nc')
        # cloud flag
        (time,lwc,timeunit,lwcunit,lwclongname,size,cellunit)=read_RF_NCAR(filename[-1],'PLWCC')
        if campaign=='CSET':
            (time,uhsas,timeunit,dataunit,long_name,size,cellunit)=read_RF_NCAR(filename[-1],'CUHSAS_RWOOU')
        elif campaign=='SOCRATES':
            # there are two variables: CUHSAS_CVIU and CUHSAS_LWII
            (time,uhsas,timeunit,dataunit,long_name,size,cellunit)=read_RF_NCAR(filename[-1],'CUHSAS_LWII')
        # calculate cloud flag based on LWC
        cflag=lwc2cflag(lwc,lwcunit)
        uhsas[cflag==1,:,:]=np.nan
        uhsas[uhsas>500]=np.nan
        
        # average in time for quicker plot
        time2=np.arange(300,86400,600)
        data2 = avg_time(time,uhsas[:,0,:],time2)
        merge = data2.T
        time0 = np.array(time)
        time=time2/3600.
        
        size=size*1000.
        sizeh = size
        sizel = np.hstack((2*size[0]-size[1],  size[0:-1]))
    
    # change to dN/dlnDp
    for bb in range(len(size)):
        dlnDp=np.log(sizeh[bb]/sizel[bb])
        merge[bb,:]=merge[bb,:]/dlnDp
    
    merge[merge<0]=np.nan
    
    # exclude 30min after takeoff and before landing
    idx=np.logical_or(time2<(time2[0]+1800), time2>(time2[-1]-1800))
    merge[:,idx]=np.nan
    
    # fig,ax=plt.subplots()
    # ax.plot(merge[9,:])
    # ax.set_title(date)
    # error
    
    if ('pdf_obs' in locals()) == False:
        pdf_obs = np.zeros(len(size)) 
        pdfall_o = np.empty((len(size),0))
    idx_valid = ~np.isnan(np.mean(merge,0))
    pdf_obs = pdf_obs + np.sum(merge[:,idx_valid],1)
    pdfall_o = np.hstack((pdfall_o,np.array(merge[:,idx_valid])))
    n_o = n_o + np.sum(idx_valid)
    

#%% calculate mean pdf

pdf_obs[pdf_obs<1e-3]=np.nan
pdf_obs=pdf_obs/n_o
for mm in range(nmodels):
    pdf_model[mm]=pdf_model[mm]/n_m[mm]

#%%
pdfall_o[pdfall_o<0]=np.nan
pct1_o = [np.nanpercentile(pdfall_o[i,:],10) for i in range(len(size))]
pct2_o = [np.nanpercentile(pdfall_o[i,:],90) for i in range(len(size))]
pct1_m = [[] for mm in range(nmodels)]
pct2_m = [[] for mm in range(nmodels)]
for mm in range(nmodels):
    pct1_m[mm] = [np.nanpercentile(pdfall_m[mm][i,:],10) for i in range(3000)]
    pct2_m[mm] = [np.nanpercentile(pdfall_m[mm][i,:],90) for i in range(3000)]

#%% make plot

if campaign=='HISCALE' or campaign=='ACEENA':
    figname = figpath_aircraft_statistics+'pdf_AerosolSize_'+campaign+'_'+IOP+'.png'
else:
    figname = figpath_aircraft_statistics+'pdf_AerosolSize_'+campaign+'.png'

print('plotting figures to '+figname)

#fig = plt.figure()
fig,ax = plt.subplots(figsize=(4,2.5))   # figsize in inches

ax.plot(size,pdf_obs,color='k',label='Obs')
for mm in range(nmodels):
    ax.plot(np.arange(1,3001),pdf_model[mm],color=color_model[mm],linewidth=1, label=Model_List[mm])

ax.fill_between(size,pct1_o,pct2_o, alpha=0.5, facecolor='gray')
for mm in range(nmodels):
    ax.fill_between(np.arange(1,3001),pct1_m[mm],pct2_m[mm], alpha=0.2, facecolor=color_model[mm])

ax.legend(loc='upper right', shadow=False, fontsize='medium')
ax.tick_params(color='k',labelsize=12)
ax.set_xscale('log')
ax.set_yscale('log')
ax.set_ylim(0.01,1e4)
ax.set_xlim(0.67,4500)
ax.set_xlabel('Diameter (nm)',fontsize=13)
ax.set_ylabel('#/dlnDp (cm$^{-3}$)',fontsize=13)

if campaign=='HISCALE' or campaign=='ACEENA':
    ax.set_title(campaign+' '+IOP,fontsize=14)
else:
    ax.set_title(campaign,fontsize=14)

fig.savefig(figname,dpi=fig.dpi,bbox_inches='tight', pad_inches=1)
plt.close()

