from .utils import Habitat
import random
from ..algorithms import migration_astar,MigrationProblem,DepredatorsProblem

class Species:
    def __init__(self, sex: int):
        self.birthday = 0
        self.age = 0
        self.sex = sex
        self.health = round(random.uniform(92,100),3)
        self.full = round(random.uniform(92,100),3)
        self.time_death = random.randint(type(self).life_expectancy()[0], type(self).life_expectancy()[1])
        self.my_speed = random.randint(type(self).speed()[0], type(self).speed()[1])

    def habitat(): raise NotImplementedError()
    def feed_on_vegetation(): raise NotImplementedError()
    def life_expectancy(): raise NotImplementedError()
    def speed(): raise NotImplementedError()
    def prey(): raise NotImplementedError()
    def depredator(): raise NotImplementedError()
    def uninhabitable(): raise NotImplementedError()
    def desnutrition(): raise NotImplementedError()
    def str(): return "Specie"

class Agent(Species):
    def __init__(self, sex: int):
        Species.__init__(self, sex)
        self.path = []
        self.looking_for_food=False
        self.ate=False
        self.time_limb = 0
        self.is_starving = False
        self.feed_way='feed'


    def reaction(self, state):    
        time, zone, colony = state
        if time == self.birthday: self.age += 1
        action = self.get_action(state)
        if action == 'death':
            zone.delete_animal(self)
        elif action == 'migrate':
            self.path[0].delete_animal(self)
            if 1- self.full/100 > 0.7: self.feed_here(self.path[0])
            self.path.pop(0)
            #distance:int = zone.adj_z[self.path[0]]
            #self.time_limb = max(1,distance // self.my_speed)
            self.time_limb = self.get_trip_time(zone,self.path[0])
            if len(self.path)>0 : self.path[0].limb.append((self, time))
        elif action == 'feed':
            self.feed_here(zone)
            if not self.ate:
                if not self.is_starving:
                    self.is_starving = True
                    next_zone, trip_time = self.get_next_zone(zone)
                    self.time_limb = trip_time
                    next_zone.limb.append((self,time))
                else: self.is_starving = False     
        elif action == 'look_for_food':
            next_zone=colony.pick_move(self,(time,zone))
            if next_zone == zone:
                self.looking_for_food=False
                self.feed_here(zone)
            elif next_zone == None: self.looking_for_food=False
            else:
                self.looking_for_food=True
                self.time_limb = self.get_trip_time(zone,next_zone)
                next_zone.limb.append((self,time))
        self.update(state)

    def get_action(self, state):
        if self.age == self.time_death: return 'death'
        if self.is_starving: return 'feed'
        if self.looking_for_food: return 'look_for_food'
        if len(self.path)>0 : return 'migrate'
        weight1 = self.feed_weight(state)
        path, weight2 = self.migrate_weight(state)
        if weight2 < 0.3 and  weight1 < 0.3: return 'nothing'
        if weight2 > weight1:
            self.path=path
            return 'migrate' #Falta comprobar que el path!= none 
        return self.feed_way

    def update(self, state):
        time, zone = state
        hungry = 0 if self.ate else type(self).desnutrition()
        self.full = max(0, self.full - hungry)
        self.health = max(0, self.health - hungry - type(self).uninhabitable()[zone.type])
        if self.health == 0: return True
        if self.time_limb > 0:
            if time == self.birthday: self.age += 1
            if self.age == self.time_death: return True
            floor = 1 if zone.floor > 0 else 0
            self.time_limb = self.time_limb - 1 + floor
        self.ate = False
        return False

    def get_trip_time(self,zone,next_zone):
        distance:int = zone.adj_z[next_zone]
        time_limb = max(1,distance // self.my_speed)
        return time_limb

    def feed_here(self,zone):
        if type(self).feed_on_vegetation() > 0 and zone.vegetation > 0:
            zone.vegetation = max(0,zone.vegetation - type(self).feed_on_vegetation())
            self.full= min(100,self.full + type(self).feed_on_vegetation())
            self.ate = True
            self.is_starving=False
        else:
            for animal in type(self).prey():
                female,male=zone.species[animal]
                if len(female + male)>0: 
                    choice=random.choice(female+male)
                    zone.delete_animal(choice)
                    self.full= min(100,self.full+choice.full)
                    self.ate=True
                    self.is_starving=False
                    return 

    def get_next_zone(self, state):
        _ , zone , _ = state
        max = 0
        result=None
        time = 0
        for next_zone, distance in zone.adj_z.items():
            current =  next_zone.vegetation  if type(self).feed_on_vegetation() > 0 else 0 # vegetacion de la zona
            for animal in self.prey:
                current+= len(zone.species[animal][0])+len(zone.species[animal][1]) # cantidad de presas en la zona
            trip_time=max(1,distance//self.my_speed)
            current-= type(self).uninhabitable()[next_zone] * (trip_time) # nivel de salud que resta cruzar hacia la zona 
            for animal in type(self).depredator():
                current-= len(zone.species[animal][0])+len(zone.species[animal][1]) # cantidad de depredadores en la zona
            if result == None: 
                max=current
                result=next_zone
                time=trip_time
            elif current > max:
                max=current
                result=next_zone
                time=trip_time
            return result, time
 
    def feed_weight(self, state):
        result= self.full/100

    def migrate_weight(self, state):
        _,zone=state
        weight=0
        path=None
        if not zone.type in type(self).habitat():
            problem = MigrationProblem(initial=zone, goal=type(self).habitat())
            path = migration_astar(problem, self.habitat_heuristic(problem))
            if len(path)>0:
                current_weight = self.get_path_weight(path)
                if current_weight>0:
                    weight=current_weight
        is_depredator= lambda specie : specie in self.depredator() and (len(zone.species[specie][0]) > 0 or len(zone.species[specie][1]) > 0)
        depredators=list(filter(is_depredator,zone.species.keys()))
        if len(depredators)>0:
            problem=DepredatorsProblem(initial=zone, goal=self.depredator())
            currentpath=migration_astar(problem, self.depredator_heuristic(problem))
            if len(currentpath)>0:
                 current_weight=self.get_path_weight(path)
                 if current_weight>0 and current_weight<=weight:
                    path = currentpath
        return path,weight

    def get_path_weight(self,path):
        health_left=self.health
        current_zone=path[0]
        for next_zone in path[1:]:
            time_limb = self.get_trip_time(current_zone,next_zone)
            health_left=max(0,health_left-time_limb * type(self).desnutrition())
            current_zone=next_zone
        return health_left/100

    def habitat_heuristic(self,problem): pass
    def depredator_heuristic(self, problem): pass 

class ReactiveAgent(Agent):
    def __init__(self, sex: int):
        Agent.__init__(self, sex)

    def habitat_heuristic(self, problem):
        def h(node):       
            zone = node.state
            result = 0
            for _, (female,male) in zone.species.items():
                animals = female + male
                if len(animals)>0 and not set(problem.goal).isdisjoint(set(animals[0].habitat())):
                    result+=len(animals)
            return zone.total - result
        return h

    def depredator_heuristic(self,problem):
        def h(node):        
            zone=node.state
            result=0
            for specie, (female,male)  in zone.species.items():
                animals=female+male
                if len(animals)>0 and specie in problem.goal:
                    result+=len(animals)
            return  result
        return h

class IntelligentAgent(ReactiveAgent):
    def __init__(self, sex: int):
        Agent.__init__(self, sex)
        self.feed_way='look_for_food'

    def habitat_heuristic(self,problem):
        def h(node):       
            zone=node.state
            result=0
            for _, (female,male) in zone.species.items():
                animals=female+male
                if len(animals)>0 and not set(problem.goal).isdisjoint(set(animals[0].habitat())):
                    result+=len(animals)
            return zone.total - result
        return h

    def depredator_heuristic(self,problem):
        def h(node):       
            zone=node.state
            result=0
            for _, (female,male)  in zone.species.items():
                animals=female+male
                if len(animals)>0 and not set(problem.goal).isdisjoint(set(animals[0].habitat())):
                    result+=len(animals)
            return zone.total - result
        return h 

class BengalTiger(ReactiveAgent):
    def habitat(): return [Habitat.polar, Habitat.tempered]
    def feed_on_vegetation(): return 0.1
    def life_expectancy(): return (20,26)
    def speed(): return(3,5)
    def prey(): return [Rabbit]
    def depredator(): return [PolarBear]
    def uninhabitable(): return {Habitat.polar:0, Habitat.tempered:0, Habitat.tropical:0.8, Habitat.desertic:1.5}
    def desnutrition(): return 1.2
    def str():return "Bengal Tiger"

class GrizzlyBear(ReactiveAgent):
    def habitat(): return [Habitat.tropical, Habitat.desertic]
    def feed_on_vegetation(): return 0
    def life_expectancy(): return (20,30)
    def speed(): return(1,3)
    def prey(): return [Tiger, Rabbit]
    def depredator(): return []
    def uninhabitable(): return {Habitat.polar:2, Habitat.tempered:1, Habitat.tropical:0, Habitat.desertic:0}
    def desnutrition(): return 2
    def str():return "Grizzly Bear"

class Horse(ReactiveAgent):
    def habitat(): return [Habitat.tropical, Habitat.desertic]
    def feed_on_vegetation(): return 1.5
    def life_expectancy(): return (25,30)
    def speed(): return(4,5)
    def prey(): return []
    def depredator(): return [Tiger]
    def uninhabitable(): return {Habitat.polar:0.8, Habitat.tempered:0.4, Habitat.tropical:0, Habitat.desertic:0}
    def desnutrition(): return 0.7
    def str():return "Horse"

class PolarBear(ReactiveAgent):
    def habitat(): return [Habitat.polar, Habitat.tempered]
    def feed_on_vegetation(): return 0.4
    def life_expectancy(): return (20,25)
    def speed(): return(1,3)
    def prey(): return [BengalTiger]
    def depredator(): return []
    def uninhabitable(): return {Habitat.polar:0, Habitat.tempered:0, Habitat.tropical:1, Habitat.desertic:2}
    def desnutrition(): return 2
    def str():return "Polar Bear"

class Rabbit(ReactiveAgent):
    def habitat():return [Habitat.tropical, Habitat.desertic, Habitat.tempered, Habitat.polar]
    def feed_on_vegetation(): return 1
    def life_expectancy(): return (7,9)
    def speed(): return(4,6)
    def prey(): return [Ant]
    def depredator(): return [BengalTiger, GrizzlyBear, Tiger]
    def uninhabitable(): return {Habitat.polar:0, Habitat.tempered:0, Habitat.tropical:0, Habitat.desertic:0}
    def desnutrition(): return 0.3
    def str():return "Rabbit"

class Tiger(ReactiveAgent):
    def habitat(): return [Habitat.tropical]
    def feed_on_vegetation(): return 0
    def life_expectancy(): return (8,10)
    def speed(): return(3,5)
    def prey(): return [Horse, Rabbit]
    def depredator(): return [GrizzlyBear]
    def uninhabitable(): return {Habitat.polar:1, Habitat.tempered:0.5, Habitat.tropical:0, Habitat.desertic:0.2}
    def desnutrition(): return 1.2
    def str():return "Tiger"
      
class Ant(ReactiveAgent):
    def habitat(): return [Habitat.desertic, Habitat.tropical]
    def feed_on_vegetation(): return 0.4
    def life_expectancy(): return (1,2)
    def speed(): return(1,1)
    def prey(): return []
    def depredator(): return [Rabbit]
    def uninhabitable(): return {Habitat.polar:2, Habitat.tempered:1, Habitat.tropical:0, Habitat.desertic:0}
    def desnutrition(): return 0.1
    def str():return "Ant"