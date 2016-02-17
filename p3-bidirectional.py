# Colin Peter cypeter@ucsc.edu
# Eliezer Miron emiron@ucsc.edu

from heapq import heappop, heappush
from math import sqrt

def pythagoras(p1, p2):
    x1, y1 = p1
    x2, y2 = p2
    return sqrt((x1-x2)**2 + (y1-y2)**2)

def dijkstra_with_point(initial_position, destination, graph, adj, starting_point, ending_point):
    """ Searches for a minimal cost path through a graph using Dijkstra's algorithm.

    Args:
        initial_position: The initial cell from which the path extends.
        destination: The end location for the path.
        graph: A loaded level, containing walls, spaces, and waypoints.
        adj: An adjacency function returning cells adjacent to a given cell as well as their respective edge costs.
        starting_point: the starting point (x, y)

    Returns:
        If a path exits, return a list containing all cells from initial_position to destination.
        Otherwise, return None.

    """

    distances_f = {initial_position: 0}           # Table of distances to cells 
    distances_r = {destination: 0}
    previous_cell_f = {initial_position: None}    # Back links from cells to predecessors
    previous_cell_r = {destination: None}
    previous_point_f = {initial_position: starting_point}
    previous_point_r = {destination: ending_point}
    queue = [(0, initial_position, 'dst'), (0, destination, 'src')]             # The heap/priority queue used

    # Initial distance for starting position
    distances_f[initial_position] = 0
    distances_r[destination] = 0

    while queue:
        # Continue with next min unvisited node
        current_priority, current_node, current_dest = heappop(queue)
        
        # Early termination check: if the destination is found, return the path
        if (current_dest == 'dst' and current_node in previous_cell_r) or (current_dest == 'src' and current_node in previous_cell_f):
                node = current_node
                path = []
                point_path = []
                while node is not None:
                    path.append(node)
                    point_path.append(previous_point_f[node])
                    node = previous_cell_f[node]
                path = path[::-1]
                point_path = point_path[::-1]
                node = current_node
                while node is not None:
                    path.append(node)
                    point_path.append(previous_point_r[node])
                    node = previous_cell_r[node]
                return (path, point_path)
                
                    
        """
        if current_node == destination:
            node = destination
            path = []
            point_path = []
            while node is not None:
                path.append(node)
                point_path.append(previous_point[node])
                node = previous_cell[node]
            return (path[::-1], point_path[::-1])
        """

        distances = distances_f if current_dest == 'dst' else distances_r
        previous_point = previous_point_f if current_dest == 'dst' else previous_point_r
        
        current_distance = distances[current_node]
        
        # Calculate tentative distances to adjacent cells
        for adjacent_node, edge_cost, new_point in adj(graph, current_node, previous_point[current_node]):
            new_distance = current_distance + edge_cost

            if adjacent_node not in distances or new_distance < distances[adjacent_node]:
                # Assign new distance and update link to previous cell
                heuristic = 0
                if current_dest == 'dst':
                    distances_f[adjacent_node] = new_distance
                    previous_cell_f[adjacent_node] = current_node
                    previous_point_f[adjacent_node] = new_point
                    heuristic = pythagoras(new_point, ending_point)
                else:
                    distances_r[adjacent_node] = new_distance
                    previous_cell_r[adjacent_node] = current_node
                    previous_point_r[adjacent_node] = new_point
                    heuristic = pythagoras(new_point, starting_point)
                
                heappush(queue, (new_distance+heuristic, adjacent_node, current_dest))
                    
    # Failed to find a path
    print("Failed to find a path from", initial_position, "to", destination)
    return (None, None)


def in_box(point, box):
    x, y = point
    x1, x2, y1, y2 = box
    return x >= x1 and x <= x2 and y >= y1 and y <= y2

