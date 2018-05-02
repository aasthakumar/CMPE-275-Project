import math
import mmh3
from bitarray import bitarray
 
class BloomFilter(object):
 
    '''
    Class for Bloom filter, using murmur3 hash function
    '''
 
    def __init__(self, items_count,fp_prob):
        # False posible probability in decimal
        self.fp_prob = fp_prob
 
        # Size of bit array to use
        self.size = self.get_size(items_count,fp_prob)
 
        # number of hash functions to use
        self.hash_count = self.get_hash_count(self.size,items_count)
 
        # Bit array of given size
        self.bit_array = bitarray(self.size)
 
        # initialize all bits as 0
        self.bit_array.setall(0)
 
    def add(self, item):
        digests = []
        for i in range(self.hash_count):
 
            # create digest for given item.
            # i work as seed to mmh3.hash() function
            # With different seed, digest created is different
            digest = mmh3.hash(item,i) % self.size
            digests.append(digest)
 
            # set the bit True in bit_array
            self.bit_array[digest] = True
 
    def check(self, item):
        '''
        Check for existence of an item in filter
        '''
        for i in range(self.hash_count):
            digest = mmh3.hash(item,i) % self.size
            if self.bit_array[digest] == False:
 
                # if any of bit is False then,its not present
                # in filter
                # else there is probability that it exist
                return False
        return True
 
    @classmethod
    def get_size(self,n,p):
        m = -(n * math.log(p))/(math.log(2)**2)
        return int(m)
 
    @classmethod
    def get_hash_count(self, m, n):
        k = (m/n) * math.log(2)
        return int(k)
    
