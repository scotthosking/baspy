import pandas as pd

filepath = 'dummy.csv'  


class baspy_DataFrame(pd.DataFrame):
    _metadata = ['metadata']
    
    @property
    def _constructor(self):
        return baspy_DataFrame




store_metadata = {}
with open(filepath) as fp:  
   line = fp.readline()
   while line.startswith('#'):
       # takes elements from comment and add to dictionary
       elements=line.strip().replace('#','').replace(' ','').split('=')
       store_metadata.update({elements[0]:elements[1]})
       ### read next line
       line = fp.readline()


df = pd.read_csv(filepath, comment='#')
df = baspy_DataFrame(df)

df.metadata = store_metadata

print( type(df.iloc[[0]]) )
print( type(df.iloc[0])   )

print( df.iloc[[0]].metadata )

# # https://github.com/pandas-dev/pandas/issues/19850
# print( df.iloc[0].metadata   )  # <--- how can I make the Series retain the metadata from the DataFrame?
