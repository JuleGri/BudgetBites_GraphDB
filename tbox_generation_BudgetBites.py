from rdflib import Graph, Namespace, RDF, RDFS, OWL, XSD, BNode
from rdflib.collection import Collection

# Namespaces
BB = Namespace("http://budgetbites.org/ontology#")
OWL_NS = OWL
RDF_NS = RDF
RDFS_NS = RDFS
XSD_NS = XSD

g = Graph()
g.bind("", BB)
g.bind("owl", OWL_NS)
g.bind("rdf", RDF_NS)
g.bind("rdfs", RDFS_NS)
g.bind("xsd", XSD_NS)

classes = [
    "Product", "Ingredient", "Supermarket",
    "Category", "Month", "Recipe"
]
for cls in classes:
    g.add((BB[cls], RDF_NS.type, OWL_NS.Class))

object_properties = {
    "soldBy": ("Product", "Supermarket"),
    "hasCategory": ("Product", "Category"),
    "isSeasonalIn": ("Ingredient", "Month"),
    "usesIngredient": ("Recipe", "Ingredient"),
    "matchesWithProduct": ("Ingredient", "Product"),
}
for prop, (domain, range_) in object_properties.items():
    g.add((BB[prop], RDF_NS.type, OWL_NS.ObjectProperty))
    g.add((BB[prop], RDFS_NS.domain, BB[domain]))
    g.add((BB[prop], RDFS_NS.range, BB[range_]))


union_classes = ["Product", "Supermarket", "Category", "Month", "Recipe"]
union_node = BNode()             # Anonyme Klasse für owl:unionOf
collection_node = BNode()        # Startpunkt der RDF-Liste
Collection(g, collection_node, [BB[cls] for cls in union_classes])
g.add((union_node, OWL_NS.unionOf, collection_node))

datatype_properties = {
    "name": (union_node, XSD_NS.string),
    "ingredientNameEN": (BB.Ingredient, XSD_NS.string),
    "ingredientNameES": (BB.Ingredient, XSD_NS.string),
    "price": (BB.Product, XSD_NS.decimal),
    "referencePrice": (BB.Product, XSD_NS.decimal),
    "referenceUnit": (BB.Product, XSD_NS.string),
    "unit": (BB.Product, XSD_NS.string),
    "insertDate": (BB.Product, XSD_NS.string),
    "imageURL": (BB.Product, XSD_NS.anyURI),
    "productURL": (BB.Product, XSD_NS.anyURI),
    "parentCategory": (BB.Product, XSD_NS.string),
    "subCategory": (BB.Product, XSD_NS.string),
}
for prop, (domain, range_) in datatype_properties.items():
    g.add((BB[prop], RDF_NS.type, OWL_NS.DatatypeProperty))
    g.add((BB[prop], RDFS_NS.domain, domain))
    g.add((BB[prop], RDFS_NS.range, range_))

g.serialize(destination="graphBoxes/tbox_BudgetBites.ttl", format="turtle")
print("TBox successfully created and saved as 'generated_tbox.ttl'")