import sys
import numpy as np
import pickle
import traci
# import libsumo as traci

edge_list_address = 'valid_edges_2023-06-29 12 09 55.txt'
traci_edge_vehicle_address = 'new output/edge_vehicle_output_min.pickle'
traci_edge_arrived_vehicle_address = 'new output/edge_arrived_vehicle_output_min.pickle'


def aggregate_vehicles_on_edge(disaggregate_data: dict):
    # new_dict = {edge: set() for edge in edge_list} # delete edges with no vehicles to reduce size
    new_dict = {}
    for step_dict in disaggregate_data.values():
        for edge in step_dict.keys():
            vehicles = step_dict[edge]
            if vehicles:
                if new_dict.get(edge) is None:
                    new_dict[edge] = set(vehicles)
                else:
                    new_dict[edge].update((step_dict[edge]))
    return new_dict


def export_output(output, address: str = traci_edge_vehicle_address):
    with open(address, 'ab') as f:
        pickle.dump(output, f)


def read_edge_list(address: str = edge_list_address):
    edge_list = []
    with open(address, 'r') as f:
        for line in f:
            edge_list.append(line.rstrip())
    return edge_list


def get_checking_dicts(last_seen, min_stay_steps, validation_range, current_min_data, last_min_data):
    dicts = []
    # simplest form:
    # if last_seen >= min_stay_steps:
    #     other_minute_data = current_min_data
    #     val_start_time = last_seen - min_stay_steps
    # else:
    #     other_minute_data = last_min_data
    #     val_start_time = 600 - (min_stay_steps - last_seen)
    #
    # dicts.append(other_minute_data[str(val_start_time)])

    # correct form
    val_start_time = last_seen - min_stay_steps - validation_range
    val_end_time = last_seen - min_stay_steps + validation_range

    if val_start_time <= 0 < val_end_time:
        for i in range(val_start_time, 1):
            dicts.append(last_min_data[str(i%600)])
            # i used % cuz if it's 0, we should use last_min_data[0] and not last_min_data[600]
        for i in range(1, val_end_time):
            dicts.append(current_min_data[str(i)])

    else:
        if val_start_time < 0 and val_end_time <= 0:
            val_start_time += 600
            val_end_time += 600
            current_min_data = last_min_data
        for i in range(val_start_time, val_end_time):
            dicts.append(current_min_data[str(i)])

    return dicts



def get_last_edgeID(vehicle_id: str, minute_data: dict, last_minute_data: dict):
    min_stay_steps = 100  # second*10
    validation_range = 20  # second*10

    ans = None
    flag = False
    for last_time, data in reversed(minute_data.items()):
        for edge2, pc_list in data.items():
            if vehicle_id in pc_list:
                msg = f'vehicle {vehicle_id} arrived on {edge2} at step{last_time} of this minute'
                flag = True
                # ans = edge2

            ##### check start
                # now we'll check if this vehicle was on main edges for at least min_stay_steps/10 seconds
                # we should see if the vehicle could be found in min_stay_steps before last_time
                # we can't just look at T = (last_time - min_stay_steps) cuz sometimes vehicle vanishes
                # (while changing edge) for ~10-20 steps. Therefore, we check T and some steps before and after it.
                checking_dicts = get_checking_dicts(int(last_time), min_stay_steps, validation_range,
                                                    minute_data, last_minute_data)
                # we use checking_dicts instead of only other_minute_data[str(first_time)]
                valid_vehicle = False
                for d in checking_dicts:
                    for edge1, pc_list in d.items():
                    # for edge1, pc_list in other_data[str(first_time)].items():
                        if vehicle_id in pc_list:
                            valid_vehicle = True
                            print(msg+'\t-> VALID')
                            ans = edge2
                            break
                    if valid_vehicle:
                        break

                if not valid_vehicle:
                    # print(msg+f'\t->NOT on main edges for at least {min_stay_steps/10} seconds')
                    # import pdb
                    # pdb.set_trace()
                    total = int(last_time)
                    seen = 0.0
                    print(f'double checking {vehicle_id}')
                    for t, d in reversed(minute_data.items()):
                        for e, edges in d.items():
                            if vehicle_id in edges:
                                seen += 1
                                ratio = seen / total
                                if ratio >= 0.9:
                                    valid_vehicle = True
                                    print(msg+'\t-> VALID by percentage')
                                break
                        if valid_vehicle:
                            break
                    print(ratio)


                if not valid_vehicle:
                    print(msg+f'\t->NOT on main edges for at least {min_stay_steps/10} seconds or 90% of minute_data')

            ##### check end
                break
        if flag:
            break
    return ans


