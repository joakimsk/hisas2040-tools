import numpy as np
import matplotlib.pyplot as plt
from PIL import Image



bpc_file = "beampatterncomp.txt"

# Read the CSV file using loadtxt
data = np.loadtxt(bpc_file, delimiter='\t', skiprows=0)

print(data)


plt.plot(data[:,0], data[:,1], 'ro') 
plt.show()