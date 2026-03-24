import pandas as pd
import tools.missing_values as mv

df1 = pd.DataFrame({'a': [1, 2, None, 4], 'b': [None, 1, 1, 4]})
df2 = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})

print('\nTest data 1:')
print(df1)
print('\nTest data 2:')
print(df2)

print('\nIs Missing Values:')
print('1.')
print(mv.is_missing_vals(df1))
print('2.')
print(mv.is_missing_vals(df2))

print('\nMissing Value Rows')
print('1.')
print(mv.missing_val_rows(df1))

print('\nMissing Value Rows Indices')
print('1.')
print(mv.missing_val_rows_indices(df1))

print('\nRemoving Missing Value Rows')
print('1.')
print(mv.remove_missing_rows(df1))

print('\nFilling Missing Values with Mean')
print('1.')
print(mv.fill_mean(df1))

print('\nFilling Missing Values with Median')
print('1.')
print(mv.fill_median(df1))

print('\nFilling Missing Values with Back Fill')
print('1.')
print(mv.backfill(df1))

print('\nFilling Missing Values with Forward Fill')
print('1.')
print(mv.forwardfill(df1))

print('\nFilling Missing Values with Both Forward Fill and Back Fill')
print('1.')
print(mv.bothfill(df1))
