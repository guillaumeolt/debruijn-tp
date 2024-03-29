import os
import argparse
import statistics
import random
import networkx as nx

def read_fastq(path_fastq):
    """
    read fastq file and output a list of the reads
    """
    with open(path_fastq, 'r') as filin:
        for ligne in filin:
            yield next(filin)[0:-1]
            next(filin)
            next(filin)

def cut_kmer(seq, k_mer):
    """
    take a sequence and a k-mer size and return an iterator of k-mer
    """
    for i in range(len(seq)-k_mer+1):
        yield seq[i:(i+k_mer)]

def build_kmer_dict(path_fastq, k_mer):
    """
    take a fastq file in argument and a k mer size and return a dictionary
    with the
    k-mer as keys and the number of occurences as values
    """
    dict_k_mer = {}
    for seq_read in read_fastq(path_fastq):
        for iterator_k_mer in cut_kmer(seq_read, k_mer):
            if iterator_k_mer in dict_k_mer:
                dict_k_mer[iterator_k_mer] +=1
            else:
                dict_k_mer[iterator_k_mer] = 1
    return(dict_k_mer)

def build_graph(dict_k_mer):
    """
    creat a networkx graph
    """
    graph = nx.DiGraph()
    for k_mer in dict_k_mer:
        graph.add_edge(k_mer[:-1], k_mer[1:], weight=dict_k_mer[k_mer])
    return(graph)

def get_starting_nodes(graph):
    start_nodes = []
    for k_mer in graph:
        if list(graph.predecessors(k_mer)) == []:
            start_nodes.append(k_mer)
    return start_nodes

def std(list_value):
    """
    compute the standard deviation
    """
    return statistics.stdev(list_value)


def get_sink_nodes(graph):
    """
    return a list of output nodes
    """
    end_nodes = []
    for k_mer in graph:
        if list(graph.successors(k_mer)) == []:
            end_nodes.append(k_mer)
    return end_nodes


def path_average_weight(graph, chemin):
    """
    returna n average weight of the path
    """
    tot_weight = []
    list_chemin = list(chemin)

    for i in range(0, len(list_chemin)-1):
        node_1 = list_chemin[i]
        node_2 = list_chemin[i+1]
        tot_weight.append(graph[node_1][node_2]["weight"])
    return sum(tot_weight)/len(tot_weight)


def remove_paths(graph, list_chemin, delete_entry_node, delete_sink_node):
    """
    remove a path in a graph
    """
    list_path_clean = []     
    for chemin in list_chemin:
        for i in range(1, len(chemin)-1):
            graph.remove_node(chemin[i])
        if delete_entry_node == True:
            graph.remove_node(chemin[0])
        if delete_sink_node == True:   
            graph.remove_node(chemin[-1])   
             
    return graph


def select_best_path(graph, list_chemin, list_size, list_weight,\
 delete_entry_node=False, delete_sink_node=False):
    """
    select best path in a set of path in a graph
    """
    max_weight = []
    index_weight = []
    i = 0
    for weight in list_weight:
        if max_weight == []:
            max_weight.append(weight)
            index_weight.append(i)
        else:

            if weight > max_weight[0]:
                max_weight = []
                index_weight = [] 
                max_weight.append(weight)
                index_weight.append(i)
            elif weight == max_weight[0]:
                max_weight.append(weight)
                index_weight.append(i)
        i +=1
    best_chemin = list_chemin[index_weight[0]]

    max_size = []
    index_size = [] 

    if len(max_weight) > 1:

        for index in index_weight:
            if max_size == []:
                max_size.append(list_size[index])
            else:
                if list_size[index] > max_size[0]:
                    max_size = []
                    index_size = [] 
                    max_size.append(list_size[index])
                    index_size.append(index)
                elif list_size[index] == max_size[0]:
                    max_size.append(list_size[index])
                    index_size.append(index)
        best_chemin = list_chemin[index_size[0]]
    if len(max_size) > 1:
        best_chemin = list_chemin[index_size[randint(0, len(max_size))]]

    for chemin in list_chemin:
        if chemin != best_chemin:
            remove_paths(graph, [chemin], delete_entry_node, delete_sink_node)
    return graph

def fill(text, width=80):
    """Split text with a line return to respect fasta format"""
    return os.linesep.join(text[i:i+width] for i in range(0, len(text), width))
    
def save_contigs(contigs, path_output):
    """
    write contigs
    """
    file_output = open(path_output, "w")
    n_contig = 0
    for contig in contigs:
        file_output.write(">contig_"+str(n_contig)+" len="+str(contig[1])+"\n")
        file_output.write(fill(contig[0]))
        file_output.write("\n")
        n_contig += 1
    file_output.close()
    pass


