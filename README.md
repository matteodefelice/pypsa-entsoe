# Simulating European power systems using open tools and data
This notebook is a sort of proof-of-concept illustrating a simple workflow to simulate the hourly operations of all the European power systems using the following tools and data sources:
  - [PyPSA power system](https://pypsa.org/): one of the most used open power system models
  - [ENTSO-E Transparency Platform](https://transparency.entsoe.eu/): data for all the European power system operators
  - [Copernicus Climate Change Service data (C3S)](https://cds.climate.copernicus.eu/): climate and energy data for all the European countries

The aim of this notebook is to show the possibility to easily simulate current power systems using open data and tools. In principle, this notebook can be used for simple explorations and to analyse specific events, simulating what-if scenarios (e.g., what if we had more wind power installed?) or analysing the impact of climate variability (the used C3S dataset provides a wide set of climatic conditions to test).

## Requirements
The file `requirements.yml` contains the list of the Python modules needed to run the example. The example is using the [open-source solver Cbc](https://github.com/coin-or/Cbc), which can be installed using Anaconda.

## How to use it
Open and run the Jupyter notebook `main.ipynb`

## Limitations
Being a proof-of-concept, the simulation shown in the notebook shows the following limitations: 
  - Country level: the spatial resolution of the simulation is quite coarse and modelling a national power system as a single node hide transmission bottlenecks and the impact of the geographical distribution of generation. A possible improvement might be switching to a Bidding Zone Level (BZN): in this case the data from the ENTSO-E TP would be available while for the wind/solar/hydro we should use the NUTS2 aggregation.
- Storage not realistic: storage (both reservoir and closed-loop pumping) is very simplified. In particular, we are assuming that all the closed-loop pumping storages have 3 hours of storage, which can be a huge underestimation for the Alpine countries. However, this can be improved using more realistic estimation on the storage size of pumping. 
- No distinction between offshore and onshore wind: for simplicity, we are using the same wind speed to derive both onshore and offshore wind capacity factors. This can be solved using the capacity factors provided by the C3S dataset, which include both onshore and offshore. 
- Generation costs: the marginal costs set in PyPSA are mostly based on the [PyPSA-EUR](https://pypsa-eur.readthedocs.io/en/latest/) and on [JRC-FF55-MIX-2030](https://data.jrc.ec.europa.eu/dataset/d4d59b89-89f7-4275-801a-45ea8957e973) and they are the same for all the countries. 
- Missing countries: in some cases, national data is not available. For example SK and UK in 2022 are not available for the entire year but this happens also in other cases. 
- Missing data points in TP: data in the Transparency Platform can be quite patchy, with missing data points in many cases.
- Availability factors and efficiency: the availability factors and efficiency of generators are not realistic and the same for all the countries. In some cases, especially for the French nuclear, this leads to behaviours quite different from the reality. 