def detail_points(box1, box2):
    if box1[1] == box2[0]:
        x_val = box1[1]
        y_vals = sorted([box1[2], box1[3], box2[2], box2[3]])[1:3]
        return [(x_val, y_vals[0]), (x_val, y_vals[1])]
    if box1[0] == box2[1]:
        x_val = box1[0]
        y_vals = sorted([box1[2], box1[3], box2[2], box2[3]])[1:3]
        return [(x_val, y_vals[0]), (x_val, y_vals[1])]
    if box1[2] == box2[3]:
        y_val = box1[2]
        x_vals = sorted([box1[0], box1[1], box2[0], box2[1]])[1:3]
        return [(x_vals[0], y_val), (x_vals[1], y_val)]
    if box1[3] == box2[2]:
        y_val = box1[3]
        x_vals = sorted([box1[0], box1[1], box2[0], box2[1]])[1:3]
        return [(x_vals[0], y_val), (x_vals[1], y_val)]
    print("Boxes are not adjacent!")
    return None

def points_vertical(p1, p2):
    if p1[1] == p2[1]:
        return 0
    if p1[0] == p2[0]:
        return 1
    print("Points are not aligned")
    return None

def get_next_point(point, box1, box2):
    detail1, detail2 = detail_points(box1, box2)
    if points_vertical(detail1, detail2):
        if point[1] < detail1[1]:
            return detail1
        elif point[1] > detail2[1]:
            return detail2
        else:
            return (detail1[0], point[1])
    else:
        if point[0] < detail1[0]:
            return detail1
        elif point[0] > detail2[0]:
            return detail2
        else:
            return (point[0], detail1[1])


def adjacent_cells(mesh, box, point):
    def costify(b):
        next_point = get_next_point(point, box, b)
        cost = pythagoras(point, next_point)
        return (b, cost, next_point)
    return map(costify, mesh['adj'][box])
        
def find_path(source_point, destination_point, mesh):
    mesh_boxes = mesh['boxes']
    #mesh_edges = mesh['adj']
    
    start_box = None
    end_box = None
    #print(source_point)
    for box in mesh_boxes:
        if in_box(source_point, box):
            start_box = box
        if in_box(destination_point, box):
            end_box = box

    if start_box == None or end_box == None:
        print("No path!")
        return ([], [])

    """
    boxes_to_consider = queue.Queue()
    boxes_to_consider.put(start_box)
    previous_box = {}
    considered = set()

    found_path = 0
    
    while not boxes_to_consider.empty():
        current = boxes_to_consider.get()
        #print(current, current in considered)
        
        if current in considered:
            continue
        
        considered.add(current)
        if current == end_box:
            found_path = 1
            break

        new_boxes = mesh_edges[current]
        for box in new_boxes:
            if not box in considered:
                previous_box[box] = current
                boxes_to_consider.put(box)
    """ 

    box_path, point_path = dijkstra_with_point(start_box, end_box, mesh, adjacent_cells, source_point, destination_point)
    
    if not box_path:
        print("No path!")
        return ([], [])

    """
    current_point = source_point
    for i in range(0, len(box_path) - 1):
        current_box = box_path[i]
        next_box = box_path[i+1]
        next_point = get_next_point(current_point, current_box, next_box)
        print(current_point, detail_points(current_box, next_box))
        current_point = next_point
    """
    """
    box_path = []
    current = end_box
    while current in previous_box:
        box_path.append(current)
        current = previous_box[current]
    box_path.append(start_box)
    box_path.reverse()

    segment_path = []
    current_point = source_point

    for i in range(0, len(box_path) - 1):
        current_box = box_path[i]
        next_box = box_path[i+1]
        next_point = get_next_point(current_point, current_box, next_box)
        
        #print(next_point)
        segment_path.append((current_point, next_point))
        current_point = next_point
    segment_path.append((current_point, destination_point))
    """

    segment_path = []
    point_path.append(destination_point)
    for i in range(0, len(point_path)-1):
        segment_path.append((point_path[i], point_path[i+1]))
    
    return (segment_path, box_path)

