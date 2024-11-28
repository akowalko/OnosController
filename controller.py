import igraph as ig
import copy
import json
import requests

con ={
    'h1': {'switch': 'of:0000000000000001', 'port': "1", 'host_ip': '10.0.0.1/32'},
    'h2': {'switch': 'of:0000000000000002', 'port': "1", 'host_ip': '10.0.0.2/32'},
    'h3': {'switch': 'of:0000000000000003', 'port': "1", 'host_ip': '10.0.0.3/32'},
    'h4': {'switch': 'of:0000000000000004', 'port': "1", 'host_ip': '10.0.0.4/32'},
    'h5': {'switch': 'of:0000000000000005', 'port': "1", 'host_ip': '10.0.0.5/32'},
    'h6': {'switch': 'of:0000000000000006', 'port': "1", 'host_ip': '10.0.0.6/32'},
    'h7': {'switch': 'of:0000000000000007', 'port': "1", 'host_ip': '10.0.0.7/32'},
    'h8': {'switch': 'of:0000000000000008', 'port': "1", 'host_ip': '10.0.0.8/32'},
    'h9': {'switch': 'of:0000000000000009', 'port': "1", 'host_ip': '10.0.0.9/32'},
    'h10': {'switch': 'of:000000000000000a', 'port': "1", 'host_ip': '10.0.0.10/32'}
}

def znajdz_polaczenia(src, dst):
    if src == 0:
        src = 'a'
    if dst == 0:
        dst = 'a'
    src_device_id = "of:000000000000000" + str(src)
    dst_device_id = "of:000000000000000" + str(dst)
    headers = {
        'Accept': 'application/json',
    }
    response = requests.get('http://172.20.10.2:8181/onos/v1/links', headers=headers, auth=('karaf', 'karaf'))
    links = response.json()['links']
    for link in links:
        if link['src']['device'] == src_device_id and link['dst']['device'] == dst_device_id:
            sd_port = link['src']['port']
            dd_port = link['dst']['port']
            return [(src_device_id, int(sd_port)), (dst_device_id, int(dd_port))]


flows = {'flows': []}

user_src = input('Wyjście: ')
user_dst = input('Wejście: ')
strumien = int(input('Wielkość strumienia danych [Mb/s]: '))

src_switch = con[user_src]['switch']
src_switch_nr = src_switch[-1::]
if src_switch_nr == 'a':
    src_switch_nr = 0
src_switch_nr = int(src_switch_nr)
src_port = con[user_src]['port']
src_host = con[user_src]['host_ip']

dst_switch = con[user_dst]['switch']
dst_switch_nr = dst_switch[-1::]
if dst_switch_nr == 'a':
    dst_switch_nr = 0
dst_switch_nr = int(dst_switch_nr)
dst_port = con[user_dst]['port']
dst_host = con[user_dst]['host_ip']

# finding the shortest path
graph_links = [(1, 2), (1, 3), (1, 4), (1, 5), (3, 7), (3, 8), (0, 3), (4, 9),
                   (8, 9), (2, 8), (2, 6), (6, 7), (1, 7), (1, 8)]

g = ig.Graph(
        10,
        graph_links
    )

g.es["weight"] = [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
results = g.get_shortest_paths(src_switch_nr, to=dst_switch_nr, weights=g.es["weight"],
                                   output="epath")
if len(results[0]) > 0:

    # Add up the weights across all edges on the shortest path
    distance = 0
    for e in results[0]:
        distance += g.es[e]["weight"]
        g.es[e]["weight"] += ((4 * strumien) / 10)
    # print(g.es["weight"])
    print("Shortest weighted distance is: ", distance)
else:
    print("End node could not be reached!")
with open('sample.json') as file:
        sample = json.load(file)
# flows between switches and hosts

flow = copy.deepcopy(sample)
flow['deviceId'] = src_switch
flow['treatment']['instructions'][0]['port'] = src_port
flow['selector']['criteria'][0]['ip'] = src_host
flows['flows'].append(flow)

flow = copy.deepcopy(sample)
flow['deviceId'] = dst_switch
flow['treatment']['instructions'][0]['port'] = dst_port
flow['selector']['criteria'][0]['ip'] = dst_host
flows['flows'].append(flow)
#print(flows)
route = [graph_links[result] for result in results[0]]
print(f"Shortest path is: {route}")
# print(route)

# setting the switches in correct order
for connection in route:
    if route.index(connection) != 0:
         if connection[0] != route[route.index(connection) - 1][1]:
            new_connection = (connection[1], connection[0])
            route[route.index(connection)] = new_connection
    elif src_switch_nr != connection[0]:
        new_connection = (connection[1], connection[0])
        route[route.index(connection)] = new_connection
#print(route)

# creating flows between switches
for connection in route:
    src_dst = connection
    link1 = znajdz_polaczenia(src_dst[0], src_dst[1])
    #print(link1)

    flow = copy.deepcopy(sample)
    flow['deviceId'] = link1[0][0]
    flow['treatment']['instructions'][0]['port'] = link1[0][1]
    flow['selector']['criteria'][0]['ip'] = dst_host
    flows['flows'].append(flow)

    flow = copy.deepcopy(sample)
    flow['deviceId'] = link1[1][0]
    flow['treatment']['instructions'][0]['port'] = link1[1][1]
    flow['selector']['criteria'][0]['ip'] = src_host
    flows['flows'].append(flow)
#print(flows)

flows_json = json.dumps(flows)

with open("flows.json", "w") as file:
        file.write(flows_json)



headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }

fil = open('flows.json', 'r')
flows = json.load(fil)
print (json.dumps(flows))
response = requests.post('http://172.20.10.2:8181/onos/v1/flows', headers=headers, data=json.dumps(flows),
                             auth=('karaf', 'karaf'))
print(response)

