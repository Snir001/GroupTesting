from TheWorld import TheWorld
import functools
# import matplotlib.pyplot as plt
import ZFD
import numpy as np
import math
import time

QUARANTINE_DAILY_COST  = 3000
HOSPITAL_DAILY_COST    = 20000
TUBE_COST              = 100
MAX_TUBES_PER_TEST     = 40
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

        LEFT_OUT = [p["id"] for p in sim.world.GetNotQuarantined()]
        print("prev day ended with ", len(LEFT_OUT), "expect new to be:", int(2.2* len(LEFT_OUT)))

        self.world.Infect()

        NOW_SICK= [p["id"] for p in sim.world.GetNotQuarantined()]
        print("we realy have ", len(NOW_SICK), " sicks")
        # NOW_LESS_QUA= set(NOW_SICK)-set(to_quarantine_list)
        self.world.RemoveCured()
        self.world.Hospitalize()
        self.RemoveFromQuarantine()
        self.SendToQuarantine(to_quarantine_list)
        
        NEW_OUT_SICKS= [p["id"] for p in sim.world.GetNotQuarantined()]
        print("but we put ",len(NOW_SICK)-len(NEW_OUT_SICKS) , " in quara and now there are ",len(NEW_OUT_SICKS)," out")


        #TODO: add here how many sicks went to quarantine, and howmany we left outside!
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


############# CREATING TUBES ############
def build_groups(id_list, zfd):
    """

    return a list of lists, each sublist contains ids group of size 'size'
    [[<---12,167--->],[<---12,167--->],[...]]
    """
    group_of_groups = [id_list[group*zfd.words_number:(group+1)*zfd.words_number] for group in range(math.ceil(len(id_list)/zfd.words_number))]
    return group_of_groups

def create_group_tubes(group, zfd):
    """
    create tubes
    word_list - binary word list says in which tube person shuld put his test
    id_list - one group of id for the tubes
    man in group[i] got the zfd.binary_word_list[i]
    """
    tube_size = zfd.binary_length
    tubes = [[] for _ in range(tube_size)]

    #foreach man in the group
    for i in range(len(group)):
        #check the indexes of the 1:
        # man in group[i] got the zfd.binary_word_list[i]
        binary_word=zfd.binary_word_list[i]
        tube_number_list=[j for j in range(zfd.binary_length) if binary_word[j] ]
        for tube_number in tube_number_list:
            tubes[tube_number].append(group[i])
    return tubes


def generate_all_tubes(group_list, zfd):
    """
    return list of all the tubes_per_group.
    """

    tubes_per_group = []
    # create man to word dic:
    for group in group_list:
        group_tubes= create_group_tubes(group,zfd)
        tubes_per_group.append(group_tubes)

    #flat tube list (currently its a list of lists of tubes)
    tubes = [item for sublist in tubes_per_group for item in sublist]
    return tubes

############# GET SICKS IDS #################

def check_vector_covered(man_word, tube_results):
    """
    checks if man word is covered by the tube result.
    """
    for i in range(len(man_word)):
        if man_word[i] and not tube_results[i]:
            return False
    return True


def get_sick_for_group(group_tubes_results, group, zfd):
    """
    for each person, check if the man vector/word is covered by tube vector
    """
    sicks = []
    for i in range(len(group)):
        #man in group[i] got the zfd.binary_word_list[i]
        if check_vector_covered(zfd.binary_word_list[i], group_tubes_results):
            sicks.append(group[i])


    return sicks


def get_sick_from_results(tubes_result, groups, zfd ,sim):  # FIXME: get group size without pass through func
    """
    seperate results to goups of size (group size), and run get_sick_from_group for each group
    """
    # seperate results to tube_groups of size of zfd_binary_word:
    group_results = []
    n=zfd.binary_length
    for i in range(0, len(tubes_result), n):
        group_results.append(tubes_result[i:i+n])

    #for each tube_group, check results:
    sicks = []


    for i in range(len(group_results)):
        g_sicks = get_sick_for_group(group_results[i], groups[i], zfd)
        sicks.append(g_sicks)
        if len(g_sicks)>10:
            print("MORE THAN 10 in group ", i)

    # flat the list
    flat_sick = [item for sublist in sicks for item in sublist]

    return flat_sick


def get_2nd_related(sick_ids):
        related_list = []
        for sick in sick_ids:
            related_list.extend(sim.world.population[sick]['related'])

        related_to_related = []
        for p in related_list:
            related_to_related.extend(sim.world.population[p]['related'])

        related_to_related=set(related_to_related)
        # make list flat
        return list(related_to_related)


############# FOR TESTING ###############

def get_sicks_from_id_list(id_list, sim):
    sicks = []
    for id in id_list:
        if sim.world.population[id]["sick"]:
            sicks.append(id)
    return sicks

########### MAIN ##################

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

    # sick_ids = [0]  # initial sick_ids != []
    start_sim_time = time.process_time()
    
    sick_history=[]

    for _ in range(30):
        start_day_time = time.process_time()

        # make groups
        groups = build_groups(no_quarantine_ids, zfd2)

        SICK = get_sicks_from_id_list(no_quarantine_ids, sim)

        tubes = generate_all_tubes(groups, zfd2)

        # get results of new day
        tubes_results = sim.StartNewDay(tubes, to_quarantine_list)

        #here we should find the prev day left_out

        # get sicks
        sick_ids = get_sick_from_results(tubes_results, groups, zfd2, sim)

        #remember who was sick
        sick_history.extend(sick_ids)

        print("    the test shows ", len(sick_ids), "sicks")

        if (set(SICK)-set(sick_ids)):
            print("REAL: ", len(SICK), "they:")
            print(SICK)
            print("func: ", len(sick_ids), "they:")
            print(sick_ids)

        if not sick_ids:
            pass
        # get_sicks_relatedto related.
        related_2nd=get_2nd_related(sick_ids)

        to_quarantine_list = list(set(related_2nd + sick_ids))

        # to_quarantine_list = []   # everyone in quarantine

        person_in_quara = sim.GetStatus()["In quarintine"]
        ids_in_quara = [p["id"] for p in person_in_quara]

        no_quarantine_ids = list(set(range(size_of_p)) - set(to_quarantine_list)-set(sick_history))
        # no_quarantine_ids = list((set(range(size_of_p)) - set(to_quarantine_list)) - set(ids_in_quara))
        # tubes = [[i] for i in no_quarantine_ids]

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

        end_day_time = time.process_time()
        print()
        print(f"Day {_+1} time = {end_day_time - start_day_time}")


    # plt.title('New Sicks per Day')
    # plt.plot(range(1, len(new_sick_per_day) + 1), new_sick_per_day)
    # plt.show()

    # plt.title('Sick per Day')
    # plt.plot(range(1, len(sick_per_day) + 1), sick_per_day)
    # plt.show()

    # plt.title('Total Healed per Day')
    # plt.plot(range(1, len(total_healed) + 1), total_healed)
    # plt.show()

    # plt.title('Cost per Day')
    # plt.plot(range(1, len(sim.daily_cost) + 1), sim.daily_cost)
    # plt.show()


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

    end_sim_time = time.process_time()
    print(f"Sim time = {end_sim_time - start_sim_time}")
