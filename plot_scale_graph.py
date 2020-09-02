import sys
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
#from networkx.drawing.nx_agraph import write_dot

def parse_file(filename):
    data = []

    with open(filename, "r") as f:
        datum = {}
        for line in f:
            if line.startswith("val:"): 
                datum = {"value": line[4:].strip()}
            if line.startswith("owf:"):
                datum["could_overflow"] = bool(int(line[4:].strip()))
            elif line.startswith("chi:") or line.startswith("par:"): 
                #remove leading "par:" and trailing "=+=" 
                #split by "=+="
                #filter out empty strings
                #strip whitespaces
                contents = filter(None, line[4:-4].split("=+="))
                #contents = line[4:-4].split("=+=")
                node_names = [x.strip() for x in contents]
                
                if line.startswith("chi:"):
                    datum["children"] = node_names
                elif line.startswith("par:"):
                    datum["parents"] = node_names
                    data.append(datum)

                print(line)
                print(contents)
                for c in node_names:
                    print(c)

    

    return data




all_data = []
for filename in sys.argv[1:]:
    all_data = all_data + parse_file(filename)

G = nx.DiGraph()
for d in all_data:
    G.add_node(d["value"])

for d in all_data:
    G.add_edges_from([(d["value"], x) for x in d["children"]])
    #G.add_edges_from([(x, d["value"]) for x in d["parents"]])

#for x in all_data:
#    print(x)
#print(G.nodes())
#print(G.edges())

#nx.draw(G, with_labels=True)

numerical_labels = {x:i for i,x in enumerate([y["value"] for y in all_data])}
color_map = []
for k,v in numerical_labels.items():
    print(v,k)
    print(next(x["children"] for x in all_data if x["value"] == k))
    if " = call" in k:
        color_map.append("purple")
    elif next(x for x in all_data if x["value"] == k)["could_overflow"] == True:
        color_map.append("red")
    else:
        color_map.append("cyan")

# good layouts: circular, kamada_kawai
nx.draw_circular(G, labels=numerical_labels, node_color=color_map, with_labels=True)
plt.show()


#A = nx.nx_agraph.to_agraph(G)
#write_dot(G, "graph.dot")
