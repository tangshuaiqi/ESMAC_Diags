# plot vertical profile of cloud fraction for all flights in each IOP
# compare models and aircraft measurements


import sys
sys.path.insert(1,'../subroutines/')

import matplotlib
matplotlib.use('AGG') # plot without needing X-display setting
import matplotlib.pyplot as plt
import numpy as np
import glob
from read_netcdf import read_extractflight,read_merged_size

#%% settings

from settings import campaign, merged_size_path, Model_List, color_model, IOP,  \
    height_bin, E3SM_aircraft_path, figpath_aircraft_statistics
    
import os
if not os.path.exists(figpath_aircraft_statistics):
    os.makedirs(figpath_aircraft_statistics)
    
    
#%%
z=height_bin
dz = z[1]-z[0]
zmin=z-np.insert((z[1:]-z[0:-1])/2,0,dz)
zmax=z+np.append((z[1:]-z[0:-1])/2,dz)

zlen=len(z)   


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

if len(lst)==0:
    print('ERROR: cannot find any file for '+IOP)
    error
    
#%% read all data

cflagall=[]
heightall=[]
cldmall=[]

nmodels=len(Model_List)
for mm in range(nmodels):
    cldmall.append([])
    
print('reading '+format(len(lst))+' files to calculate the statistics: ')

for filename in lst:
    
    # get date info:        
    date=filename[-12:-3]
    if date[-1]=='a':
        flightidx=1
    else:
        flightidx=2
    print(date)
    
    #% read in flight information
    (time,size,height,timeunit,cunit,long_name)=read_merged_size(filename,'height')
    (time,size,cflag,timeunit,cunit,long_name)=read_merged_size(filename,'cld_flag')
    time=np.ma.compressed(time)
    
    heightall.append(height)
    cflagall.append(cflag)
    
    #%% read in models
    
    for mm in range(nmodels):
        filename_m = E3SM_aircraft_path+'Aircraft_vars_'+campaign+'_'+Model_List[mm]+'_'+date+'.nc'
        
        (timem,heightm,cloud,timeunit,cldunit,cldname)=read_extractflight(filename_m,'CLOUD')
            
        cldmall[mm].append(cloud)

#%% calculate percentiles for each height bin

cflag_z = list()
cldm_z = []
nmodels=len(Model_List)
for mm in range(nmodels):
    cldm_z.append([])
for zz in range(zlen):
    cflag_z.append(np.empty(0))
    for mm in range(nmodels):
        cldm_z[mm].append(np.empty(0))
    
ndays=len(heightall)
# ndays=1;
for dd in range(ndays):
    height = heightall[dd]
    cflag  = cflagall[dd]
    for zz in range(zlen):
        idx = np.logical_and(height>=zmin[zz], height<zmax[zz])
        cflag_z[zz]=np.append(cflag_z[zz],cflag[idx])
        
    for mm in range(nmodels):
        cldm = cldmall[mm][dd]
        for zz in range(zlen):
            idx = np.logical_and(height>=zmin[zz], height<zmax[zz])
            cldm_z[mm][zz]=np.append(cldm_z[mm][zz],cldm[idx])
        
#%% remove all NANs and calculate cloud frequency
cldfreq_flag = np.full(zlen,np.nan)
cldfreq_m = []
for mm in range(nmodels):
    cldfreq_m.append(np.full(zlen,np.nan))
    
for zz in range(zlen):
    data = cflag_z[zz]
    data = data[data>=0]
    if len(data)>0:
        cldfreq_flag[zz] = sum(data==1)/len(data)
    for mm in range(nmodels):
        data = cldm_z[mm][zz]
        data = data[~np.isnan(data)]
        if len(data)>0:
            cldfreq_m[mm][zz] = np.mean(data)
  
#%% plot frequency  
figname = figpath_aircraft_statistics+'profile_height_CldFreq_'+campaign+'_'+IOP+'.png'
print('plotting figures to '+figname)

fig,ax = plt.subplots(figsize=(4,8))

ax.plot(cldfreq_flag,z,color='k',linewidth=1,linestyle='-',label='Obs')
for mm in range(nmodels):
    ax.plot(cldfreq_m[mm],z,color=color_model[mm],linewidth=1,label=Model_List[mm])

ax.tick_params(color='k',labelsize=12)
# ax.set_ylim(-1,zlen)
# ax.set_yticks(range(zlen))
# ax.set_yticks(z[0:-1:2])
ax.set_ylabel('Height (m MSL)',fontsize=12)
ax.legend(loc='upper right', fontsize='large')
ax.set_xlabel('Cloud Frequency',fontsize=12)
ax.set_title(IOP,fontsize=15)

fig.savefig(figname,dpi=fig.dpi,bbox_inches='tight', pad_inches=1)