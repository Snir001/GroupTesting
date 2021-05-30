from TheWorld import TheWorld
import functools
import matplotlib.pyplot as plt
import ZFD
# import numpy as np
import math

import time
start_time = time.process_time()

QUARANTINE_DAILY_COST  = 3000
HOSPITAL_DAILY_COST    = 20000
TUBE_COST              = 100
MAX_TUBES_PER_TEST     = 20
MIN_DAYS_IN_QUARANTINE = 4

LOW       = 0
HIGH      = 1
FORBIDDEN = 2

 
class WorldSimulator:

    def __init__(self):
        self.day = 0
        self.daily_cost = []
        self.world = TheWorld()
    
    # Get list of ID's lists and return the results:
    # 0 - No sicks
    # 1 - At least a single sick
    # 2 - If someone's test splitted into more than MAX_TUBES_PER_TEST
    def CheckTubes(self, tubes):
        results = []
        tubes_per_id = {}
        for tube in tubes:
            result = 0
            for person_id in tube:
                self.world.population[person_id]["test dates"].append(self.day)
                
                if person_id in tubes_per_id:
                    tubes_per_id[person_id] += 1
                    if tubes_per_id[person_id] > MAX_TUBES_PER_TEST:
                        result = 2
                        break
                else:
                    tubes_per_id[person_id] = 1
                if self.world.population[person_id]["sick"]:
                    result = 1
            results.append(result)
        return results
    
    # Get ID's and send them to quarantine
    def SendToQuarantine(self, ids_list):
        for person_id in ids_list:
            self.world.population[person_id]["in quarantine"] = True
            self.world.population[person_id]["days in quarantine"] = 0
    
    # Detract people from quarantine
    # Person is get out of quarantine if either he cured
    # or if 4 days of quarantine have passed, the latest.
    def RemoveFromQuarantine(self):
        quarantined = self.world.GetQuarantined()
        for person in quarantined:
            person_id = person["id"]
            days_in_quarantine = person["days in quarantine"] + 1

            if (days_in_quarantine > MIN_DAYS_IN_QUARANTINE) and (person["cured"] or not person["sick"]):
                self.world.population[person_id]["in quarantine"] = False
                self.world.population[person_id]["out of quarantine"] = True
            else:
                self.world.population[person_id]["days in quarantine"] = days_in_quarantine


    def CalcDailyCost(self, num_of_tubes):
        quarantine_cost = QUARANTINE_DAILY_COST*len(self.world.GetQuarantined())
        hospital_cost = HOSPITAL_DAILY_COST*len(self.world.GetHospitalized())
        tube_cost = TUBE_COST*num_of_tubes
        self.daily_cost.append(quarantine_cost + hospital_cost + tube_cost)

    def StartNewDay(self, tubes = [], to_quarantine_list = []):
        self.day += 1
        results = self.CheckTubes(tubes)
        self.world.Infect()
        self.world.RemoveCured()
        self.world.Hospitalize()
        self.RemoveFromQuarantine()
        self.SendToQuarantine(to_quarantine_list)
        self.CalcDailyCost(len(tubes or []))
        return results

    # Return a dictionary depend on the requested verbosity
    # LOW       - Number of: quarantined, out of quarintine and hospitalized 
    # HIGH      - Allowed details of: quarantined, out of quarintine and hospitalized
    # FORBIDDEN - Return full detailes about the pandemic's status 
    def GetStatus(self, verbose=HIGH):
        if verbose == LOW:
            return {
                    "num of people in quarintine"     : len(self.world.GetQuarantined()),
                    "num of people out of quarintine" : len(self.world.GetOutOfQuarantine()),
                    "num of people in hospitalized"   : len(self.world.GetHospitalized())
                   }
        
        if verbose == HIGH:
            return {
                    "In quarintine"     : list(map(self.GetAuthDetailes, self.world.GetQuarantined())),
                    "Out of quarintine" : list(map(self.GetAuthDetailes, self.world.GetOutOfQuarantine())),
                    "Hospitalized"      : list(map(self.GetAuthDetailes, self.world.GetHospitalized())),
                   }

        if verbose == FORBIDDEN:
            return {
                    "In quarintine"     : self.world.GetQuarantined(),
                    "Not in quarintine" : self.world.GetNotQuarantined(),
                    "Out of quarintine" : self.world.GetOutOfQuarantine(),
                    "Hospitalized"      : self.world.GetHospitalized(),
                    "Cured"             : self.world.GetCured(),
                    "Not yet sick"      : self.world.GetNotYetSicks()
                   }

    # Return detail the user id allowed to see
    def GetAuthDetailes(self, person):
        return {
                "id"                : person["id"],
                "related"           : person["related"],
                "in hospital"       : person["in hospital"], 
                "in quarantine"     : person["in quarantine"],
                "out of quarantine" : person["out of quarantine"], 
                "test dates"        : person["test dates"]
               }

    # def ToQuarantine(self):
    #     if day == 0:
    #         return range(len(self.world.population))
    #     return []




