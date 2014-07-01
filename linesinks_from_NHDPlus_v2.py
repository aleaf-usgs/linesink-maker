'''
develop GFLOW stream network from NHDPlus information
all input shapefiles have to be in the same projected (i.e. ft. or m, not deg) coordinate system
'''
import numpy as np
import os
import sys
sys.path.append('D:/ATLData/Documents/GitHub/GIS/')
import GISio
import shapely.geometry
import math

working_dir = 'D:/ATLData/GFL files/Nicolet/new_linesinks'

# model domain info
farfield = 'M:/GroundWater_Systems/USFS/Nicolet/ARC/Nicolet_FF.shp'
nearfield = 'M:/GroundWater_Systems/USFS/Nicolet/ARC/Nicolet_NF.shp'

# output linesink file
outfile_basename = 'Nicolet'
error_reporting = 'linesinks_from_NHDPlus_v2_errors.txt'

# merged NHD files for major drainage areas in domain
flowlines = os.path.join(working_dir, 'NHDPlus_0407_NAD27_utm16.shp')
elevslope = 'D:/ATLData/BadRiver/BCs/SFR_v4_new_streams/elevslope.dbf'
PlusFlowVAA = 'D:/ATLData/BadRiver/BCs/SFR_v4_new_streams/PlusFlowlineVAA_0407Merge.dbf'

split_by_HUC = True # GFLOW may not be able import if the lss file is too big
HUC_shp = 'D:/ATLData/GFL files/Nicolet/basemaps/HUC8_NAD27_utm16.shp'

# set max error tolerance for simplifying linework 
# (largest distance between original lines and simplified lines, in projection units)
nearfield_tolerance = 100
farfield_tolerance = 300

z_mult = 1/(2.54*12) # elevation units multiplier (from NHDPlus cm to model units)
resistance = 0.3
ScenResistance = 'Rlinesink' # one global parameter for now


def width_from_arboate(arbolate):
    # estimate stream width from arbolate sum
    estwidth = 0.1193*math.pow(1000*arbolate, 0.5032)
    return estwidth


def name(x):
    # convention to name linesinks from NHDPlus
    if x.GNIS_NAME:
        # reduce name down with abbreviations
        abb = {'Branch': 'Br',
               'Creek': 'Crk',
               'East': 'E',
               'North': 'N',
               'River': 'R',
               'South': 'S',
               'West': 'W'}
               
        name = '{} {}'.format(x.name, x.GNIS_NAME)
        for k, v in abb.iteritems():
            name = name.replace(k, v)
    else:
        name = '{} unnamed'.format(x.name)
    return name

    
def write_lss(df, outfile):
    '''
    write GFLOW linesink XML (lss) file from dataframe df
    '''
    # global inputs
    depth = 3 # streambed thickness
    DefaultResistance = 0.3
    ComputationalUnits = 'Feet' # 'Feet' or 'Meters'; for XML output file
    BasemapUnits = 'Meters'
    
    nlines = sum([len(p)-1 for p in df.ls_coords])
    
    print 'writing {} lines to {}'.format(nlines, outfile)
    ofp = open(outfile,'w')
    ofp.write('<?xml version="1.0"?>\n')
    ofp.write('<LinesinkStringFile version="1">\n')
    ofp.write('\t<ComputationalUnits>{}</ComputationalUnits>\n\t<BasemapUnits>{}</BasemapUnits>\n\n'.format(ComputationalUnits, BasemapUnits))

    for comid in df.index:
        ofp.write('\t<LinesinkString>\n')
        ofp.write('\t\t<Label>{}</Label>\n'.format(df.ix[comid, 'ls_name']))
        ofp.write('\t\t<HeadSpecified>1</HeadSpecified>\n')
        ofp.write('\t\t<StartingHead>{:.2f}</StartingHead>\n'.format(df.ix[comid, 'maxElev']))
        ofp.write('\t\t<EndingHead>{:.2f}</EndingHead>\n'.format(df.ix[comid, 'minElev']))
        ofp.write('\t\t<Resistance>{}</Resistance>\n'.format(df.ix[comid, 'resistance']))
        ofp.write('\t\t<Width>{:.2f}</Width>\n'.format(df.ix[comid, 'width']))
        ofp.write('\t\t<Depth>{:.2f}</Depth>\n'.format(resistance))
        ofp.write('\t\t<Routing>{}</Routing>\n'.format(df.ix[comid, 'routing']))
        ofp.write('\t\t<EndStream>{}</EndStream>\n'.format(df.ix[comid, 'end_stream']))
        ofp.write('\t\t<OverlandFlow>0</OverlandFlow>\n')
        ofp.write('\t\t<EndInflow>0</EndInflow>\n')
        ofp.write('\t\t<ScenResistance>{}</ScenResistance>\n'.format(df.ix[comid, 'ScenResistance']))
        ofp.write('\t\t<Drain>0</Drain>\n')
        ofp.write('\t\t<ScenFluxName>__NONE__</ScenFluxName>\n')
        ofp.write('\t\t<Gallery>0</Gallery>\n')
        ofp.write('\t\t<TotalDischarge>0</TotalDischarge>\n')
        ofp.write('\t\t<InletStream>0</InletStream>\n')
        ofp.write('\t\t<OutletStream>0</OutletStream>\n')
        ofp.write('\t\t<OutletTable>__NONE__</OutletTable>\n')
        ofp.write('\t\t<Lake>0</Lake>\n')
        ofp.write('\t\t<Precipitation>0</Precipitation>\n')
        ofp.write('\t\t<Evapotranspiration>0</Evapotranspiration>\n')
        ofp.write('\t\t<Farfield>1</Farfield>\n')
        ofp.write('\t\t<chkScenario>false</chkScenario>\n')
        ofp.write('\t\t<AutoSWIZC>0</AutoSWIZC>\n')
        ofp.write('\t\t<DefaultResistance>{:.2f}</DefaultResistance>\n'.format(DefaultResistance))
        ofp.write('\t\t<Vertices>\n')
        
        # now write out linesink vertices
        for x, y in df.ix[comid, 'ls_coords']:
            ofp.write('\t\t\t<Vertex>\n')
            ofp.write('\t\t\t\t<X> {:.2f}</X>\n'.format(x))
            ofp.write('\t\t\t\t<Y> {:.2f}</Y>\n'.format(y))
            ofp.write('\t\t\t</Vertex>\n')
            
        ofp.write('\t\t</Vertices>\n')
        ofp.write('\t</LinesinkString>\n\n')
    ofp.write('</LinesinkStringFile>')
    ofp.close()