def get_contigs(G, start_nodes, end_nodes):
    """
    get contigs
    """
    contigs = []
    for start in start_nodes:
        for end in end_nodes:
            if list(nx.all_simple_paths(G, start, end)) != []:
                contig_seq = nx.shortest_path(G, start, end)
                contig = []
                for i in range(len(contig_seq)-1):
                    contig.append(contig_seq[i][0])
                    flag = i
                contig.append(contig_seq[flag+1])
                join_contig = ''.join(contig)
                size_contig = len(join_contig)
                contigs.append((join_contig, size_contig))
    return contigs


def solve_bubble(graph, node_ancestor, node_descendant):
    """
    clean a graph from a bubble
    """
    all_path = list(nx.all_simple_paths(graph, node_ancestor, node_descendant))
    if all_path == []:
        return graph
    list_size = []
    list_weight = []
    for i in range(len(all_path)):
        list_size.append(len(all_path[i]))
        list_weight.append(path_average_weight(graph, all_path[i]))
        
    graph = select_best_path(graph, all_path, list_size, list_weight,\
     delete_entry_node=False, delete_sink_node=False)
    return graph


def simplify_bubbles(graph):
    """
    remove all bubbles from a graph
    """
    for node_1 in graph.nodes:
        nodes_ancestor = list(graph.predecessors(node_1))
        if len(nodes_ancestor) > 1:
            for i in range(len(nodes_ancestor)-1):
                for j in range(i+1, len(nodes_ancestor)):
                    path = nx.lowest_common_ancestor(graph, nodes_ancestor[i],\
                     nodes_ancestor[j])

                    if path != nodes_ancestor[i] and path != nodes_ancestor[j]:
                        graph = solve_bubble(graph, path, node_1)
                        return graph
    return graph


def solve_entry_tips(graph, node_entry):
    """
    take off unwaned path in a graph (entry nodes)
    """
    main_path = []
    pointe = []
    flag = True
    while flag:
        flag = False
        main_path = []
        pointe = []
        for node_1 in graph.nodes:
            if main_path == []:
                main_path.append(node_1)
            elif len(main_path) == 1:
                main_path.append(node_1)
            if len(main_path) >= 2:
                nodes_predecessor = list(graph.predecessors(node_1))
                if len(nodes_predecessor) > 1:
                    pointe.append(node_1)
                    while nodes_predecessor != []:
                        for node_p in nodes_predecessor:
                            if node_p not in main_path:
                                pointe.append(node_p)
                                nodes_predecessor = \
                                list(graph.predecessors(node_p))

                    main_path_weight = path_average_weight(graph, main_path)
                    pointe_weight = path_average_weight(graph, pointe[::-1])
                    graph = select_best_path(graph, [main_path, pointe[::-1]],\
                                                [len(main_path), len(pointe)],\
                                            [main_path_weight, pointe_weight],\
                                            delete_entry_node=True)
                    Flag = True
                    break
    return graph


def solve_out_tips(graph, node_entry):
    """
    take off unwaned path in a graph (out nodes)
    """
    main_path = []
    pointe = []
    flag = True
    while flag:
        flag = False
        main_path = []
        pointe = []
        for node_1 in graph.nodes:
            nodes_successors = list(graph.successors(node_1))

            if len(nodes_successors) > 1:
                pointe.append(node_1)
                while nodes_successors != []:
                    for node_p in nodes_successors:
                        if node_p not in main_path:
                            pointe.append(node_p)
                            nodes_successors = list(graph.successors(node_p))

                main_path_weight = path_average_weight(graph, main_path)
                pointe_weight = path_average_weight(graph, pointe)
                graph = select_best_path(graph, [main_path, pointe],\
                 [len(main_path), len(pointe)],\
                 [main_path_weight, pointe_weight], \
                 delete_sink_node=True)
                Flag = True
                break
    return graph
    
def main():
    """
    main for launching debruijn
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("-i", nargs="?",\
        help="fichier fastq single end")
    parser.add_argument("-k", nargs="?",\
        help="taille des kmer (optionnel - default 21)",)
    parser.add_argument("-o", nargs="?",\
        help="fichier config")

    args = parser.parse_args()
    
    random.seed(9001)
    
    dict_k_mer = build_kmer_dict(args.i, int(args.k))
    graph = build_graph(dict_k_mer)
    sart_nodes = get_starting_nodes(graph)
    end_nodes = get_sink_nodes(graph)
    contigs = get_contigs(graph, sart_nodes, end_nodes)
    save_contigs(contigs, "test.txt")

if __name__ == "__main__":
    main()
