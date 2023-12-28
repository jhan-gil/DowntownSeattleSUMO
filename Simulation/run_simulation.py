import sys
import traci

#######################################
### 1- CONNECT TO SUMO SIMULATION TOOL
#######################################
# traci.start(["sumo-gui", "-c", "Bigger_Seattle.sumocfg"])
##  The simulation above is the old one used in https://github.com/Yiran6/MatSumo. We used this as the basis of our work
# traci.start(["sumo-gui", "-c", "test_fariviewAve_reformed_Seattle.sumocfg"])
## In the simulation above, we tried to force vehicles used fairview avenue (which is a main street) using corridor
## coordination, increasing speed, increasing priority, etc. The problem was that without the second part of this code,
## vehicles did not have reasonable routing and were using roads with low priority too much.
traci.start(["sumo-gui", "-c", "clean_reformed_Seattle.sumocfg"])

################################################
### 2- ELIMINATE THE EFFECT OF PEDESTRAIN LANES
## we used the commented lines in part 3 and found out that the speed of pedestrian lanes in the latest version of SUMO
## negatively affects the travel time of edges. This resulted in writing this part.
## https://github.com/eclipse-sumo/sumo/issues/14181
################################################
SMALL_SPEED_LIMIT = 8.94  # meter per second --  20 mph
# we use this speed if we can't find the speed limit of adjacent vehicle lane
lane_ids = traci.lane.getIDList()
for lane_id in lane_ids:
    if "pedestrian" in traci.lane.getAllowed(lane_id):
        # set pedestrian disallowed and adjust the speed limit to vehicles'
        # traci.lane.setDisallowed(lane_id, "pedestrian")
        ref_lane = lane_id[:-2] + "_1"
        if ref_lane in lane_ids:
            speed_limit = traci.lane.getMaxSpeed(ref_lane)
        else:
            speed_limit = SMALL_SPEED_LIMIT
        # if speed_limit < SMALL_SPEED_LIMIT:
        #     print(lane_id, speed_limit)
        traci.lane.setMaxSpeed(lane_id, speed_limit)


###############################
### 3- RUN THE SIMULATION LOOP
###############################
last_step = 5*3600*10
step = 0
# while step < last_step:  # uncomment this if you want the simulation stop in a certain time
while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep()
    step += 1
    print(f'step: {step}')
    # # observe the travel time on links
    # observed_id = "-428087138#0"
    # left_id = "-6464775#4"
    # right_id = "-560096281#2"
    # travel_time = traci.edge.getTraveltime(observed_id)
    # print("center street: {}. Speed limit: {}".format(travel_time, traci.lane.getMaxSpeed("{}_1".format(observed_id))))
    # print("left street: {}. Speed limit: {}".format(traci.edge.getTraveltime(left_id), traci.lane.getMaxSpeed("{}_1".format(left_id))))
    # print("right street: {}. Speed limit: {}".format(traci.edge.getTraveltime(right_id), traci.lane.getMaxSpeed("{}_1".format(right_id))))

# Close TraCI connection
traci.close()
sys.stdout.flush()


