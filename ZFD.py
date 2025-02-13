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

import itertools as iter


def polymul(A, B):
    """
    # Simple Python3 program to multiply two polynomials

    # A[] represents coefficients of first polynomial
    # B[] represents coefficients of second polynomial
    # m and n are sizes of A[] and B[] respectively
    """
    m=len(A)
    n=len(B)
    prod = [0] * (m + n - 1)
    # Multiply two polynomials term by term
    # Take ever term of first polynomial
    for i in range(m):
        # Multiply the current term of first
        # polynomial with every term of
        # second polynomial.
        for j in range(n):
            prod[i + j] += A[i] * B[j]
    return prod


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
        self.binary_length = self.q * self.n
        self.words_number = q**k
        if (n-self.d)==0:
             self.max_precision=999
        else:
            self.max_precision=int((n-1)/(n-self.d))

    def find_creator(self,q):
        # for each number from 1 to q-1
        for i in range(1,q):
            # check if i power all number reach to all the numbers in the field
            check_arr=[0]*(q)
            for j in range(1,q):
                num=pow(i,j)%q
                check_arr[num]=1
            # if all the check_arr is 1, we found it!
            print(check_arr)
            if sum(check_arr)==q-1:
                return i
        print("cant find creator, {} is not a prime power".format(q))
        raise 



    def get_creator_poly(self,q,d,a):
        #create array with small polynomials (x-a),(x-a^2),..,(x-a^(d-1))
        small_p=[]
        for i in range(1,d):
            small_p.append([1,-(a^i)])
        if len(small_p) > 0:
            sum=small_p[0]  
        else:
            sum=[1]

        #multiply them by one another
        for i in range(1,d-1):
            sum=polymul(sum,small_p[i])
        
        #return the multipication
        return sum        

    def generate_code(self,q,n,g,d):
        """
        create c(x) = m(x) * g(x);    deg(c(x))= n
        g(x) is the creatore polynom. deg(g(x))=d-1
        m(x) are all the posible messages in the left degree. deg(m)=n-(d-1)
        """
        # start_time = time.process_time()
        # first, create m array:
        # each m is an array of deg(m), with all posibilities
        m_list=iter.product(range(q),repeat=n-d+1)
        # for each m, find his c(x) and add to the word list
        for m in m_list:
            c=polymul(list(m),g)
            word=list(map(lambda i:i%q,c))
            # pad with zeros to right size
            word=word+[0]* (n-len(word))
            self.word_list.append(word)
        # print("done. working time: ",time.process_time() - start_time)

    
    
    def uniqe_binary_words(self):
        """
        convert the wordlist to a uniqe binary pattern with weight 1
        [2,1,0,2]_3 -> [100,010,001,100]-> [1,0,0,0,1,0,0,0,1,1,0,0]
        """
        for word in self.word_list:
            #create new arr
            b_word=[[0]*self.q for _ in range(self.n)]
            for i,num in enumerate(word):
                #some nums are 0.0 which is float which is bad
                b_word[i][int(num)]=1
            one_list=[item for sublist in b_word for item in sublist]                                                       
            self.binary_word_list.append(one_list)

            

# q C[nq, kq, dq]q n       N         m
#11 [10, 5,  6]11 110 11^5 = 161,051 m=2
#23 [22, 4, 19]23 506 23^4 = 279,841 m=7
#23 [21, 3, 19]23 483 23^3 = 12,167 m=10

# zfd1=zfd(22,4,23)
# zfd2=zfd(21,3,23)
# zfd3=zfd(10,5,6)

# print(zfd1.word_list[160000])
# print(zfd1.binary_word_list[160000])


# print("done. working time: ",time.process_time() - start_time)