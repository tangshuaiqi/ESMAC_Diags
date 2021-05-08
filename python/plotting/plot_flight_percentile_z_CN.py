# plot percentile of aerosol number concentration (CN) with height
# for flight data in IOPs
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

from settings import campaign, cpcpath,merged_size_path, Model_List, color_model, IOP, \
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

height_all = []
cpc10_o = []
cpc3_o = []
cpc10_m = []
cpc3_m = []
nmodels=len(Model_List)
for mm in range(nmodels):
    cpc10_m.append([])
    cpc3_m.append([])
    
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
    (time,size,cvi,timeunit,cunit,long_name)=read_merged_size(filename,'CVI_inlet')
    (time,size,cflag,timeunit,cunit,long_name)=read_merged_size(filename,'cld_flag')
    (time,size,height,timeunit,zunit,long_name)=read_merged_size(filename,'height')
    time=np.ma.compressed(time)
    
    height_all.append(height)
    
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
        elif np.logical_and(campaign=='HISCALE', date=='20160425a'):
            cpc=np.insert(cpc,0,cpc[:,0],axis=1)
            cpc[0,0]=cpc[0,0]-1
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
    
    cpc10_o.append(cpc10)
    cpc3_o.append(cpc3)
    
    #%% read in Models
    for mm in range(nmodels):
        filename_m = E3SM_aircraft_path+'Aircraft_CNsize_'+campaign+'_'+Model_List[mm]+'_'+date+'.nc'
    
        (timem,heightm,cpc_m,timeunitm,ncn_unit,ncn_longname)=read_extractflight(filename_m,'NCN')
        (timem,heightm,cpcu_m,timeunitm,ncnu_unit,ncnu_longname)=read_extractflight(filename_m,'NUCN')
        if len(cpc10)!=len(cpc_m):
            print('CPC and MAM have different dimensions! check')
            print(cpc10.shape,cpc_m.shape)
            errors
        if any(height!=heightm):
            print('ERROR: model and obs have inconsistent heights. check!')
            print(height[height!=heightm])
            print(heightm[heightm!=height])
            error
        
        cpc10_m[mm].append(cpc_m*1e-6)    # #/m3 to #/cm3
        cpc3_m[mm].append(cpcu_m*1e-6)    # #/m3 to #/cm3
        
        
#%% calculate percentiles for each height bin

cpc10_o_z = list()
cpc3_o_z = list()
cpc10_m_z = []
cpc3_m_z = []
nmodels=len(Model_List)
for mm in range(nmodels):
    cpc10_m_z.append([])
    cpc3_m_z.append([])
for zz in range(zlen):
    cpc10_o_z.append(np.empty(0))
    cpc3_o_z.append(np.empty(0))
    for mm in range(nmodels):
        cpc10_m_z[mm].append(np.empty(0))
        cpc3_m_z[mm].append(np.empty(0))
    
ndays=len(height_all)
for dd in range(ndays):
    height = height_all[dd]
    cpc10 = cpc10_o[dd]
    cpc3 = cpc3_o[dd]
    for zz in range(zlen):
        idx = np.logical_and(height>=zmin[zz], height<zmax[zz])
        cpc10_o_z[zz]=np.append(cpc10_o_z[zz],cpc10[np.logical_and(idx,~np.isnan(cpc10))])
        cpc3_o_z[zz]=np.append(cpc3_o_z[zz],cpc3[np.logical_and(idx,~np.isnan(cpc3))])
        for mm in range(nmodels):
            model10 = cpc10_m[mm][dd]
            model3 = cpc3_m[mm][dd]
            cpc10_m_z[mm][zz]=np.append(cpc10_m_z[mm][zz],model10[idx])
            cpc3_m_z[mm][zz]=np.append(cpc3_m_z[mm][zz],model3[idx])
        

#%% make plot
# set position shift so that models and obs are not overlapped
p_shift = np.arange(nmodels+1)
p_shift = (p_shift - p_shift.mean())*0.2

    
figname = figpath_aircraft_statistics+'percentile_height_CN_'+campaign+'_'+IOP+'.png'
print('plotting figures to '+figname)