def build_groups(id_list, size):
    """
    return a list of lists, each sublist contains ids group of size 'size'
    [[<---12,167--->],[<---12,167--->],[...]]
    """
    group_of_groups = [id_list[group*size:(group+1)*size] for group in range(math.ceil(len(id_list)/size))]
    return group_of_groups

def man_to_word(word_list, group):
    """
    create dic that tie a man with a word (which says in which tube he shuld put his test)
    """
    # if len(word_list) != len(id_list):
    #     print()
    man_to_tubes = {}
    for i, id in enumerate(group):
        man_to_tubes[id] = word_list[i]
    return man_to_tubes

def create_group_tubes(man_to_word_dic, num_of_tubes):
    """
    create tubes
    word_list - binary word list says in which tube person shuld put his test
    id_list - one group of id for the tubes
    """
    tube_size = num_of_tubes # TODO fix this
    tubes = [[] for _ in range(tube_size)]

    #foreach man in the dic
    for id, tube_list in man_to_word_dic.items():
        #check the indexes of the 1:
        tube_number_list=[i for i in range(len(tube_list)) if tube_list[i]]
        for tube_number in tube_number_list:
            tubes[tube_number].append(id)
    return tubes


def generate_all_tubes(zfd, id_list):
    """

    return list of all the tubes_per_group.
    """
    group_of_groups = build_groups(id_list, len(zfd.binary_word_list))

    man_dic_list = []
    tubes_per_group = []
    # create man to word dic:
    for group in group_of_groups:
        man_dic = man_to_word(zfd2.binary_word_list, group)
        man_dic_list.append(man_dic)

        tubes_per_group.append(create_group_tubes(man_dic, len(zfd2.binary_word_list[0])))

    tubes = [item for sublist in tubes_per_group for item in sublist]
    return tubes, man_dic_list



def check_vector_covered(man_word, tube_results):
    """
    checks if man word is covered by the tube result.
    """
    for i in range(len(tube_results)):
        if tube_results[i] != man_word[i]:
            return False
    return True


def get_sick_for_group(tubes_results, man_to_tube):
    """
    for each person, check if the man vector/word is covered by tube vector
    """
    sicks=[]
    for id, word in man_to_tube.items():
        if check_vector_covered(word, tubes_results):
            sicks.append(id)
    return sicks




def get_sick_from_results(tubes_result, man_to_tube_list, group_size,sim):  # FIXME: get group size without pass through func
    """
    seperate results to goups of size (group size), and run get_sick_from_group for each group
    """
    # seperate results to tube_groups of size of zfd_wrod
    test_groups = [tubes_result[group * group_size:(group + 1) * group_size] for group in range(math.ceil(len(tubes_result) / group_size))]
    #for each tube_group, check results:
    sicks = []
    for i, tube_g in enumerate(test_groups):
        
        REAL_SICK = get_sicks_from_id_list(man_to_tube_list[i].keys(), sim)
        print("iter ",i," REAL found: ", len(REAL_SICK)," sicks")
        print("they: ", REAL_SICK)

        g_sicks = get_sick_for_group(tube_g, man_to_tube_list[i])
        sicks.append(g_sicks)


        print("iter ",i," FUNC found: ", len(g_sicks)," sicks")
        print("they: ", g_sicks)
    return sicks




############# FOR TESTING ###############

def get_sicks_from_id_list(id_list, sim):
    sicks = []
    for id in id_list:
        if sim.world.population[id]["sick"]:
            sicks.append(id)
    return sicks





