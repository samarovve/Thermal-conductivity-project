import numpy as np
import sympy as sp
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import spsolve
class SuperCubeStatic:


    def __init__(self, size):
        self.size = size
        self.data_float=np.zeros(self.size**3, dtype=float).reshape(self.size, self.size, self.size)



        if size<7:
            symbols = []
            for x in range(size):
                for y in range(size):
                    for z in range(size):
                        symbols.append(sp.symbols(f't_{x}{y}{z}'))
            self.data_symbols = np.array(symbols).reshape(size, size, size)
            self.eqs = []
            self.unknowns = []
            self.params = []
            for x in range(self.size):
                for y in range(self.size):
                    for z in range(self.size):
                        if not (x == 0 or x == self.size - 1 or
                   y == 0 or y == self.size - 1 or
                   z == 0 or z == self.size - 1):
                            eq = 6 * self.data_symbols[x, y, z] - self.data_symbols[x - 1, y, z] - self.data_symbols[
                                x, y - 1, z] - self.data_symbols[x, y, z - 1] - self.data_symbols[x + 1, y, z] - \
                                 self.data_symbols[x, y + 1, z] - self.data_symbols[x, y, z + 1]
                            self.eqs.append(eq)
                            self.unknowns.append(self.data_symbols[x, y, z])
                        else:
                            self.params.append(self.data_symbols[x, y, z])
            self.solutions = list(sp.linsolve(self.eqs, self.unknowns))[0]
        if size>=7:
            size = self.size - 2
            data=[]
            rows=[0]
            columns=[]
            for x in range (1, self.size-1):
                for y in range(1, self.size-1):
                    for z in range(1, self.size-1):
                        members=0
                        if z>1:
                            data.append(-1)
                            members+=1
                            columns.append((z-2)*size*size+(y-1)*size+x-1)
                        if y>1:
                            data.append(-1)
                            members+=1
                            columns.append((z-1)*size*size+(y-2)*size+x-1)
                        if x>1:
                            data.append(-1)
                            members+=1
                            columns.append((z-1)*size*size+(y-1)*size+x-2)
                        data.append(6)
                        members+=1
                        columns.append((z-1)*size*size+(y-1)*size+x-1)
                        if x<self.size-2:
                            data.append(-1)
                            members+=1
                            columns.append((z-1)*size*size+(y-1)*size+x)
                        if y<self.size-2:
                            data.append(-1)
                            members+=1
                            columns.append((z-1)*size*size+(y)*size+x-1)
                        if z<self.size-2:
                            data.append(-1)
                            members+=1
                            columns.append((z)*size*size+(y-1)*size+x-1)
                        rows.append(rows[-1]+members)

            self.A=csr_matrix((data,columns,rows),shape=((self.size-2)**3,(self.size-2)**3))



    def get_size(self):
        return self.size


    def get_temp_from_number(self, x,y,z):
        try:
            return(self.data_float[x,y,z])
        except:
            raise AttributeError('incorrect index')


    def set_temp(self, x, y, z, temp_val):
        try:
            if (x == 0 or x == self.size - 1 or
               y == 0 or y == self.size - 1 or
               z == 0 or z == self.size - 1):
                self.data_float[x,y,z]=temp_val
            else:
                raise AttributeError('incorrect index')
        except:
            raise AttributeError('incorrect index')

    def solve_in_numbers(self):
         if self.size < 7:
            fast_solver = sp.lambdify(self.params, self.solutions, modules='numpy')
            params_float = []
            for x in range(self.size):
                for y in range(self.size):
                    for z in range(self.size):
                        if (x == 0 or x == self.size - 1 or
                   y == 0 or y == self.size - 1 or
                   z == 0 or z == self.size - 1):
                            params_float.append(self.get_temp_from_number(x,y,z))
            unknowns_float=fast_solver(*params_float)
            i=0
            j=0
            for x in range(self.size):
                for y in range(self.size):
                    for z in range(self.size):
                        if not (x == 0 or x == self.size - 1 or
                   y == 0 or y == self.size - 1 or
                   z == 0 or z == self.size - 1):
                            self.data_float[x,y,z]=unknowns_float[i]
                            i+=1
                        else:
                            self.data_float[x,y,z]=params_float[j]
                            j+=1
         else:
             b=[]
             for x in range(1, self.size-1):
                 for y in range(1, self.size-1):
                     for z in range(1, self.size-1):
                         summ=0
                         if x==1:
                             summ+=(self.data_float[x-1,y,z])
                         if y==1:
                             summ+=(self.data_float[x,y-1,z])
                         if z==1:
                             summ+=(self.data_float[x,y,z-1])
                         if x==self.size-2:
                             summ+=(self.data_float[x+1,y,z])
                         if y==self.size-2:
                             summ+=(self.data_float[x,y+1,z])
                         if z==self.size-2:
                             summ+=(self.data_float[x,y,z+1])
                         b.append(summ)
             sols=spsolve(self.A, b)
             i=0
             for x in range(1, self.size-1):
                 for y in range(1, self.size-1):
                     for z in range(1, self.size-1):
                         self.data_float[x,y,z]=sols[i]
                         i+=1























