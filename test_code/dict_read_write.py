#!/usr/bin/env python

import ast
  
# reading the data from the file
with open('dictionary.txt') as f:
    data = f.read()
  
print("Data type before reconstruction : ", type(data))
      
# reconstructing the data as a dictionary
d = ast.literal_eval(data)
  
print("Data type after reconstruction : ", type(d))
print(d)

# dictionary.txt
'''
{
"Name": "John",
"Age": 21,
"ID": 28,
"map":{
   1: "one",
   2: "two"
   }
}
'''