if __name__ == '__main__':
    sim = WorldSimulator()
    zfd2 = ZFD.zfd(21, 3, 23)   # 23 [21, 3, 19]23 483 23^3 = 12,167 m=10

    sick_per_day = [len(sim.world.GetNotQuarantined())]
    new_sick_per_day = [len(sim.world.GetNotQuarantined())]
    total_healed = [0]
    to_quarantine_list = []
    tubes_per_day = []

    size_of_p = (len(sim.world.population))
    no_quarantine_ids = list(range(size_of_p))
    # tubes=[ [id1,id2,...] ,[id3,id4,...],[id1,id2,...] ]
    tubes = [[i] for i in range(size_of_p)]
    # to_quarantine_list = [i for i in range(size_of_p)] # everyone in quarantine

    tubes, man_dic_list = generate_all_tubes(zfd2, no_quarantine_ids)
    tubes_results = sim.StartNewDay(tubes, to_quarantine_list)
    sicks = get_sick_from_results(tubes_results, man_dic_list, len(zfd2.binary_word_list[0]), sim)
    print("done. working time: ",time.process_time() - start_time)
    exit()
    for _ in range(30):
        tubes_results = sim.StartNewDay(tubes, to_quarantine_list)

        infected_tubes_places = [i for i in range(len(tubes_results)) if tubes_results[i] == 1]
        sick_ids = [no_quarantine_ids[i] for i in infected_tubes_places]

        related_to_sick = []
        for sick in sick_ids:
            related_to_sick.append(sim.world.population[sick]['related'])

        # make list flat
        related_ids = [item for sublist in related_to_sick for item in sublist]



        related_to_related = []
        for p in related_ids:
            related_to_related.append(sim.world.population[p]['related'])

        # make list flat
        related_to_related_flat = [item for sublist in related_to_related for item in sublist]
        to_quarantine_list = (set(list(related_ids) + related_to_related_flat + sick_ids))

        # to_quarantine_list = []   # everyone in quarantine

        no_quarantine_ids = list(set(range(size_of_p)) - set(to_quarantine_list))
        tubes = [[i] for i in no_quarantine_ids]
        if sick_ids == []:
            tubes = []
        tubes_per_day.append(len(tubes))


        _sick_pepole = [p["id"] for p in sim.world.GetSicks()]
        _quarantine_list = [p["id"] for p in sim.world.GetQuarantined()]
        _sick_not_q = set(_sick_pepole) - set(_quarantine_list)
        # print(_sick_not_q)
        # _not detected = list(set(sick_ids) - to_quarantine_list)
        # quarantine = sim.world.GetQuarantined()
        # tubes=GetQuarantined()

        status = sim.GetStatus(LOW)
        status = sim.GetStatus(HIGH)
        status = sim.GetStatus(FORBIDDEN)
        # new_sick_per_day.append(len(list(set(sick_ids) - to_quarantine_list)))
        sick_per_day.append(len(sim.world.GetNotQuarantined()))   # TODO: check GetNotQuarantined()
        total_healed.append(len(sim.world.GetCured()))
        if not sim.world.GetNotYetSicks():
            break

    # plt.title('New Sicks per Day')
    # plt.plot(range(1, len(new_sick_per_day) + 1), new_sick_per_day)
    # plt.show()

    plt.title('Sick per Day')
    plt.plot(range(1, len(sick_per_day) + 1), sick_per_day)
    plt.show()

    plt.title('Total Healed per Day')
    plt.plot(range(1, len(total_healed) + 1), total_healed)
    plt.show()

    plt.title('Cost per Day')
    plt.plot(range(1, len(sim.daily_cost) + 1), sim.daily_cost)
    plt.show()
    print('TOTAL COST ', f"{sum(sim.daily_cost):,}")
    print(sim.daily_cost)
    print('TOTAL SICK ', f"{(size_of_p-len(status['Not yet sick'])):,}")
    print(sick_per_day)
    print('TOTAL TUBES COST ', f"{sum(tubes_per_day)*100:,}")
    print(tubes_per_day)
    # plt.plot(range(len(sick_per_day)),sick_per_day)
    # plt.show()
    # plt.plot(range(len(total_healed)),total_healed)
    # plt.show()
    # plt.plot(range(len(sim.daily_cost)),sim.daily_cost)
    # plt.show()