# Connect to SUMO simulation
# traci.start(["sumo-gui", "-c", "Bigger_Seattle.sumocfg"])
traci.start(["sumo-gui", "-c", "clean_reformed_Seattle.sumocfg"])
# traci.start(["sumo-gui", "-c", "test_fariviewAve_reformed_Seattle.sumocfg"])
# edge_ids = traci.edge.getIDList()
# edge_ids = read_edge_list()

# remove pedestrian lanes
# SMALL_SPEED_LIMIT = 4.47  # some random number, I use 10 mph for now
SMALL_SPEED_LIMIT = 8.94  # or 20 mph
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


edge_vehicle_data = dict()
edge_arrived_data = dict()

temp_data = dict()
last_min_data = dict()

vehicle_lookup_table = dict()
all_vehicles = set()
list_aux = list()

tracked_trips = 0
untracked_trips = 0

# Simulation loop
last_step = 5*3600*10
step = 0
first_tracking_step = 0
# while step < last_step:
while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep()
    step += 1
    # if step == 59:
    #     print("hi")
    print(f'step: {step}')

    # changing TAZs every ten minutes. randomly remove half of the links in each TAZ, every ten minutes.
    # Why ten? why half? There's no real reason for that!
    # todo


    # # observe the travel time on links
    # observed_id = "-428087138#0"
    # left_id = "-6464775#4"
    # right_id = "-560096281#2"
    # travel_time = traci.edge.getTraveltime(observed_id)
    # print("center street: {}. Speed limit: {}".format(travel_time, traci.lane.getMaxSpeed("{}_1".format(observed_id))))
    # print("left street: {}. Speed limit: {}".format(traci.edge.getTraveltime(left_id), traci.lane.getMaxSpeed("{}_1".format(left_id))))
    # print("right street: {}. Speed limit: {}".format(traci.edge.getTraveltime(right_id), traci.lane.getMaxSpeed("{}_1".format(right_id))))
    #
    # print()
    # print("")

    if False:
    # if step > first_tracking_step:
        arrived_vehicles = traci.simulation.getArrivedIDList()

        step_data = dict()
        for edge_id in edge_ids:
            vehicles_list = traci.edge.getLastStepVehicleIDs(edge_id)
            pc_list = [veh_id for veh_id in vehicles_list if traci.vehicle.getTypeID(veh_id) == 'passenger']
            if len(pc_list) > 0: step_data[edge_id] = pc_list
        temp_data[str(step % 600)] = step_data.copy()

        for vehicle in arrived_vehicles:

            # if vehicle_lookup_table.get(vehicle) is not None:
            #     edge = vehicle_lookup_table[vehicle]
            #     print(f'latest edge for {vehicle} is {edge}')
            #     if edge_arrived_data.get(edge) is None:
            #         edge_arrived_data[edge] = {vehicle}
            #     else:
            #         edge_arrived_data[edge].add(vehicle)
            # else:
            #     flag = False
            #     for time, data in reversed(temp_data.items()):
            #         for edge, pc_list in data.items():
            #             if vehicle in pc_list:
            #                 print(f'step of this minute: {time}, arrived vehicle {vehicle} was seen on {edge}')
            #                 flag = True
            #
            #                 if edge_arrived_data.get(edge) is None:
            #                     edge_arrived_data[edge] = {vehicle}
            #                 else:
            #                     edge_arrived_data[edge].add(vehicle)
            #
            #                 break
            #         if flag:
            #             break
            edge = get_last_edgeID(vehicle, temp_data, last_min_data)
            if edge is None:
                untracked_trips += 1
            else:
                tracked_trips += 1
                if edge_arrived_data.get(edge) is None:
                    edge_arrived_data[edge] = {vehicle}
                else:
                    edge_arrived_data[edge].add(vehicle)
        if len(arrived_vehicles)>0: print(f' tracked arrived vehicles: {tracked_trips} -- untracked: {untracked_trips}')

        if step % 600 == 0:
            edge_vehicle_data[str(step // 600)] = aggregate_vehicles_on_edge(temp_data)
            last_min_data = temp_data
            temp_data = dict()


with open(traci_edge_vehicle_address, 'wb') as f:
    pickle.dump(edge_vehicle_data, f)

with open(traci_edge_arrived_vehicle_address, 'wb') as f:
    pickle.dump(edge_arrived_data, f)


# Close TraCI connection
traci.close()
sys.stdout.flush()