'''
import arcpy
# initialize the arcpy environment
arcpy.env.workspace = working_dir
arcpy.env.overwriteOutput = True
arcpy.env.qualifiedFieldNames = False
arcpy.CheckOutExtension("spatial") # Check spatial analyst license

# clip NHD flowlines to domain
arcpy.Clip_analysis(flowlines, farfield, os.path.join(working_dir, 'flowlines_clipped.shp'))

# convert farfield polygon to donut by erasing the nearfield area (had trouble doing this with shapely)
arcpy.Erase_analysis(farfield, nearfield, os.path.join(working_dir, 'ff_cutout.shp')
'''
# open error reporting file
efp = open(error_reporting, 'w')

# read linework shapefile into pandas dataframe
df = GISio.shp2df(os.path.join(working_dir, 'flowlines_clipped.shp'), geometry=True, index='COMID')
elevs = GISio.shp2df(elevslope, index='COMID')
pfvaa = GISio.shp2df(PlusFlowVAA, index='COMID')

# check for MultiLineStrings and drop them (these are lines that were fragmented by the boundaries)
mls = [i for i in df.index if 'multi' in df.ix[i]['geometry'].type.lower()]
df = df.drop(mls, axis=0)

# join everything together
df = df.join(elevs, how='inner', lsuffix='fl', rsuffix='elevs')
df = df.join(pfvaa, how='inner', lsuffix='fl', rsuffix='pfvaa')

# read in nearfield and farfield
nf = GISio.shp2df(nearfield, geometry=True)
ff = GISio.shp2df(os.path.join(working_dir, 'ff_cutout.shp'), geometry=True)
ffg = ff.iloc[0]['geometry'] # shapely geometry object for farfield

print '\nidentifying farfield and nearfield linesinks'
df['farfield'] = [line.intersects(ffg) for line in df['geometry']]

print 'simplifying linework geometries to reduce equations...'
#(see http://toblerity.org/shapely/manual.html)
df['geometry_nf'] = df['geometry'].map(lambda x: x.simplify(nearfield_tolerance))
df['geometry_ff'] = df['geometry'].map(lambda x: x.simplify(farfield_tolerance))


print 'assigning attributes for GFLOW input...'

# routing
df['routing'] = len(df)*[1]
df.loc[df['farfield'], 'routing'] = 0 # turn off all routing in farfield (conversely, nearfield is all routed)

# elevations
min_elev_col = [c for c in df.columns if 'minelev' in c.lower()][0]
max_elev_col = [c for c in df.columns if 'maxelev' in c.lower()][0]
df['minElev'] = df[min_elev_col] * z_mult
df['maxElev'] = df[max_elev_col] * z_mult
df['dStage'] = df['maxElev'] - df['minElev']

print "adjusting elevations for comids with zero-gradient..."
# record up and downstream comids
df['dncomid'] = [list(df[df['Hydroseq'] == df.ix[i, 'DnHydroseq']].index) for i in df.index]
df['upcomids'] = [list(df[df['DnHydroseq'] == df.ix[i, 'Hydroseq']].index) for i in df.index]

comids0 = df[df['dStage'] == 0].COMIDfl
efp.write('zero-gradient errors:\n')
efp.write('comid, upcomids, downcomid, elevmax, elevmin\n')
zerogradient = []

