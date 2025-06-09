# This script only creates an abox for translated and original mercadona and carrefour data
# To add further supermarkets to the graph, add the link to the cleaned data file in line #27 
# 

from rdflib import Graph, Namespace, Literal, RDF, URIRef
from rdflib.namespace import XSD
import csv
import json
import os
import pandas as pd

BB = Namespace("http://budgetbites.org/ontology#")
g = Graph()
g.bind("bb", BB)

def safe_float(val, fallback=0.0):
    try:
        return float(val)
    except (ValueError, TypeError):
        return fallback  # or use 

# === 1. Supermarkets ===
g.add((BB.Mercadona, RDF.type, BB.Supermarket))
g.add((BB.Carrefour, RDF.type, BB.Supermarket))

# === 2. Load translated ingredients ===
with open("landing_zone/api_files/translated_mealdb_ingredients.json", encoding="utf-8") as f:
    translations = json.load(f)
    for en, es in translations.items():
        uri = URIRef(f"http://budgetbites.org/resource/ingredient/{en.replace(' ', '_')}")
        g.add((uri, RDF.type, BB.Ingredient))
        g.add((uri, BB.ingredientNameEN, Literal(en)))
        g.add((uri, BB.ingredientNameES, Literal(es)))

# === 3. Load product data from Mercadona ===
with open("landing_zone/downloaded_csv/mercadona_products.csv", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        pid = row["Product ID"].strip()
        product = URIRef(f"http://budgetbites.org/resource/product/{pid}")
        g.add((product, RDF.type, BB.Product))
        g.add((product, BB.name, Literal(row["Name"])))
        g.add((product, BB.price, Literal(safe_float(row["Price"]))))
        g.add((product, BB.referencePrice, Literal(safe_float(row["Reference Price"]))))
        g.add((product, BB.referenceUnit, Literal(row["Reference Format"])))
        g.add((product, BB.unit, Literal(row["Unit"])))
        g.add((product, BB.imageURL, Literal(row["Image URL"])))
        g.add((product, BB.productURL, Literal(row["Product URL"])))
        g.add((product, BB.insertDate, Literal("2024-01-01")))  # Static or inferred

        # Add category info
        parent_cat = Literal(row["Parent Category"])
        category = Literal(row["Category"])
        subcategory = Literal(row["Subcategory"])
        g.add((product, BB.hasCategory, category))
        g.add((product, BB.parentCategory, parent_cat))
        g.add((product, BB.subCategory, subcategory))

        # Link to supermarket
        g.add((product, BB.soldBy, BB.Mercadona))

# === 4. Load product data from Carrefour ===
with open("landing_zone/downloaded_csv/thegurus-opendata-carrefour-es-products.csv", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        pid = row["id"].strip()
        product = URIRef(f"http://budgetbites.org/resource/product/{pid}")
        g.add((product, RDF.type, BB.Product))
        g.add((product, BB.name, Literal(row["name"])))
        g.add((product, BB.price, Literal(safe_float(row["price"]))))
        g.add((product, BB.referenceUnit, Literal(row["reference_unit"])))
        g.add((product, BB.insertDate, Literal(row["insert_date"])))
        g.add((product, BB.soldBy, BB.Carrefour))
        g.add((product, BB.hasCategory, Literal(row["category"])))

# === 5. Load seasonality info (new structure) ===
with open("landing_zone/api_files/ingredient_seasonality.json", encoding="utf-8") as f:
    seasonality = json.load(f)

for ingredient, months in seasonality.items():
    ing_uri = URIRef(f"http://budgetbites.org/resource/ingredient/{ingredient.replace(' ', '_')}")
    for month in months:
        month_uri = URIRef(f"http://budgetbites.org/resource/month/{month}")
        g.add((month_uri, RDF.type, BB.Month))
        g.add((ing_uri, BB.isSeasonalIn, month_uri))
        g.add((month_uri, BB.name, Literal(month)))

# === 6. Load recipes from MealDB JSON ===
with open("landing_zone/api_files/data_recipe.json", encoding="utf-8") as f:
    data = json.load(f)

for meal in data.get("meals", []):
    recipe_id = meal["idMeal"]
    recipe_name = meal["strMeal"]
    recipe_uri = URIRef(f"http://budgetbites.org/resource/recipe/{recipe_id}")

    g.add((recipe_uri, RDF.type, BB.Recipe))
    g.add((recipe_uri, BB.name, Literal(recipe_name)))

    # Optional: Add image or instructions
    if meal.get("strMealThumb"):
        g.add((recipe_uri, BB.imageURL, Literal(meal["strMealThumb"])))
    if meal.get("strInstructions"):
        g.add((recipe_uri, BB.instruction, Literal(meal["strInstructions"])))

    # Link to ingredients
    for i in range(1, 21):
        raw_ingredient = meal.get(f"strIngredient{i}")
        if raw_ingredient and raw_ingredient.strip():
            ingredient = raw_ingredient.strip()
            ing_uri = URIRef(f"http://budgetbites.org/resource/ingredient/{ingredient.replace(' ', '_')}")
            g.add((recipe_uri, BB.usesIngredient, ing_uri))

# === 7. Link matched ingredients to Mercadona products ===
match_file = "landing_zone/downloaded_csv/matched_mealdb_to_mercadona.csv"
matched_df = pd.read_csv(match_file)

for _, row in matched_df.iterrows():
    eng_ing = row["mealdb_english"]
    product_id = row["id"]

    ingredient_uri = URIRef(f"http://budgetbites.org/resource/ingredient/{eng_ing.replace(' ', '_')}")
    product_uri = URIRef(f"http://budgetbites.org/resource/product/{product_id}")

    # Declare the link
    g.add((ingredient_uri, BB.matchesWithProduct, product_uri))

    # Add product metadata (if not already added)
    if row.get("matched_mercadona"):
        g.add((product_uri, BB.name, Literal(row["matched_mercadona"])))
    if not pd.isna(row.get("price")):
        g.add((product_uri, BB.price, Literal(float(row["price"]), datatype=XSD.decimal)))
    if not pd.isna(row.get("reference_price")):
        g.add((product_uri, BB.referencePrice, Literal(float(row["reference_price"]), datatype=XSD.decimal)))
    if row.get("unit"):
        g.add((product_uri, BB.unit, Literal(row["unit"])))

# === 8. Save the ABox ===
output_path = "processing/abox_recipes.ttl"
os.makedirs("processing", exist_ok=True)
g.serialize(destination=output_path, format="turtle")
print(f"✅ ABox with recipes successfully written to {output_path}")