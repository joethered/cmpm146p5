import json
from collections import namedtuple, defaultdict, OrderedDict
from timeit import default_timer as time
from heapq import heappop, heappush
from typing import ItemsView
from operator import itemgetter



Recipe = namedtuple('Recipe', ['name', 'check', 'effect', 'cost', 'heuristic'])
Ingredient = namedtuple('Ingredient', ['name', 'back_check', 'deffect', 'cost', 'heuristic'])
exploration_factor = 5

class State(OrderedDict):
    """ This class is a thin wrapper around an OrderedDict, which is simply a dictionary which keeps the order in
        which elements are added (for consistent key-value pair comparisons). Here, we have provided functionality
        for hashing, should you need to use a state as a key in another dictionary, e.g. distance[state] = 5. By
        default, dictionaries are not hashable. Additionally, when the state is converted to a string, it removes
        all items with quantity 0.

        Use of this state representation is optional, should you prefer another.
    """

    def __key(self):
        return tuple(self.items())

    def __hash__(self):
        return hash(self.__key())

    def __lt__(self, other):
        return self.__key() < other.__key()

    def copy(self):
        new_state = State()
        new_state.update(self)
        return new_state

    def __str__(self):
        return str(dict(item for item in self.items() if item[1] > 0))

def make_checker(rule):
    # Returns a function to determine whether a state meets a rule's requirements.
    # This code runs once, when the rules are constructed before the search is attempted.

    def check(state):
        # This code is called by graph(state) and runs millions of times.
        # Tip: Do something with rule['Consumes'] and rule['Requires'].
        if 'Requires' in rule.keys():
            for requirement, req_value in rule['Requires'].items():
                if (requirement not in state.keys()):
                    return False
                if (state[requirement] == 0):
                    return False
        if 'Consumes' in rule.keys():
            for consumbable, quantity in rule['Consumes'].items():
                if (consumbable not in state.keys()):
                    return False
                if (state[consumbable] < quantity):
                    return False
        return True

    return check

def make_back_checker(rule):
    # Returns a function to determine whether a state meets a rule's requirements.
    # This code runs once, when the rules are constructed before the search is attempted.
    def back_check(state):
        # This code is called by graph(state) and runs millions of times.
        # Tip: Do something with rule['Consumes'] and rule['Requires'].
        for item, quantity in state.items():
            if quantity == 0:
                continue
            if item in rule['Produces'].keys():
                return True
        return False
    return back_check

def get_available_recipes(state, all_recipes):
    ready_recipies = []
    for recipe in all_recipes:
        if recipe.check(state):
            ready_recipies.append(recipe)

    return ready_recipies

def make_effector(rule):
    # Returns a function which transitions from state to new_state given the rule.
    # This code runs once, when the rules are constructed before the search is attempted.

    def effect(state):
        # This code is called by graph(state) and runs millions of times
        # Tip: Do something with rule['Produces'] and rule['Consumes'].
        next_state = state.copy()        
        if 'Consumes' in rule.keys():
            #print("consume")
            for consumbable, quantity in rule['Consumes'].items():
                next_state[consumbable] -= quantity
        for product, quantity in rule['Produces'].items():
            if product not in next_state.keys():
                next_state[product] = quantity
            else:
                next_state[product] += quantity
        return next_state

    return effect

def make_deffector(rule):
    # Returns a function which transitions from state to new_state given the rule.
    # This code runs once, when the rules are constructed before the search is attempted.

    def deffect(state):
        # This code is called by graph(state) and runs millions of times
        # Tip: Do something with rule['Produces'] and rule['Consumes'].
        next_state = state.copy()
        #print("")
        #print("from " + str(state))
        for item, quantity in state.items():
            if item in rule["Produces"]:
                produced = rule['Produces'][item]
                #print("remove " + str(produced) + " " + item)
                next_state[item] -= produced
                if next_state[item] < 0:
                    next_state[item] = 0
                if 'Consumes' in rule.keys():
                    for consumbable, quantity in rule['Consumes'].items():
                        next_state[consumbable] += quantity
                        #print("\t" + consumbable + ": " + str(quantity))
                if 'Requires' in rule.keys():
                    for requirement in rule['Requires'].keys():
                        next_state[requirement] = 1
        #print("   to " + str(next_state))
        return next_state

    return deffect