for comid in comids0:

    # get up and down comids/elevations
    upcomids = df[df.index == comid]['upcomids'].item()
    upelevsmax = [df[df.index == uid]['maxElev'].item() for uid in upcomids]
    dncomid = df[df.index == comid]['dncomid'].item()
    dnelevmin = [df[df.index == dnid]['minElev'].item() for dnid in dncomid]
    
    # adjust elevations for zero gradient comid if there is room
    if len(upcomids) > 0 and np.min(upelevsmax) > df.ix[comid, 'maxElev']:
        df.loc[comid, 'maxElev'] = 0.5 * (df.ix[comid, 'maxElev'] + np.min(upelevsmax))
    elif len(dncomid) > 0 and dnelevmin < df.ix[comid, 'minElev']:
        df.loc[comid, 'minElev'] = 0.5 * (df.ix[comid, 'minElev'] + dnelevmin)
    # otherwise report to error file
    else:
        farfield = df.ix[comid, 'farfield']
        if not farfield:
            efp.write('{},{},{},{:.2f},{:.2f}\n'.format(comid, upcomids, dncomid, df.ix[comid, 'maxElev'].item(),
                      df.ix[comid, 'minElev'].item()))
            df.loc[comid, 'routing'] = 0
            zerogradient.append(comid)

print "\nWarning!, the following comids had zero gradients:\n{}".format(zerogradient)
print "routing for these was turned off. Elevations must be fixed manually"

# convert lists in dn and upcomid columns to strings (for writing to shp)
df['dncomid'] = df['dncomid'].map(lambda x: ' '.join([str(c) for c in x])) # handles empties
df['upcomids'] = df['upcomids'].map(lambda x: ' '.join([str(c) for c in x]))


# end streams
# evaluate whether downstream segment is in farfield
downstream_ff = []
for i in range(len(df)):
    try:
        dff = df.ix[df.iloc[i].dncomid[0], 'farfield'].item()
    except:
        dff = True
    downstream_ff.append(dff)
    
# set segments with downstream segment in farfield as End Segments
df['end_stream'] = len(df) * [0]
df.loc[downstream_ff, 'end_stream'] = 1 # set

# widths
arbolate_sum_col = [c for c in df.columns if 'arbolate' in c.lower()][0]
df['width'] = df[arbolate_sum_col].map(lambda x: width_from_arboate(x))

# resistance
df['resistance'] = resistance
df.loc[df['farfield'], 'resistance'] = 0

# resistance parameter (scenario)
df['ScenResistance'] = ScenResistance
df.loc[df['farfield'], 'ScenResistance'] = '__NONE__'

# names
df['ls_name'] = len(df)*[None]
df['ls_name'] = df.apply(name, axis=1)

# coordinates
def xy_coords(x):
    xy = zip(x.coords.xy[0], x.coords.xy[1])
    return xy
df.loc[np.invert(df['farfield']), 'ls_coords'] = df['geometry_nf'].apply(xy_coords) # nearfield coordinates
df.loc[df['farfield'], 'ls_coords'] = df['geometry_ff'].apply(xy_coords) # farfield coordinates

# compare number of line segments before and after
npoints_orig = sum([len(p)-1 for p in df['geometry'].map(lambda x: x.xy[0])])
npoints_simp = sum([len(p)-1 for p in df.ls_coords])

print '\nnumber of lines in original NHD linework: {}'.format(npoints_orig)
print 'number of simplified lines: {}\n'.format(npoints_simp)

if split_by_HUC:
    # intersect lines with HUCs; then group dataframe by HUCs
    HUCs_df = GISio.shp2df(HUC_shp, index='HUC', geometry=True)
    df['HUC'] = len(df)*[None]
    for HUC in HUCs_df.index:
        lines = [line.intersects(HUCs_df.ix[HUC, 'geometry']) for line in df['geometry']]
        df.loc[lines, 'HUC'] = HUC
    dfg = df.groupby('HUC')

    # write lines for each HUC to separate lss file
    HUCs = np.unique(df.HUC)
    for HUC in HUCs:
        dfh = dfg.get_group(HUC)
        outfile = '{}_{}.lss.xml'.format(outfile_basename, HUC)
        write_lss(dfh, outfile)
else:
    write_lss(df, '{}.lss.xml'.format(outfile_basename))

# write shapefile of results; first make combined geometry column
df = df.drop([c for c in df.columns if 'geometry' in c], axis=1)
df['geometry'] = df['ls_coords'].map(lambda x: shapely.geometry.LineString(x))
df = df.drop(['ls_coords'], axis=1)
GISio.df2shp(df, outfile_basename.split('.')[0]+'.shp', 'geometry', flowlines[:-4]+'.prj')

efp.close()
print 'Done!'



'''

the shapely way to create a donut (didn't work)
# create a donut for the farfield by clipping out the nearfield area
nfg, ffg = ff.iloc[0]['geometry'], nf.iloc[0]['geometry']
ff_clip = ffg.difference(nfg)


# compare with actual linesinks from FC Potowatami model
Pot_ls = GISio.shp2df('D:/ATLData/GFL files/Nicolet/overlapping_GFLOW/shps/Potawatomi_Final_lines.shp', geometry=True)
# write back out to shape
GISio.df2shp(df, 'FCP_test_s.shp', 'geometry_s', 'FCP_test.prj')
'''


