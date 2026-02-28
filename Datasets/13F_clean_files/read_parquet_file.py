import pandas as pd
df = pd.read_parquet(r"C:\Users\User\Documents\NUS\Y3S2\DSE3101\dse3101investmentproject\Datasets\13F_clean_individual\01dec2024-28feb2025_clean_df.parquet")
print(df.head())
print(list(df.columns))
print(df.shape)