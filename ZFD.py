"""
create zero false drop:
code is defined by :
    [n,k,d]q when n<q and d=n-k+1
the number of words is N=q^k (each word is where person should put his test)
number of tubes is T=n*q 
 this code can detect maximum of m pepole without false drop, when m is:
    m = lower_value((n-1)/(n-d))
"""
import time
start_time = time.process_time()

import numpy as np
import itertools as iter

class zfd:

    word_list=[]
    binary_word_list=[]

    def __init__(self,n,k,q):
        self.n=n
        self.k=k
        self.q=q
        self.d=n-k+1
        self.a=self.find_creator(self.q)
        self.g=self.get_creator_poly(self.q,self.d,self.a)
        self.generate_code(q,n,self.g,self.d)
        self.uniqe_binary_words()

    def find_creator(self,q):
        # for each number from 1 to q
        for i in range(1,q+1):
            # check if i power all number reach to all the numbers in the field
            check_arr=np.zeros(q)
            for j in range(1,q+1):
                num=pow(i,j)%q
                check_arr[num]=1
            # if all the check_arr is 1, we found it!
            if sum(check_arr)==q:
                return i
        return -1



    def get_creator_poly(self,q,d,a):
        #create array with small polynomials (x-a),(x-a^2),..,(x-a^(d-1))
        small_p=[]
        for i in range(1,d):
            small_p.append([1,-(a^i)])
        sum=small_p[0]

        #multiply them by one another
        for i in range(1,d-1):
            sum=np.polymul(sum,small_p[i])
        
        #return the multipication
        return sum




        

    def generate_code(self,q,n,g,d):
        """
         create c(x) = m(x) * g(x). deg(c(x))= n
         g(x) is the creatore polynom. deg(g(x))=d-1
         m(x) are all the posible messages in the left degree. deg(m)=n-(d-1)
        """
        
        # first, create m array:
        # each m is an array of deg(m), with all posibilities
        m_list=iter.product(range(q),repeat=n-d+1)
        # for each m, find his c(x) and add to the word list
        for m in m_list:
            c=np.polymul(list(m),g)
            word=list(map(lambda i:i%q,c))
            word=np.pad(word,(0, n-len(word)))
            self.word_list.append(word)

    
    
    def uniqe_binary_words(self):
        """
        convert the wordlist to a uniqe binary pattern with weight 1
        [2,1,0,2]_3 -> [100,010,001,100]-> [1,0,0,0,1,0,0,0,1,1,0,0]
        """
        # template=[np.zeros(self.q) for _ in range(self.n)]
        for word in self.word_list:
            #create new arr
            b_word=[np.zeros(self.q) for _ in range(self.n)]
            for i,num in enumerate(word):
                #some nums are 0.0 which is float which is bad
                b_word[i][int(num)]=1                                                      
            self.binary_word_list.append(b_word)
        

        

        
            

      


zfd1=zfd(22,4,23)
print(zfd1.word_list[160000])
print(zfd1.binary_word_list[160000])

print("done. working time: ",time.process_time() - start_time)