def make_goal_checker(goal):
    # Returns a function which checks if the state has met the goal criteria.
    # This code runs once, before the search is attempted.

    def is_goal(state):
        # This code is used in the search process and may be called millions of times.
        for item, quantity in goal.items():
            if (item not in state.keys()):
                return False
            if (state[item] < quantity):
                return False
        return True

    return is_goal

def make_start_checker(start):
    # Returns a function which checks if the state has met the goal criteria.
    # This code runs once, before the search is attempted.

    def is_start(state):
        # This code is used in the search process and may be called millions of times.
        for item, quantity in state.items():
            if item in start.keys() and start[item] != quantity:
                return False
            if item not in start.keys() and quantity != 0:
                return False
        return True

    return is_start


def graph(state):
    # Iterates through all recipes/rules, checking which are valid in the given state.
    # If a rule is valid, it returns the rule's name, the resulting state after application
    # to the given state, and the cost for the rule.
    for r in all_recipes:
        if r.check(state):
            yield (r.name, r.effect(state), r.cost, r.heuristic)
            
def reverse_graph(state):
    # Iterates through all recipes/rules, checking which are valid in the given state.
    # If a rule is valid, it returns the rule's name, the resulting state after application
    # to the given state, and the cost for the rule.
    #for items, quantity in state.items():
        
    for i in all_ingredients:
        if i.back_check(state):
            yield (i.name, i.deffect(state), i.cost, i.heuristic)


def make_heuristic(goal):
    def heuristic(state):
        # This heuristic function should guide your search.
        estimate = 0
        for item, quantity in goal.items():
            if state[item] != quantity:
                estimate += abs(quantity - state[item])
        for item, quantity in state.items():
            if item in goal.keys():
                if goal[item] != quantity:
                    estimate += abs(quantity - goal[item])
            else:
                estimate += quantity
        return estimate
    return heuristic

def make_back_heuristic(start, rule):
    def back_heuristic(state):
        # This heuristic function should guide your search.
        estimate = 0
        for item, quantity in start.items():
            if state[item] != quantity:
                estimate += quantity
            else:
                estimate += quantity - state[item]
        if 'Requires' in rule.keys():  
            for item, quantity in state.items():
                if quantity <= 0 and item in rule['Requires'].keys():
                    estimate *= 10
        return estimate
    return back_heuristic


# Search
def search(graph, state, is_goal, limit):
    start_time = time()
    initial_state = state.copy()
    times = {initial_state: 0}
    previous_recipe = {initial_state: (None, None)}
    queue = [(0, initial_state)]
    known_recipes = {}
    current_state = None

    # Search
    while time() - start_time < limit and queue:
        current_game_time, current_state = heappop(queue)
        #print("cur " + str(current_state))
        if is_goal(current_state):
            #print (current_game_time)
            node = None
            if previous_recipe[current_state] is not None:
                node = current_state
            path = []
            while previous_recipe[node][0] is not None:
                path.append(previous_recipe[node][0])
                node = previous_recipe[node][1]
                #print(previous_recipe[node][0])
            total_time = time() - start_time
            return (path[::-1], total_time)
        for name, resulting_state, time_cost, heuristic in graph(current_state):
            new_time = current_game_time + heuristic(resulting_state)
            #print("go " + name)
            #print(resulting_state)
            #if resulting_state in times:
                #print("res " + str(times[resulting_state]))
            #print(new_time)
            if resulting_state not in times or new_time < times[resulting_state]:
                times[resulting_state] = new_time
                previous_recipe[resulting_state] = (name, current_state)
                #print("he " + name)
                if name not in known_recipes:
                    known_recipes[name] = 0
                    #print(name)
                    new_time /= exploration_factor
                heappush(queue, (new_time, resulting_state))



    # Failed to find a path
    #print(time() - start_time)
    print("Failed to find a path from", state, 'within time limit.')
    return None

