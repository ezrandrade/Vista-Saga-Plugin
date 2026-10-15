"""Exercita o processamento raster real com TIFFs, substituindo só a interface GDAL.

A homologação do driver GDAL fornecido pelo QGIS será feita no QGIS 4.x.
"""
import os
import sys
import types

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from geosaga.combination_raster import run_raster_combination


class Reader:
    def __init__(self, path):
        self.ds = rasterio.open(path)
        self.RasterXSize = self.ds.width
        self.RasterYSize = self.ds.height
        self.RasterCount = self.ds.count
    def GetProjection(self):return self.ds.crs.to_wkt() if self.ds.crs else ''
    def GetGeoTransform(self):return self.ds.transform.to_gdal()
    def GetRasterBand(self, index):return ReadBand(self.ds, index)


class ReadBand:
    def __init__(self,ds,i):self.ds,self.i=ds,i
    def GetNoDataValue(self):return self.ds.nodata
    def GetCategoryNames(self):return None
    def ReadAsArray(self,x,y,w,h):return self.ds.read(self.i,window=((y,y+h),(x,x+w)))


class WriteBand:
    def __init__(self, ds):self.ds=ds
    def SetNoDataValue(self, value):self.ds.nd=value
    def WriteArray(self,arr,x,y):
        self.ds.arr[y:y+arr.shape[0],x:x+arr.shape[1]]=arr
        return 0
    def FlushCache(self):self.ds.FlushCache()


class Writer:
    def __init__(self,path,w,h):
        self.path,self.RasterXSize,self.RasterYSize=path,w,h
        self.arr=np.zeros((h,w),dtype=np.int32)
        self.nd=None
        self.gt=None
        self.crs=None
        self.meta={}
    def SetGeoTransform(self,gt):self.gt=gt
    def SetProjection(self,crs):self.crs=crs
    def GetRasterBand(self,_):return WriteBand(self)
    def SetMetadataItem(self,k,v):self.meta[k]=v
    def FlushCache(self):
        with rasterio.open(self.path,'w',driver='GTiff',width=self.RasterXSize,
                           height=self.RasterYSize,count=1,dtype='int32',
                           crs=self.crs,transform=rasterio.Affine.from_gdal(*self.gt),
                           nodata=self.nd,compress='lzw') as dest:
            dest.write(self.arr,1)
            dest.update_tags(**self.meta)


class Driver:
    def Create(self,p,w,h,*args,**kwargs):return Writer(p,w,h)


class SRS:
    def ImportFromWkt(self,text):
        from pyproj import CRS
        self.crs=CRS.from_wkt(text)
        return 0
    def IsSame(self,other):return self.crs==other.crs
    def IsProjected(self):return self.crs.is_projected
    def GetLinearUnits(self):return 1.0


def install_fake_gdal(monkeypatch):
    gdal=types.SimpleNamespace(Open=lambda p,mode: Reader(p), GA_ReadOnly=0,
           GDT_Int32=5, GetDriverByName=lambda _:Driver())
    osr=types.SimpleNamespace(SpatialReference=SRS)
    monkeypatch.setitem(sys.modules,'osgeo',types.SimpleNamespace(gdal=gdal,osr=osr))
    publish = lambda pairs, parent: [os.replace(source,dest) for source,dest in pairs]
    monkeypatch.setitem(sys.modules,'geosaga.vector_evaluation_writer',
                        types.SimpleNamespace(_publish_set=publish))


def newtif(path,values,nodata=255,gt=None):
    transform=gt or from_origin(1000,2000,10,10)
    with rasterio.open(path,'w',driver='GTiff',height=values.shape[0],
                        width=values.shape[1],count=1,dtype='uint8',nodata=nodata,
                        crs='EPSG:31985',transform=transform) as ds:
        ds.write(values,1)


def test_raster_real_tiff_readwrite(tmp_path,monkeypatch):
    install_fake_gdal(monkeypatch)
    a=tmp_path/'a.tif'; b=tmp_path/'b.tif'; output=tmp_path/'resultado.tif'
    ar1=np.array([[1,1,2],[2,0,255]],dtype=np.uint8)
    ar2=np.array([[4,4,5],[4,5,255]],dtype=np.uint8)
    newtif(a,ar1);newtif(b,ar2)
    result=run_raster_combination([a,b],output)
    if result['combinations']!=4 or result['valid_pixels']!=5:
        raise AssertionError(result)
    with rasterio.open(output) as ds:
        values=ds.read(1)
        if ds.count!=1 or ds.nodata!=0 or ds.crs.to_epsg()!=31985:
            raise AssertionError('GeoTIFF de saída com metadados incorretos')
        if values[1,1]==0 or values[1,2]!=0:
            raise AssertionError(f'Máscara ou código zero indevidamente descartado: {values}')
        if not (values[0,0]==values[0,1]):
            raise AssertionError('Pixels com a mesma combinação receberam códigos distintos')
    if result['area_ha']!=pytest.approx(.05):
        raise AssertionError('Área raster incorreta')
    if len(result['rows'])!=4:
        raise AssertionError('CSV incompleto')
    with rasterio.open(a) as ds:
        if not np.array_equal(ds.read(1),ar1):
            raise AssertionError('Entrada original foi alterada')


def test_reject_incompatible_grids(tmp_path,monkeypatch):
    install_fake_gdal(monkeypatch)
    a=tmp_path/'a.tif';b=tmp_path/'b.tif'
    newtif(a,np.array([[1,2]],dtype=np.uint8))
    newtif(b,np.array([[1,2]],dtype=np.uint8),gt=from_origin(1005,2000,10,10))
    with pytest.raises(ValueError,match='Grades'):
        run_raster_combination([a,b],tmp_path/'out.tif')


def test_preserves_preexisting_on_cancel(tmp_path,monkeypatch):
    install_fake_gdal(monkeypatch)
    a=tmp_path/'a.tif';b=tmp_path/'b.tif';out=tmp_path/'out.tif'
    newtif(a,np.array([[1,2]],dtype=np.uint8))
    newtif(b,np.array([[3,4]],dtype=np.uint8))
    out.write_bytes(b'original')
    with pytest.raises(InterruptedError):
        run_raster_combination([a,b],out,cancelled=lambda:True)
    if out.read_bytes()!=b'original':
        raise AssertionError('Cancelamento modificou destino')
