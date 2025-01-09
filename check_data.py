import pandas as pd
df = pd.read_csv('sample_data.csv')

df = df[df['username'] == 'Ben']

print(df[:50])