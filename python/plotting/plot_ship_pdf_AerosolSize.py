# plot mean aerosol size ditribution for ship track data
# average for all data
# compare models and aircraft measurements

import sys
sys.path.insert(1,'../subroutines/')

import matplotlib
matplotlib.use('AGG') # plot without needing X-display setting
import matplotlib.pyplot as plt
import numpy as np
import glob
from read_ARMdata import read_uhsas
from read_netcdf import read_E3SM
from time_format_change import cday2mmdd,yyyymmdd2cday

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

from settings import campaign, Model_List, color_model, shipuhsaspath, E3SM_ship_path, figpath_ship_statistics

import os
if not os.path.exists(figpath_ship_statistics):
    os.makedirs(figpath_ship_statistics)

lst = glob.glob(E3SM_ship_path+'Ship_CNsize_'+campaign+'_'+Model_List[0]+'_shipleg*.nc')


#%% read in model
nmodels=len(Model_List)
pdf_model = list()
pdfall_m = [np.empty((3000,0)) for mm in range(nmodels)]

for mm in range(nmodels):
    data2=list()
    ntimes = list()
    for ll in range(len(lst)):
        if campaign=='MAGIC':
            legnum=lst[ll][-5:-3]
        elif campaign=='MARCUS':
            legnum=lst[ll][-4]
        print(legnum)
        
        filenamem = E3SM_ship_path+'Ship_CNsize_'+campaign+'_'+Model_List[mm]+'_shipleg'+legnum+'.nc'
        (timem,data,timeunitm,datamunit,datamlongname)=read_E3SM(filenamem,'NCNall')
        
        # average for each file to reduce computational time
        ntimes.append(sum(data[0,:]>0))  # number of valid values
        data[data<0]=np.nan
        data=data*1e-6   # change unit from 1/m3 to 1/cm3
        
        # average in time for quicker plot
        time0=np.arange(timem[0],timem[-1]+0.04,1./24)
        data0 = avg_time(timem,data.T,time0)
        pdfall_m[mm] = np.column_stack((pdfall_m[mm],data0.T))
        
        meandata=np.nanmean(data,1)
        data2.append(meandata)
        
    # mean pdf
    ntotal=sum(ntimes)
    data3=[data2[ii]*ntimes[ii]/ntotal for ii in range(len(ntimes))]
    pdf_model.append(sum(data3))
    
#%% read in observations

nbins = 99 # for UHSAS at MAGIC
pdfall_o = np.empty((nbins,0))

if campaign=='MAGIC':
    startdate='2012-09-22'
    enddate='2013-09-26'
elif campaign=='MARCUS':
    startdate='2017-10-30'
    enddate='2018-03-22'
cday1=yyyymmdd2cday(startdate,'noleap')
cday2=yyyymmdd2cday(enddate,'noleap')
if startdate[0:4]!=enddate[0:4]:
    cday2=cday2+365  # cover two years

uhsasall=list()
ntimes = list()
for cc in range(cday1,cday2+1):
    if cc<=365:
        yyyymmdd=startdate[0:4]+cday2mmdd(cc)
    else:
        yyyymmdd=enddate[0:4]+cday2mmdd(cc-365)
        
    if campaign=='MAGIC':
        filenameo = glob.glob(shipuhsaspath+'magaosuhsasM1.a1.'+yyyymmdd+'*')
    elif campaign=='MARCUS':
        filenameo = glob.glob(shipuhsaspath+'maraosuhsasM1.a1.'+yyyymmdd+'*')
    if len(filenameo)==0:
        continue  
    elif len(filenameo)>1:
        print('ERROR: should only find one file. check: ')
        print(filenameo)
        error
    
    print(yyyymmdd)
    
    (time,dmin,dmax,uhsas,timeunit,uhunit,uhlongname)=read_uhsas(filenameo[0])
    
    uhsas=np.ma.filled(uhsas)
    uhsas[uhsas<0]=np.nan
    # average in time for quicker plot
    time0=np.arange(1800,86400,3600)
    data0 = avg_time(time,uhsas,time0)
    pdfall_o = np.column_stack((pdfall_o,data0.T))
    
    # average for each file to reduce computational time
    ntimes.append(sum(uhsas[:,0]>=0))  # number of valid values
    meandata=np.nanmean(uhsas,0)
    meandata[np.isnan(meandata)]=0
    uhsasall.append(meandata) 
    
size_u = (dmin+dmax)/2
dsize_u = dmax-dmin

# mean pdf
ntotal=sum(ntimes)
pdf_obs=sum([uhsasall[ii]*ntimes[ii]/ntotal for ii in range(len(ntimes))])

#%% change to dN/dlnDp
dlnDp_u=np.empty(nbins)
for bb in range(len(size_u)):
    dlnDp_u[bb]=np.log(dmax[bb]/dmin[bb])
dlnDp=np.empty(3000)
for bb in range(3000):
    dlnDp[bb]=np.log((bb+2)/(bb+1))
pdf_obs=pdf_obs/dlnDp_u
for mm in range(nmodels):
    pdf_model[mm]=pdf_model[mm]/dlnDp

#%%
pct1_o = [np.nanpercentile(pdfall_o[i,:]/dlnDp_u[i],10) for i in range(nbins)]
pct2_o = [np.nanpercentile(pdfall_o[i,:]/dlnDp_u[i],90) for i in range(nbins)]
pct1_m = [[] for mm in range(nmodels)]
pct2_m = [[] for mm in range(nmodels)]
for mm in range(nmodels):
    pct1_m[mm] = [np.nanpercentile(pdfall_m[mm][i,:]/dlnDp[i],10) for i in range(3000)]
    pct2_m[mm] = [np.nanpercentile(pdfall_m[mm][i,:]/dlnDp[i],90) for i in range(3000)]

#%% plot
figname = figpath_ship_statistics+'pdf_AerosolSize_'+campaign+'.png'

print('plotting figures to '+figname)

#fig = plt.figure()
fig,ax = plt.subplots(figsize=(4,2.5))   # figsize in inches

ax.plot(size_u,pdf_obs,color='k',label='Obs')
for mm in range(nmodels):
    ax.plot(np.arange(1,3001),pdf_model[mm],color=color_model[mm],linewidth=1, label=Model_List[mm])

ax.fill_between(size_u,pct1_o,pct2_o, alpha=0.5, facecolor='gray')
for mm in range(nmodels):
    ax.fill_between(np.arange(1,3001),pct1_m[mm],pct2_m[mm], alpha=0.2, facecolor=color_model[mm])
    
ax.legend(loc='upper right', shadow=False, fontsize='medium')
ax.tick_params(color='k',labelsize=12)
ax.set_xscale('log')
ax.set_yscale('log')
ax.set_ylim(0.01,1e4)
ax.set_xlabel('Diameter (nm)',fontsize=13)
ax.set_ylabel('#/dlnDp (cm$^{-3}$)',fontsize=13)
ax.set_title(campaign,fontsize=14)

fig.savefig(figname,dpi=fig.dpi,bbox_inches='tight', pad_inches=1)