fig,(ax1,ax2) = plt.subplots(1,2,figsize=(8,8))   # figsize in inches
# plt.tight_layout(pad=0.4, w_pad=0.5, h_pad=1.5)   #pad=0.4, w_pad=0.5, h_pad=1.0
    
ax1.boxplot(cpc10_o_z,whis=(5,95),showmeans=False,showfliers=False,
            positions=np.array(range(zlen))+p_shift[-1],widths=0.15,
            boxprops=dict(facecolor='k', color='k'),whiskerprops=dict(color='k'),
            medianprops=dict(color='lightyellow',linewidth=1),capprops=dict(color='k'),
            vert=False, patch_artist=True)    # need patch_artist to fill color in box
for mm in range(nmodels):
    c = color_model[mm]
    ax1.boxplot(cpc10_m_z[mm],whis=(5,95),showmeans=False,showfliers=False,
            positions=np.array(range(zlen))+p_shift[mm],widths=0.15,
            boxprops=dict(facecolor=c, color=c),whiskerprops=dict(color=c),
            medianprops=dict(color='lightyellow',linewidth=1),capprops=dict(color=c),
            vert=False, patch_artist=True)    # need patch_artist to fill color in box
ax1.tick_params(color='k',labelsize=12)
ax1.set_xscale('log')
ax1.set_ylim(-1,zlen)
ax1.set_yticks(range(zlen))
ax1.set_yticklabels(z)
# ax1.set_yticks([1,3,5,7,9,11,12,13,14,15,16])
# ax1.set_yticklabels(range(400,4100,400))
# plot temporal lines for label
ax1.plot([],c='k',label='CPC(>10nm)')
for mm in range(nmodels):
    ax1.plot([],c=color_model[mm],label=Model_List[mm])
ax1.legend(loc='upper right', fontsize='large')
    
ax2.boxplot(cpc3_o_z,whis=(5,95),showmeans=False,showfliers=False,
            positions=np.array(range(zlen))+p_shift[-1],widths=0.15,
            boxprops=dict(facecolor='k', color='k'),whiskerprops=dict(color='k'),
            medianprops=dict(color='lightyellow',linewidth=1),capprops=dict(color='k'),
            vert=False, patch_artist=True)    # need patch_artist to fill color in box
for mm in range(nmodels):
    c = color_model[mm]
    ax2.boxplot(cpc3_m_z[mm],whis=(5,95),showmeans=False,showfliers=False,
            positions=np.array(range(zlen))+p_shift[mm],widths=0.15,
            boxprops=dict(facecolor=c, color=c),whiskerprops=dict(color=c),
            medianprops=dict(color='lightyellow',linewidth=1),capprops=dict(color=c),
            vert=False, patch_artist=True)    # need patch_artist to fill color in box
ax2.tick_params(color='k',labelsize=12)
ax2.set_xscale('log')
ax2.set_ylim(-1,zlen)
ax2.set_yticks(range(zlen))
ax2.set_yticklabels([])
# ax1.set_yticks(np.arange(0,20,2))
# ax1.set_yticklabels(range(400,4100,400))
# plot temporal lines for label
ax2.plot([],c='k',label='CPC(>3nm)')
for mm in range(nmodels):
    ax2.plot([],c=color_model[mm],label=Model_List[mm])
ax2.legend(loc='upper right', fontsize='large')
    
# set xlimit consistent in subplots
xlim1 = ax1.get_xlim()
xlim2 = ax2.get_xlim()
ax1.set_xlim([min(xlim1[0],xlim2[0]), max(xlim1[1],xlim2[1])])
ax2.set_xlim([min(xlim1[0],xlim2[0]), max(xlim1[1],xlim2[1])])

ax1.set_ylabel('Height (m MSL)',fontsize=14)
fig.text(0.4,0.06, 'Aerosol number (cm$^{-3}$)', fontsize=14)
fig.text(0.48,0.9, IOP, fontsize=16)

fig.savefig(figname,dpi=fig.dpi,bbox_inches='tight', pad_inches=1)
# plt.close()