import pandas as pd

filepath = 'dummy.csv'  






class baspy_DataFrame(pd.DataFrame):
    _metadata = ['metadata']
    
    @property
    def _constructor(self):
        return baspy_DataFrame

def write_csv_with_comments(df, fname, **kwargs):
  user_values = kwargs.copy()
  keys   = list(user_values.keys())
  values = list(user_values.values())
  with open(fname, 'w') as file:
      for key, value in zip(keys,values):
        comment = '# '+str(key)+'='+str(value)+'\n'
        file.write(comment)
      df.to_csv(file, index=False)


def read_csv_with_comments(fname):
  ### read file
  store_metadata = {}
  with open(fname) as fp:  
      line = fp.readline()
      while line.startswith('#'):
         # takes elements from comment and add to dictionary
         elements=line.strip().replace('#','').replace(' ','').split('=')
         store_metadata.update({elements[0]:elements[1]})
         ### read next line
         line = fp.readline()

  df = pd.read_csv(fname, comment='#')
  df = baspy_DataFrame(df)
  df.metadata = store_metadata
  return df




### write file
df = read_csv_with_comments(filepath)




# print( type(df.iloc[[0]]) )
# print( type(df.iloc[0])   )

print( df.iloc[[0]].metadata )

# # https://github.com/pandas-dev/pandas/issues/19850
# print( df.iloc[0].metadata   )  # <--- how can I make the Series retain the metadata from the DataFrame?