# Search
def backsearch(reverse_graph, end, is_start, limit):
    start_time = time()
    end_state = end.copy()
    times = {end_state: 0}
    previous_recipe = {end_state: (None, None)}
    queue = [(0, end_state)]
    known_recipes = {}
    current_state = None

    # Search
    while time() - start_time < limit and queue:
        current_game_time, current_state = heappop(queue)
        #print("cur " + str(current_state))
        if is_start(current_state):
            #print (current_game_time)
            node = None
            if previous_recipe[current_state] is not None:
                node = current_state
            path = []
            while previous_recipe[node][0] is not None:
                path.append(previous_recipe[node][0])
                node = previous_recipe[node][1]
                #print(previous_recipe[node][0])
            total_time = time() - start_time
            #print (path)
            #print(current_state)
            #print(current_game_time)
            #print(total_time)
            return (path, total_time)
        for name, resulting_state, time_cost, heuristic in reverse_graph(current_state):
            new_time = current_game_time + heuristic(resulting_state)
            #print("go " + name)
            #print(resulting_state)
            #if resulting_state in times:
                #print("res " + str(times[resulting_state]))
            #print(new_time)
            if resulting_state not in times or new_time < times[resulting_state]:
                #print (new_time)
                times[resulting_state] = new_time
                previous_recipe[resulting_state] = (name, current_state)
                #print("he " + name)
                if name not in known_recipes:
                    known_recipes[name] = 0
                    #print(name)
                    new_time /= exploration_factor
                heappush(queue, (new_time, resulting_state))



    # Failed to find a path
    #print(time() - start_time)
    print("Failed to find a path from", state, 'within time limit.')
    return None

if __name__ == '__main__':
    total_cost = 0
    with open('Crafting.json') as f:
        Crafting = json.load(f)
    '''
    # List of items that can be in your inventory:
    print('All items:',Crafting['Items'])

    # List of items in your initial inventory with amounts:
    print('Initial inventory:',Crafting['Initial'])

    # List of items needed to be in your inventory at the end of the plan:
    print('Goal:',Crafting['Goal'])

    # Dict of crafting recipes (each is a dict):
    print('Example recipe:','craft stone_pickaxe at bench ->',Crafting['Recipes']['craft stone_pickaxe at bench'])
    '''
    # Build rules
    all_recipes = []
    all_ingredients = []
    for name, rule in Crafting['Recipes'].items():
        checker = make_checker(rule)
        effector = make_effector(rule)
        heuristic =  make_heuristic(Crafting['Goal'])
        back_heuristic =  make_heuristic(Crafting['Initial'])
        back_checker = make_back_checker(rule)
        deffector = make_deffector(rule)
        recipe = Recipe(name, checker, effector, rule['Time'], heuristic)
        ingredient = None
        for product, quantity in rule["Produces"].items():
            ingredient = Ingredient(name, back_checker, deffector, \
                               rule['Time'], back_heuristic)
        all_recipes.append(recipe)
        all_ingredients.append(ingredient)
        


    # Create a function which checks for the goal
    is_goal = make_goal_checker(Crafting['Goal'])
    is_start = make_start_checker(Crafting['Initial'])

    # Initialize first state from initial inventory
    state = State({key: 0 for key in Crafting['Items']})
    state.update(Crafting['Initial'])
    
    goal = State({key: 0 for key in Crafting['Items']})
    goal.update(Crafting['Goal'])

    #make_start_checker test
    '''print(Crafting['Initial'])
    print(goal)
    print(is_start(goal))'''

    
    
    #make_deffector test
    '''print("start: " + str(state))
    for ingredient in all_ingredients:
        if ingredient.back_check(state):
            print(ingredient.name)
            state = ingredient.deffect(state)
            print(state)'''

    # Search - This is you!
    results = backsearch(reverse_graph, goal, is_start, 30)
    #results = search(graph, state, is_goal, 30)
    if (results != None):
        action_list = results[0]
        real_time_taken = results[1]
        if action_list != None:
            for action in action_list:
                print(action)
        for recipe in action_list:
            total_cost += Crafting['Recipes'][recipe]['Time']
        print("In game cost: " + str(total_cost))
        print("Computation time: " + str(real_time_taken) + " seconds")
