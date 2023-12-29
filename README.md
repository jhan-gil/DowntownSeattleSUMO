# Simulation of Downtown Seattle AM peak
In this work, we simulated passenger vehicles and public transportation of Downtown seattle between 5 to 10 AM. The exact simulation period could be modified in step3 of demand generation and in sumocfg file. 
Our network includes south of Mercer St, west of 12th Ave, and north of S Holgate St.

![The network and the TAZs used in the simulation](https://github.com/BlueSoheil99/DowntownSeattleSUMO/blob/main/network%20image.png?raw=true)

- A more detailed documentation will be linked soon. 
- This work was based upon the simulation in
https://github.com/Yiran6/MatSumo (private repo). It also included pedestrians. That simulation could be found in `old files` folder.

Our work was divided into two sections, generating a  demand file (rou.xml) based on the real-world data
and running a reasonable simulation in SUMO.

-------
## Demand generation
If you just want to run the simulation, skip this section.
Demand generation takes place in four steps and 
final output of each step is the input of the next step. Output of the 4th step is the input for the simulation (route file).
- **Step1: Trip generation**
  - Run `step1-read h5.ipynb`
  - Input(s): PSRC trip dataset, estimated for Puget sound population. 
  <span style="color: red;"> The data file is not uploaded yet (1 GB).</span>
  - Output: `psrc_vehicle_trips.csv`, shows [otaz,dtaz,deptm,travtime] for each trip.
  - Description:
    - In this step, we work on trip data of individuals. Each row of the input file shows a trip for a person which could be done in different modes. 
    We first find trips done with cars. Then we try to remove the trips that were shared but used one vehicle (duplicate trips shared between different people).
    -   <span style="color: red;"> Trips are happening in different days and we have not taken that into account. </span>
    -   <span style="color: green;"> add a picture of departure times </span>


  
- **Step2: TAZ calibration**
  - Run `step2-taz filteration_conversion-v.2.ipynb`
  - Input(s): `psrc_vehicle_trips.csv`, `taz2010.shp`, `modified_new_Taz_with_pseudo.add.xml`, TAZ list of different super TAZs (`regions` folder)
  - Output:  `psrc_vehicle_trips_converted_taz.csv`, if either `otaz` or `dtaz` for an input row is not in the simulation network, it is changed to its corresponding pseudo TAZ.
  - Description:
    - For our network we do not have all Puget sound TAZs and just focus on Downtown Seattle.
    Therefore, when we want to simulate trips that go to(come from) out of Downtown Seattle, 
    we need to guess where they exit (enter) our network. 
    The TAZ.add.xml file we used has many pseudo TAZs (TAZs with #taz>=5000) to account for entering and exiting our network if desired in a trip.
    - This code replaces corresponding pseudo TAZs with TAZs that are not present in the simulation network (Downtown Seattle).
    - To develop this code, I assumed multiple super TAZs in King County (pictures are included in the code)
    and used Google Maps to guess how the route of trips from/to those super TAZs to/from Downtown will be and what pseudo TAZ they will pass through. Also, for the trips that have otaz out of downtown, I estimated the time distance from corresponding super TAZs to the assigend pseudo TAZs and adjusted those trips' `deptime` (which is the time they enter our network).
  
- **Step3: Route file (SUMO input) generation**
  - Run `step3-generate_rou.ipynb`
  - Input(s): `psrc_vehicle_trips_converted_taz.csv`,`modified_new_Taz_with_pseudo.add.xml`, start and end time of demand insertion, 
  
  - Output: `(TAZ or od2trips)_psrc_vehicle_trips_converted_taz.rou.xml`
    - In the final step for demand generation, we can generate route files in two ways. 1) 
    - Remember: if you use the first method (od2trips), make sure that you are using the exact TAZ file used in the simulation (in case you change something in this file in `simulation` folder and want to generate demand in `Demand generation` folder) 

    
- **Step4: Make little adjustments**
  - Run `misc.ipynb` in `simulation` folder.
  - Input(s): `(TAZ or od2trips)_psrc_vehicle_trips_converted_taz.rou.xml`
  - Output: adjusted and/or reduced version of input
    - Use it after generating the demand file and copying it into `simulation` folder.

----
## Simulation
To run the simulation, you have to:
1) Have SUMO installed on your system.
2) Install python packages in `requirements.txt`
3) Run `run_simulation.py` file
4) Find the output results in "new output" folder.

- Attention: We had two different types of demand (route) file: 

- Some of the signals in `offset_signal_Seattle_network_reformed connections2.net.xml` were manually changed. 
To use the original specification of traffic signals, use 
`no_alley_Seattle_network_reformed connections.net.xml` instead. Note that this network probably won't work well with 
route files generated with od2trips.
- If you decide to change the hours to something else rather than 5-10am, remove additional demand of public transit in `bus_link_route.rou.xml` and replace it with 
    `new_bus_link_route.rou.xml` in `clean corrected inputs` folder.
