from data_loader import load_data

stores, features, sales = load_data()

print("Connexion réussie ✅")
print(f"stores: {stores.shape}")
print(f"features: {features.shape}")
print(f"sales: {sales.shape}")
