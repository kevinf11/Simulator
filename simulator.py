import contextlib
from itertools import zip_longest, cycle, islice, chain
import sys


# Round Robin function
def roundrobin(*iterables):
    num_active = len(iterables)
    nexts = cycle(iter(it).__next__ for it in iterables)
    while num_active:
        try:
            for next in nexts:
                yield next()
        except StopIteration:
            num_active -= 1
            nexts = cycle(islice(nexts, num_active))

# Collect data into fixed-length blocks
def grouper(iterable, n, fillvalue=None):
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


def debug_fuc(count_references, ind, pag):
    if pag == 0:
        print(count_references, ind, 0, 0, 0, flush=True)
    else:
        print(count_references, ind, pag.pn, pag.pagenum, pag.dirty,flush=True)


# Create the process table
class PTP:
    def __init__(self):
        self.table_clock = []

    def add (self,page):
        self.table_clock.append(page)

    def add_NRU(self, page_to_change):
        global hit
        for ind, pag in enumerate(self.table_clock):
            if pag.referenced == 0 and pag.dirty == 0:
                if debug:
                    debug_fuc(count_references, ind, pag)
                self.table_clock[ind] = page_to_change
                return
        for ind, pag in enumerate(self.table_clock):
            if pag.referenced == 0 and pag.dirty == 1:
                hit += 1
                if debug:
                    debug_fuc(count_references, ind, pag)
                self.table_clock[ind] = page_to_change
                return
        for ind, pag in enumerate(self.table_clock):
            if pag.referenced == 1 and pag.dirty == 0:
                if debug:
                    debug_fuc(count_references, ind, pag)
                self.table_clock[ind] = page_to_change
                return
        for ind, pag in enumerate(self.table_clock):
            if pag.referenced == 1 and pag.dirty == 1:
                if debug:
                    debug_fuc(count_references, ind, pag)
                hit += 1
                self.table_clock[ind] = page_to_change
                return

    def add_LRU(self, page_to_change):
        global hit
        clock_list = [x.clock_num for x in self.table_clock]
        min_n = clock_list[0]
        ind = 0
        for i in range(len(clock_list)):
            if clock_list[i] < min_n:
                min_n = clock_list[i]
                ind = i
        if self.table_clock[ind].dirty == 1:
            hit += 1
        if debug:
            debug_fuc(count_references, ind, self.table_clock[ind])
        self.table_clock[ind] = page_to_change
        return


# Def page class
class Page:
    def __init__(self, pn, pagenum, mode,clock_num):
        self.pn = pn
        self.pagenum = pagenum
        if mode == "W":
            self.dirty= 1
        else:
            self.dirty = 0
        self.referenced = 1
        self.clock_num = clock_num


# Create table and perform NRU or LRU
def perform_version(pn, addr, mode, version, clock_num, p_size, m_size):
    global faults, hit, debug, count_references
    addr = (addr//p_size)
    if addr in [x.pagenum for x in page_table.table_clock if x.pn == pn]:
        for ind, pag in enumerate(page_table.table_clock):
            if pag.pn == pn and pag.pagenum == addr:
                currpage = page_table.table_clock[ind]
        currpage.referenced = 1
        currpage.clock_num = clock_num
        if mode == 'W':
            currpage.dirty = 1

    else:
        newpage = Page(pn, addr, mode, clock_num)
        if len(page_table.table_clock) < m_size:
            if debug == 1:
                debug_fuc(count_references, len(page_table.table_clock), 0)
            faults += 1
            hit += 1
            page_table.add(newpage)
        else:
            if version == 1:
                faults += 1
                hit += 1
                page_table.add_NRU(newpage)
            elif version == 2:
                faults += 1
                hit += 1
                page_table.add_LRU(newpage)


# Variables
hit = 0
clock_num = 0
page_table = PTP()
debug = 0
count_references = 0 
faults = 0
arguments = sys.argv[1:]
file_name = arguments[0]
version = int(arguments[1])
count_pars = 0
p_size = 0
m_size = 0
quantum = 0
n_proc = 0
process = []
parameters = open(file_name, 'r')
fline = 0 


# Reading Parameters from file 
for line in parameters:
    line = line.split("%")
    if count_pars == 0:
        p_size = int(line[0])
    elif count_pars == 1:
        m_size = int(line[0])
    elif count_pars == 2:
        quantum = int(line[0])
    elif count_pars == 3:
        n_proc = int(line[0])
    else:
        data_file = str(line[0])
        data_file.rstrip
        process.append(data_file)
    count_pars += 1


# Removing Blank spaces from file names in list 
for i in range(len(process)):
    process[i] = process[i].rstrip()


# Printing information
print("Reading parameters...")
print("Page Size: " , p_size)
print("Memory Size: ", m_size)
print("Quantum: ", quantum)
print("N Process: ",n_proc)
print("Reading data files...")
for data in process:
    print("Data Files: ", data)


# File name to write after round robin process
result_file = "result_file.txt"


# Main process for round robin process 
with contextlib.ExitStack() as stack:
    # Open each file *once*; the exit stack will make sure they get closed
    files = [stack.enter_context(open(fname)) for fname in process]
    # Iterate over them in n instructions batches.
    groups = [grouper(f, quantum) for f in files]
    # Interleave the groups by taking an n instructions group from one file,
    # then another, etc.
    interleaved = roundrobin(*groups)
    # Then flatten them into a stream of single lines
    flattened = chain.from_iterable(interleaved)
    # Filter out the None padding added by grouper() and
    # read the instructions into a list
    rr_list = list(filter(lambda x: x is not None, flattened))

# Writes rr_list into a result file
with open(result_file, 'w') as f:
    for item in rr_list:
        f.write("%s" % item)

# Handling command line arguments				
if len(arguments) > 2:
    debug = 1


lines = open(result_file, 'r')

# Reading result file 
for line in lines:
    count_references += 1
    line = line.split()
    pn = int(line[0])
    addr = int(line[1])
    memory_reference = int(line[2])
    mode = line[3]

# NRU AND LRU for result file
    perform_version(pn, addr, "R", version, count_references, p_size, m_size)
    perform_version(pn, memory_reference, mode, version, count_references, 
    p_size, m_size)
    if version ==1 and count_references %200 == 0:
        for page in page_table.table_clock:
            page.referenced = 0

print("Instructions readed: ", len(rr_list))
print("Total page faults:", faults)
print("Total writes to disk:", hit-faults)
