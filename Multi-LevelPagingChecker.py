import os.path

# check whether valid input given
def get_filename():
    while True:
        filename = input("Please enter the filename containing the memory dump: ")
        if not os.path.isfile(filename):
            print ("Sorry, can't find the file you specified.")
            continue
        else:
            break
    return filename

def get_vaddr():
    while True:
        try:
            vaddr = hex(int((input("Please enter the virtual address: ")), 16))
        except ValueError: # if string or other invalid form
            print("Virtual address isn't valid.")
            continue #keep trying until valid input
        except TypeError:
            print("Virtual address isn't valid.")
            continue 
        else:
            # successfully parsed user's input
            break
    return vaddr


# class for storing information about the pages
class MemoryDump():

    def __init__(self):
        self.frames = []
        self.pdbr = None
        self.boffset = None
        self.vaddrs = dict()

    def find_paddr(self, vaddr=0x40dd):
        vaddr = (bin(int(vaddr, 16))[2:]).zfill(15)
        print ("Converted virtual address to binary:", vaddr, "\n")
        
        bpage, bframe, boffset = (vaddr[i:i+5] for i in range(0, len(vaddr), 5))
        page, frame, offset = (int(i, 2) for i in (bpage, bframe, boffset))

        print("Page is", bpage, "in binary and", page, "in decimal")
        print("Frame is", bframe, "in binary and", frame, "in decimal")
        print("Offset is", boffset, "in binary and", offset, "in decimal\n")
        print("Checking PDBR frame", self.pdbr, "[" + str(page) + "]")

        # find |VALID|PFN6 ... PFN0|
        value1 = self.frames[self.pdbr][page]
        # convert it to binary and check the first bit for if valid
        first = bin(int(value1, 16))[2:]
        if first[0] == '0':
            return None, None
        # if it's valid, we use the remaining 7 bits to find the next frame
        first = int(first[1:], 2)
        print("Checking frame", first, "[" + str(frame) + "]")

        # find |VALID|PT6 ... PT0|
        value2 = self.frames[first][frame]
        second = bin(int(value2, 16))[2:]
        # check if valid
        if second[0] == '0':
            return None, None

        # create physical address: 7 bits PFN + 5 bits offset
        paddr = hex(int((second[1:] + boffset), 2))
        
        second = int(second[1:], 2)
        print("Checking frame", second, "[" + str(offset) + "] to find the value it's pointing to.\n")

        # last step: find value it's pointing to
        value = self.frames[second][offset]     
        
        return paddr, value

def create_dump(filename):
    # open file and read contents
    file = open(filename, 'r')
    memdump = MemoryDump()

    for line in file:
        line = line.strip()
        # save frames

        startsw = (line[:line.find(":")].lower()).split(' ')[0]
        data = (line[line.find(':')+1:].strip()).split(' ')
        
        if startsw == "frame":
            # if it starts with frame, save the frame
            memdump.frames.append(data)
        elif startsw == "pdbr":
            # if pdbr, store value for future reference
            memdump.pdbr = int(data[0])

    file.close()

    # error checks
    if not memdump.frames:
        print ("Something went wrong with finding the frames.")
        raise ValueError
    if not memdump.pdbr:
        print ("Please put the PDBR in the file.")
        raise ValueError

    memdump.boffset = len(memdump.frames[0])

    if not memdump.boffset or memdump.boffset < 0:
        print ("Bad byte offset.")
        raise ValueError

    return memdump
    

if __name__ == "__main__":
    filename = get_filename()
    memdump = create_dump(filename)

    print ("The byte offset is:", memdump.boffset)
    print ("The PDBR location is:", memdump.pdbr)
    print ("The # of frames is:", len(memdump.frames))

    while True:
        vaddr = get_vaddr()
        # get the physical address and value it's pointing to if exists otherwise calculate it
        memdump.vaddrs[vaddr] = memdump.vaddrs.get(vaddr, memdump.find_paddr(vaddr))
        paddr, value = memdump.vaddrs[vaddr]

        print (memdump.vaddrs)
        
        if not paddr and not value:
            print ("The virtual address is not valid!\n")
        else:
            print ("The physical address is", hex(int(paddr, 16)), "and the value it's pointing to is", hex(int(value, 16)), "\n")
