import pandas as pd
df = pd.read_parquet(r"C:\Users\tyiho\DSE3101 Project\dse3101investmentproject\Datasets\13F_clean_files\01jun2024-31aug2024_clean_df.parquet")
print(df.head())
print(list(df.columns))
print(df.shape)

constant_cols = df.columns[df.nunique(dropna=False) == 1]

print("Columns with same value for all rows:")
print(list(constant_cols))