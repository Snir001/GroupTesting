"""
create zero false drop:
code is defined by :
    [n,k,d]q when n<q and d=n-k+1
the number of words is N=q^k (each word is where person should put his test)
number of tubes is T=n*q 
 this code can detect maximum of m pepole without false drop, when m is:
    m = lower_value((n-1)/(n-d))
"""
import numpy as np


class zfd:

    word_list=[]

    def __init__(self,n,k,q):
        self.n=n
        self.k=k
        self.q=q
        self.generate_zfd()


    def check_mod0(self,word,digit_index):
        if digit_index==(len(word)-1):
            for i in range(self.q):
                word[digit_index]=i
                if sum(word)%self.q==0:
                    self.word_list.append(word.copy())
            return
        for i in range(self.q):
            if digit_index==0:
                print("word: ",word)
            word[digit_index]=i
            self.check_mod0(word,digit_index+1)
            


    def generate_zfd(self):
        """
        this method will return list of vectors of this code
        """
        #generate codes:
        #make a list with size n:
        word=[0]*self.n
        self.check_mod0(word,0)
        return self.word_list
    
zzz=zfd(10,5,11)
print(len(zzz.word_list))