import pandas as pd
import numpy as np
import json, pypsa
import plotnine
from plotnine import *

class pypsa_support:
    """
    This static class provides a set of function to support the creation of a PyPSA model using energy-met data.
    """
    @staticmethod
    def generators_from_entsoe(cap:pd.DataFrame, pmin = None, ramping = None, template = pd.DataFrame)->pd.DataFrame:
        """
        """
        mapping = json.load(open('mapping.json', 'r'))
        
        cap = cap.transpose().reset_index()

        cap.columns.values[1] = 'p_nom'
        
        cap['carrier'] = cap['index'].map(mapping)

        cap = cap.groupby(['carrier']).sum(numeric_only=True)

        gen = pd.merge(cap, right = template, left_on = 'carrier', right_on = 'carrier')
        # 
        if pmin is not None:
            pmin['carrier'] = pmin['ProductionType'].map(mapping)
            pmin_df = pmin.groupby(['carrier']).sum(numeric_only = True)['q001']
            
            gen = pd.merge(gen, right = pmin_df, left_on = 'carrier', right_on='carrier', how = 'outer')
            gen['p_min_pu'] = np.where(pd.isna(gen['q001']), gen['p_min_pu'], gen['q001'] / gen['p_nom'])
            
            gen = gen.drop(columns = ['q001'])
        
        if ramping is not None:
            ramping['carrier'] = ramping['ProductionType'].map(mapping)
            gen = pd.merge(gen, right = ramping, left_on = 'carrier', right_on='carrier', how = 'outer')
            gen['ramp_limit_up']   = gen['q999_up'] / gen['p_nom']
            gen['ramp_limit_down'] = gen['q999_down'] / gen['p_nom']


        return(gen)
    @staticmethod
    def stores_from_entsoe(cap:pd.DataFrame)->pd.DataFrame:
        """
        """
        mapping = json.load(open('mapping.json', 'r'))
        
        cap = cap.transpose().reset_index()

        cap.columns.values[1] = 'p_nom'
        
        cap['carrier'] = cap['index'].map(mapping)

        cap = (cap
        .groupby(['carrier'])
        .sum(numeric_only=True)
        .query("carrier in ['hydro', 'PHS']")
        )

        # add efficiency / marginal_cost
        template = pd.read_csv('entsoe_template_stores.csv')

        sto = pd.merge(cap, right = template, left_on = 'carrier', right_on = 'carrier')
        return sto 
    @staticmethod
    def dispatch_plot(n: pypsa.Network, buses:list, snapshots, return_dataframe = False):
        """
        """
        gen_list = n.generators[['carrier', 'bus']].reset_index()
        gen_list['type'] = gen_list['carrier']

        gen = (pd.merge(
            n.generators_t.p
            .unstack()
            .reset_index(), gen_list)
            .groupby(['type', 'bus', 'snapshot'])
            .sum(numeric_only=True)
            .reset_index()
        )

        # define list of storage
        sto_list = n.storage_units[['bus']].reset_index()
        sto_list['type'] = 'storage'

        sto = (pd.merge(
            n.storage_units_t.p
            .unstack()
            .reset_index(), sto_list)
            .groupby(['type', 'bus', 'snapshot'])
            .sum(numeric_only=True).reset_index()
        )

        # define links
        link_list = n.links[['bus1']].reset_index()
        link = (pd.merge(
            n.links_t.p1
            .unstack()
            .reset_index(), link_list)
            .rename(columns= {'bus1': 'bus', 'Link': 'type'})
        )
        link['type'] = link['type'].str[0:4]

        link[0] = link[0] * -1

        df = pd.concat([gen, sto, link]).rename(columns = {0:'prod'})

        dem =  pd.merge(n.loads_t.p_set.reset_index().melt(id_vars=['snapshot']), right = n.loads.reset_index()[['Load', 'bus']], left_on = 'Load', right_on = 'Load')
        dem = dem.loc[dem['snapshot'].isin(snapshots)]

        toplot = df.copy()
        toplot['type'] = toplot['type'].replace(
            {'biomass': 'Other', 
            'coal': 'coal/lignite',
            'lignite': 'coal/lignite',
            'hydr': 'hydro',
            'Derived gasses fleet': 'Other', 
            'oil': 'Other', 
            'onwind':'RES',
            'offwind': 'RES',
            'ror': 'RES',
            'solar':'RES',
            'CCGT' : 'gas',
            'OCGT': 'gas'})
        toplot = toplot.groupby(['type', 'bus', 'snapshot']).sum(numeric_only=True).reset_index()
        aggr = toplot.groupby(['type']).sum(numeric_only=True).reset_index()
        aggr = aggr[abs(aggr['prod']) > 1]
        toplot = toplot[toplot['type'].isin(aggr['type'])]

        if return_dataframe: 
            return toplot
        else:

            plotnine.options.figure_size = (7.4, 8)
            SEL_C = buses
            sel = toplot[toplot['bus'].isin(SEL_C)]
            sel = sel.loc[sel['snapshot'].isin(snapshots)]
            g = (
                ggplot(sel[sel['bus'].map(lambda x: len(str(x)) == 2)], aes(x='snapshot', y='prod')) + 
                geom_area(aes(fill = 'type')) + 
                geom_line(aes(x = 'snapshot', y = 'value'), data= dem[dem['bus'].isin(SEL_C)]) + 
                facet_wrap(['bus'], ncol = 1, scales = 'free') +
                theme_light()
            )

            return g


